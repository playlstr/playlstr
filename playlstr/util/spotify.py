import re
from typing import Optional

from django.db.models import Q
from django.db.utils import IntegrityError

from playlstr.models import *


def import_spotify(info: dict) -> str:
    """
    Import Spotify playlist and return playlist ID or cause of error if unsuccessful
    :param info: dict where playlist_url is the url of the playlist and access_token is the Spotify access token
    :return: playlist ID or cause of error if unsuccessful
    """
    url = info['playlist_url']
    # Validate URL
    if not (isinstance(url, str) and re.match(r'^http(s?)://open\.spotify\.com/playlist/[a-zA-Z\d]*/?', url)):
        return 'invalid'
    playlist_id = url[-23:0] if url[-1] == '/' else url[-22:]
    query_url = 'https://api.spotify.com/v1/playlists/' + playlist_id
    query_headers = {'Authorization': 'Bearer {}'.format(info['access_token'])}
    # Get/create playlist
    playlist_json = requests.get(query_url, headers=query_headers).json()
    playlist = Playlist(name=playlist_json['name'], last_sync_spotify=timezone.now(), spotify_id=playlist_id,
                        owner=info['user'])
    playlist.save()
    # Get playlist tracks
    tracks_response = requests.get(query_url + '/tracks', headers=query_headers)
    if tracks_response.status_code != 200:
        return tracks_response.reason
    tracks_json = tracks_response.json()
    try:
        return "Error: " + tracks_json['error_description']
    except KeyError:
        pass
    # Get list of tracks
    index = -1
    while 'next' in tracks_json and tracks_json['next'] is not None:
        for j in tracks_json['items']:
            index += 1
            track = track_from_spotify_json(j['track'])
            try:
                PlaylistTrack.objects.create(playlist=playlist, track=track, index=index)
            except IntegrityError:
                continue
        tracks_json = requests.get(tracks_json['next'], headers=query_headers).json()
    return str(playlist.playlist_id)


def track_from_spotify_json(track_json: dict) -> Track:
    """
    Return a track matching Spotify track JSON
    :param track_json: the Spotify track JSON
    :return: Track matching Spotify JSON
    """
    # Check if track already exists
    query = Q(spotify_id=track_json['id'])
    try:
        query.add(Q(isrc=track_json['external_ids']['isrc']), Q.OR)
    except:
        pass
    track = Track.objects.filter(query).first()
    if track is None:
        title = track_json['name']
        try:
            isrc = track_json['external_ids']['isrc']
        except KeyError:
            isrc = None
        # Create new track
        track = Track.objects.create(title=title)
    track.spotify_id = track_json['id']
    # Get track attributes
    try:
        track.artist = track_json['artists'][0]['name']
    except KeyError:
        pass
    try:
        track.album = track_json['album']['name']
    except KeyError:
        pass
    try:
        track.duration = round(track_json['duration_ms'] * 1000)
    except KeyError:
        pass
    track.save()
    return track


def valid_spotify_token(token: str) -> bool:
    test_url = 'https://api.spotify.com/v1/tracks/11dFghVXANMlKmJXsNCbNl'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(test_url, headers=headers)
    return response.status_code == 200


def get_user_spotify_token(user: PlaylstrUser) -> dict:
    if not user.spotify_linked():
        return {'error': 'unauthorized'}
    if user.spotify_token_expiry is None or user.spotify_token_expiry <= timezone.now():
        updated_token = user.update_spotify_tokens()
        if updated_token != 'success':
            return {'error': updated_token}
    return {'access_token': user.spotify_access_token,
            'expires_in': floor((user.spotify_token_expiry - timezone.now()).total_seconds())}


def spotify_parse_code(info: dict) -> str:
    data = info['post']
    user = info['user']
    headers = {'Authorization': 'Basic {}'.format(
        b64encode((SPOTIFY_CLIENT_ID + ':' + SPOTIFY_CLIENT_SECRET).encode()).decode())}
    body = {'grant_type': 'authorization_code', 'code': data['code'], 'redirect_uri': data['redirect_uri']}
    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=body)
    if response.status_code != 200:
        return response.reason
    try:
        info = response.json()
    except json.JSONDecodeError:
        return 'invalid json'
    if 'access_token' not in info or 'refresh_token' not in info:
        return ''
    if 'expires_in' not in info:
        info['expires_in'] = 3600
    user.spotify_refresh_token = info['refresh_token']
    user.spotify_access_token = info['access_token']
    try:
        user.spotify_token_expiry = timezone.now() + timezone.timedelta(seconds=int(info['expires_in']))
    except ValueError:
        return ''
    user.update_spotify_info()
    user.save()


def spotify_create_playlist(playlist_id: int, access_token: str, user_spotify_id: str, public: bool = True,
                            description: str = None) -> str:
    playlist = Playlist.objects.get(playlist_id=playlist_id)
    headers = {'Authorization': 'Bearer {}'.format(access_token),
               'Content-Type': 'application/json'}
    body = {'name': playlist.name, 'public': public}
    if description is not None:
        body['description'] = description
    response = requests.post('https://api.spotify.com/v1/users/{}/playlists'.format(user_spotify_id), headers=headers,
                             json=body)
    if response.status_code != 200 and response.status_code != 201:
        return 'Error {}'.format(response.reason)
    return response.json()['id']


def add_tracks_to_spotify_playlist(tracks: list, playlist_spotify_id: str, access_token: str):
    headers = {'Authorization': 'Bearer {}'.format(access_token),
               'Content-Type': 'application/json'}
    print(playlist_spotify_id)
    # Add tracks 100 at a time per Spotify API docs
    for i in range(0, len(tracks), 100):
        last = min(i + 100, len(tracks))
        uris = ['spotify:track:{}'.format(t.spotify_id) for t in tracks[i: last] if t.spotify_id is not None]
        response = requests.post('https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_spotify_id),
                                 headers=headers, json={'uris': uris})
        if response.status_code != 200 and response.status_code != 201:
            print('Error: {} (processing tracks {} to {})'.format(response.text, i, last))
            return False
        if last == len(tracks):
            break
    return True


def spotify_playlist_as_json_tracks(playlist_id: int, access_token: str) -> list:
    query_url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(playlist_id)
    query_headers = {'Authorization': 'Bearer {}'.format(access_token)}
    # Get playlist tracks
    tracks_response = requests.get(query_url, headers=query_headers)
    if tracks_response.status_code != 200:
        return tracks_response.reason
    tracks_json = tracks_response.json()
    if 'error_description' in tracks_json:
        return []
    # Get list of tracks
    tracks = []
    while 'next' in tracks_json and tracks_json['next'] is not None:
        for t in tracks_json['items']:
            tracks.append(t['track'])
        tracks_json = requests.get(tracks_json['next'], headers=query_headers).json()
    return tracks


def spotify_id_from_token(access_token: str) -> Optional[str]:
    if access_token is None:
        return None
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    response = requests.post('https://api.spotify.com/v1/me', headers=headers)
    if response.status_code != 200:
        return None
    user = response.json()
    if 'id' not in user:
        return None
    return user['id']
