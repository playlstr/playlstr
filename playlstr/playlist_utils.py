from .spotify_utils import *
from .track_utils import *


def update_playlist(data: dict) -> str:
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
        response = get(base_url + track, headers=headers)
        track_json = response.json()
        track = track_from_spotify_json(track_json)
        PlaylistTrack.objects.create(playlist=playlist, track=track, index=last_index)
    if len(spotify_ids > 0):
        changed = True
    if changed:
        playlist.edit_date = timezone.now()
        playlist.save()
    return 'success'


def client_import_parse(name: str, tracks: list) -> str:
    playlist = Playlist.objects.create(name=name)
    index = 0
    for t in tracks:
        track = add_track_by_metadata(t)
        # TODO handle duplicate tracks
        PlaylistTrack.objects.create(track=track, playlist=playlist, index=index)
        index += 1
    return playlist.playlist_id
