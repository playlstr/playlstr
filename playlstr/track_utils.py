from django.db.models import Q, ObjectDoesNotExist
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from .models import *


def add_track_by_metadata(data: dict) -> Track:
    if 'title' not in data:
        return None
    if 'isrc' in data:
        try:
            track = Track.objects.get(isrc=data['isrc'])
            return track.track_id
        except ObjectDoesNotExist:
            pass
    track = Track.objects.filter(md5=data['hash']).first()
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
    if 'title' not in info:
        print('Tried to add track with no title')
        return None
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
    if 'is_single' in info:
        track.is_single = bool(info['is_single'])
    if 'album_artist' in info:
        track.album_artist = info['album_artist']
    if 'duration' in info:
        track.duration = int(info['duration'])
    track.save()
    return track
