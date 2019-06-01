from re import match
import json
from django.db.models import Q
from requests import get
from .models import *


def import_spotify(info):
    """
    Import Spotify playlist and return playlist ID or cause of error if unsuccessful
    :param info: dict where playlist_url is the url of the playlist and access_token is the Spotify access token
    :return: playlist ID or cause of error if unsuccessful
    """
    url = info['playlist_url']
    # Validate URL
    if not (isinstance(url, str) and match(r'^http(s?)://open\.spotify\.com/playlist/.{22}/?', url)):
        return 'Invalid URL'
    playlist_id = url[-23:0] if url[-1] == '/' else url[-22:]
    query_url = 'https://api.spotify.com/v1/playlists/' + playlist_id
    query_headers = {'Authorization': 'Bearer {}'.format(info['access_token'])}
    # Get/create playlist
    playlist_json = get(query_url, headers=query_headers).json()
    playlist = Playlist.objects.get_or_create(spotify_id=playlist_id)[0]
    playlist.name = playlist_json['name']
    playlist.last_sync_spotify = timezone.now()
    playlist.save()
    # Get playlist tracks
    tracks_response = get(query_url + '/tracks', headers=query_headers)
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
            PlaylistTrack.objects.create(playlist=playlist, track=track, index=index)
        tracks_json = get(tracks_json['next'], headers=query_headers).json()
    return playlist.playlist_id


def track_from_spotify_json(json):
    """
    Return a track matching Spotify track JSON
    :param json: the Spotify track JSON
    :return: Track matching Spotify JSON
    """
    # Check if track already exists
    query = Q(spotify_id=json['id'])
    try:
        query.add(Q(isrc=json['external_ids']['isrc']), Q.OR)
    except:
        pass
    track = Track.objects.filter(query).first()
    if track is None:
        title = json['name']
        try:
            isrc = json['external_ids']['isrc']
        except KeyError:
            isrc = None
        # Create new track
        track = Track.objects.create(title=title)
    else:
        # Ensure existing track has correct spotify id
        track.spotify_id = json['id']
    # Get track attributes
    try:
        track.artist = json['artists'][0]['name']
    except KeyError:
        pass
    try:
        track.album = json['album']['name']
    except KeyError:
        pass
    try:
        track.duration_ms = json['duration_ms']
    except KeyError:
        pass
    track.save()
    return track


def valid_spotify_token(token):
    test_url = 'https://api.spotify.com/v1/tracks/11dFghVXANMlKmJXsNCbNl'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = get(test_url, headers=headers)
    return response.status_code == 200
