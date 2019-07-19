import re
from typing import Optional

from django.db.models import Q, ObjectDoesNotExist
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from playlstr.models import *
from playlstr.util.deezer import deezer_single_track_search
from playlstr.util.gplay import gplay_search


def add_track_by_metadata(data: dict) -> Track:
    """
    Create a track from given metadata
    :param data: track metadata
    :return: newly created Track
    """
    assert 'title' in data
    if 'isrc' in data:
        try:
            track = Track.objects.get(isrc=data['isrc'])
            return track.track_id
        except ObjectDoesNotExist:
            pass
    track = Track.objects.filter(md5=data['hash']).first() if 'hash' in data else None
    if track is None:
        query = Q(title=data['title'])
        if 'artist' in data and len(data['artist']) > 0:
            query.add(Q(artist=data['artist']), Q.AND)
        if 'album' in data and len(data['album']) > 0:
            query.add(Q(album=data['album']), Q.AND)
        if 'duration' in data:
            query.add((Q(duration=data['duration']) | Q(duration=None)), Q.AND)
        if 'date' in data:
            query.add(Q(year=data['date']), Q.AND)
        if 'albumartist' in data:
            query.add(Q(album_artist=data['albumartist']), Q.AND)
        elif 'album artist' in data:
            query.add(Q(album_artist=data['album artist']), Q.AND)
        if 'tracknumber' in data:
            query.add(Q(track_number=data['tracknumber']), Q.AND)
        track = Track.objects.filter(query).first()
        if track is None:
            track = create_custom_track(data)
    update_track_with_file_metadata(track, data)
    return track


def update_track_with_file_metadata(track: Track, data: dict) -> None:
    """
    Update Track to match metadata
    :param track: track to update
    :param data: metadata to update to
    """
    if 'title' in data:
        track.title = data['title']
    if 'artist' in data:
        track.artist = data['artist']
    if 'album' in data:
        track.album = data['album']
    if 'date' in data:
        track.year = data['date']
    if 'albumartist' in data:
        track.album_artist = data['albumartist']
    if 'duration' in data:
        track.duration = int(data['duration'])
    if 'tracknumber' in data:
        track.track_number = int(data['tracknumber'])
    if 'genre' in data:
        if track.genres is None:
            track.genres = []
        if isinstance(data['genre'], str):
            track.genres.append(data['genre'])
        else:
            # TODO handle multiple genres
            pass
    track.save()


def create_custom_track(info: dict) -> Track:
    """
    Create and return a track matching metadata
    :param info: track metadata
    :return: newly created Track
    """
    track = Track.objects.create(title=info['title'])
    if 'artist' in info:
        track.artist = info['artist']
    if 'album' in info:
        track.album = info['album']
    if 'release_date' in info:
        release = parse_datetime(info['release_date'])
        if not is_aware(release):
            release = make_aware(release)
        track.release_date = release
    if 'album_artist' in info:
        track.album_artist = info['album_artist']
    if 'duration' in info:
        track.duration = int(info['duration'])
    track.save()
    return track


def guess_info_from_path(file_path: str) -> dict:
    """
    Return a guess of what the track metadata might be based on the path to the file
    :param file_path: path of the file to guess the info from
    :return: guessed metadata of file
    """
    info = {}
    # Get path as a valid unix path
    file_path = file_path.lstrip().rstrip()
    if re.match(r'^[A-Z]:\\.*$', file_path):
        file_path.replace('\\', '/')
    # Split up the path
    path = file_path.split('/')
    path.reverse()
    in_directory = True  # Whether the file is in a directory
    if len(path) == 1:
        path = path[0].split(' - ')
        path.reverse()
        in_directory = False
    file_with_folder = '{}/{}'.format(path[1], path[0]) if len(path) >= 2 else path[0]
    file_no_extension, extension = path[0].rsplit('.', 1)
    info['source'] = extension.lower()
    ''' Try to get year (at least 1700) from filename and parent directory'''
    # First look for year in brackets
    year = re.search(r'[\[({]((1[7-9])|(20))\d{2}[\])}]', file_with_folder)
    # If no year in brackets look for just any valid year
    if year is None:
        year = re.search(r'((1[7-9])|(20))\d{2}', file_with_folder)
        if year is not None:
            info['year'] = int(year.group(0))
    else:
        info['year'] = int(year.group(0)[1:-1])

    ''' Try to get track number (up to 99) from filename '''
    # Track number at beginning
    # TODO handle track number in different places
    track_no = re.search(r'^[\d|A|B]\d?.*', file_no_extension)
    # Get just track number for case where track number is at beginning
    if track_no:
        track_no = track_no.group(0)
        if len(track_no) > 1 and track_no[1].isdecimal():
            track_no = track_no[0:2]
        else:
            track_no = track_no[0]
        info['track_number'] = track_no
    ''' Try to get artist/album name '''
    # Check for structure artist - album/tracks
    if in_directory:
        folder = path[1]
        # Delete parts of the directory name that aren't album/artist so hyphens inside don't mess up parsing
        folder = re.sub(r'{.*}', '', folder)
        folder = re.sub(r'\[.*\]', '', folder)
        folder = re.sub(r'\(.*\)', '', folder)
        if '-' in folder:
            split = folder.lstrip().rstrip().split('-')
            if len(split) > 2:
                for s in split:
                    if re.match(r'\d{4}', s.lstrip().rstrip()):
                        split.remove(s)
                split = split[0:2]
            artist = split[0].rstrip()
            album = split[1].lstrip()
        # Structure artist/album/tracks
        else:
            artist = path[2]
            album = path[1]
    else:
        artist = path[1]
        album = ''
    # TODO make this work with albums/artists with parentheses in their name
    if artist != '':
        artist = re.sub(r'(^FLAC )|( FLAC )|( FLAC$)', '', artist)
        artist = re.sub(r'\(.*?\)', '', artist)
        info['artist'] = artist.replace('_', ' ').rstrip().lstrip()
    # Try to isolate album name
    if album != '':
        album = re.sub(r'(^FLAC )|( FLAC )|( FLAC$)', '', album)
        album = re.sub(r'\(.*?\)', '', album)
        info['album'] = album.replace('_', ' ').rstrip().lstrip()

    ''' Try to get catalog number of album '''
    if in_directory:
        non_version_info = re.compile(
            r'^((FLAC)|(WEB ?-? ?(FLAC)?)|(SACD)|(CD)|([Vv]inyl)|(MP3)|(24 ?[Bb]it)|(\d{4})).*$')
        curly = re.finditer(r'{([a-zA-Z]|\d| )* ?-?[ ,\d-]*}', path[1])
        for c in curly:
            if not re.match(non_version_info, c.group(0).replace('{', '').replace('}', '')):
                info['album_version'] = c.group(0)[1:-1]
                break
        if 'album_version' not in info:
            square = re.finditer(r'\[([a-zA-Z]|\d| )* ?-?[ ,\d-]*\]', path[1])
            for s in square:
                if not re.match(non_version_info, s.group(0).replace('[', '').replace(']', '')):
                    info['album_version'] = s.group(0)[1:-1]
                    break
            if 'album_version' not in info:
                parenth = re.finditer(r'\(([a-zA-Z]|\d| )* ?-?[a-zA-Z ,\d-]*\)', path[1])
                for p in parenth:
                    if not re.match(non_version_info, p.group(0).replace('(', '').replace(')', '')):
                        info['album_version'] = p.group(0)[1:-1]
                        break

    ''' Try to get track name '''
    if re.match(r'[ABC\d]\d ?-? ?.*', file_no_extension):
        info['title'] = re.sub(r'(\d{1,2} ?-? ?)', '', file_no_extension, 1)
    else:
        info['title'] = file_no_extension
    return info


def match_track_deezer(track: Track, match_title=True, match_album=True, match_artist=True, *match_custom) -> bool:
    """
    Find Deezer track matching the track info and update the Track with Deezer info if all attributes in match_req are the same
    :param track: Track to find matching info for
    :param match_title: whether to require matching track title to update track
    :param match_album: whether to require matching track album to update track
    :param match_artist: whether to require matching track artist to update track
    :param match_custom: Track attributes which must be the same as the Deezer attribute
    :return: whether the track was updated
    :raises AttributeError: if a key in match_custom is not in track or a Deezer track
    """
    # Make sure all the custom attributes are valid
    for req in match_custom:
        if not hasattr(track, req):
            raise AttributeError
    deezer_results = deezer_single_track_search(
        '{} {}'.format(track.title, track.artist) if track.artist != UNKNOWN_ARTIST else track.title)
    for dtrack in deezer_results:
        if dtrack['type'] != 'track':
            continue
        if match_title and dtrack['title'] != track.title and dtrack['title_short'] != track.title:
            continue
        if match_artist and track.artist != UNKNOWN_ARTIST and dtrack['artist']['name'] != track.artist:
            continue
        if match_album and track.album != UNKNOWN_ALBUM and dtrack['album']['title'] != track.album:
            continue
        reqs_matched = False if match_custom else True
        for req in match_custom:
            if req not in dtrack:
                raise AttributeError
            if dtrack[req] != getattr(track, req):
                reqs_matched = False
                break
        if not reqs_matched:
            continue
        track.deezer_id = dtrack['id']
        track.save()
        return True
    return False


def match_track_gplay(track: Track, match_title=True, match_artist=True) -> bool:
    """
    Find Google Play track matching the track info and update the Track with Google Play IDs
    :param track: Track to find matching info for
    :param match_title: whether to require matching track title to update track
    :param match_artist: whether to require matching track artist to update track
    :return: whether the track was updated
    """
    gplay_tracks = gplay_search('{} {}'.format(track.title, track.artist), 'track')
    for gtrack in gplay_tracks:
        if match_title and gtrack['title'] != track.title:
            continue
        if match_artist and gtrack['artist'] != track.artist:
            continue
        track.gplay_id = gtrack['id']
        track.gplay_album_id = gtrack['album_id']
        track.save()
        return True
    return False


def get_similar_track(track_info: dict) -> Track:
    # TODO
    raise ValueError('Unimplemented')
