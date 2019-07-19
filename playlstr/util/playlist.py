from .spotify import *
from .track import *


def playlist_add_track(playlist: Playlist, track: Track) -> PlaylistTrack:
    """
    Add a track to a playlist and return the new PlaylistTrack
    :param playlist: playlist to add the track to
    :param track: track to add to playlist
    :return: newly created PlaylistTrack
    """
    try:
        return PlaylistTrack.objects.get(playlist=playlist, track=track)
    except ObjectDoesNotExist:
        last = PlaylistTrack.objects.filter(playlist=playlist).last()
        index = 0 if last is None else last.index + 1
        return PlaylistTrack.objects.create(playlist=playlist, track=track, index=index)


def update_playlist(data: dict) -> Optional[str]:
    """
    Update playlist with data from playlist edit view
    :param data: dict of data to add to playlist
    :return: error message if an error occurred else None
    """
    changed = False
    # Validate spotify token before changing anything in the DB
    spotify_ids = []
    spotify_token = ''
    if 'spotify_new' in data:
        spotify_ids = json.loads(data['spotify_new'])
        if len(spotify_ids) > 0:
            if 'spotify_token' not in data:
                return 'invalid token'
            spotify_token = data['spotify_token']
            if not valid_spotify_token(spotify_token):
                return 'invalid token'
    # Get playlist
    try:
        playlist = Playlist.objects.get(playlist_id=int(data['playlist']))
    except (KeyError, ValueError):
        return 'invalid playlist'
    # Update playlist name
    try:
        new_name = data['playlist_name']
    except KeyError:
        pass
    else:
        if new_name != playlist.name:
            playlist.name = new_name
            changed = True
    # Remove tracks
    try:
        removed = [int(i) for i in json.loads(data['removed'])]
        if len(removed) > 0:
            changed = True
        for r in removed:
            PlaylistTrack.objects.filter(track=r).delete()
    except (KeyError, ValueError):
        pass
    # TODO update the indices of elements and calculate the index of new elements so that indices are sequential
    last_index = PlaylistTrack.objects.filter(playlist=playlist).last()
    last_index = 0 if last_index is None else last_index.index
    # Add tracks
    try:
        added = [int(i) for i in json.loads(data['added'])]
        for a in added:
            last_index += 1
            PlaylistTrack.objects.create(playlist=playlist, track=Track.objects.get(track_id=a), index=last_index)
        if len(added) > 0:
            changed = True
    except (KeyError, ValueError):
        pass
    # Add spotify tracks
    base_url = 'https://api.spotify.com/v1/tracks/'
    headers = {'Authorization': 'Bearer {}'.format(spotify_token)}
    for track in spotify_ids:
        last_index += 1
        response = requests.get(base_url + track, headers=headers)
        track_json = response.json()
        track = track_from_spotify_json(track_json)
        PlaylistTrack.objects.create(playlist=playlist, track=track, index=last_index)
    if len(spotify_ids) > 0:
        changed = True
    if changed:
        playlist.edit_date = timezone.now()
        playlist.save()
    return None


def client_import_parse(name: str, tracks: list, user: PlaylstrUser) -> int:
    """
    Create a playlist from list of track metadata and return its id
    :param name: playlist name
    :param tracks: list of dicts of track metadata
    :param user: the user who should own the playlist
    :return: playlist_id of created playlist
    """
    playlist = Playlist.objects.create(name=name, owner=user)
    index = 0
    for t in tracks:
        track = add_track_by_metadata(t)
        if track.deezer_id is None:
            match_track_deezer(track)
        if track.gplay_id is None:
            match_track_gplay(track)
        # TODO handle duplicate tracks
        PlaylistTrack.objects.create(track=track, playlist=playlist, index=index)
        index += 1
    return playlist.playlist_id


def import_playlist_from_string(filename: str, playlist: str, user: PlaylstrUser) -> Optional[int]:
    """
    Import a playlist from a string formatted as a playlist file
    :param filename: name of playlist file being imported
    :param playlist: string containing a playlist file in its entirety
    :param user: the user who should own the newly created playlist
    :return: playlist_id of newly created playlist or None if the playlist to be imported was empty or malformed
    """
    name, filetype = filename.rsplit('.')
    if filetype == 'm3u' or filetype == 'm3u8':
        return create_playlist_from_m3u(name, playlist, user)


def create_playlist_from_m3u(name: str, playlist: str, user: PlaylstrUser, ext_overrides_guess: bool = True) -> \
        Optional[int]:
    """
    Create a playlist from an m3u file
    :param name: name of the m3u file
    :param playlist: m3u file as a string
    :param user: user who will own the created playlist
    :param ext_overrides_guess: if true then if the file is an m3uext file the metadata given in the playlist file takes
     precedence over the metadata guessed from the file name and path
    :return: the new playlist's id if the file was valid else None
    """
    lines = playlist.splitlines()
    if lines[0] == '#EXTM3U':
        ext = True
        on_inf = True  # Whether we are on a #EXTINF line
        lines = lines[1:-1]
    else:
        on_inf = False  # Whether we are on a #EXTINF line
        ext = False
    inf_duration = None
    inf_artist = None
    inf_track = None
    playlist = None
    for line in lines:
        if line == '':
            continue
        if on_inf:
            line = line[7:]
            split_colon = line.split(':', 1)
            inf_duration = split_colon[0] if len(split_colon) > 0 else None
            split_dash = line.split('-', 2)
            inf_artist = split_dash[0].strip().split(',', 1)[1] if len(split_dash) > 0 else None
            inf_track = split_dash[1].strip() if len(split_dash) > 1 else None
            on_inf = False
            continue
        else:
            info = guess_info_from_path(line)
            if ext:
                if inf_track:
                    if 'title' not in info or info['title'] == '' or (
                            ext_overrides_guess and inf_artist is not None and inf_artist != ''):
                        info['title'] = inf_track
                if inf_artist:
                    if 'artist' not in info or info['artist'] == '' or (
                            ext_overrides_guess and inf_artist is not None and inf_artist != ''):
                        info['artist'] = inf_artist
                if inf_duration:
                    info['duration'] = inf_duration
                on_inf = True
            track = add_track_by_metadata(info)
            if track is None:
                continue
            if playlist is None:
                playlist = Playlist.objects.create(name=name)
                playlist.owner = user
                playlist.save()
            playlist_add_track(playlist, track)
    return None if playlist is None else playlist.playlist_id
