from re import match
from requests import get
from django.db.models import Q
import json
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
        for json in tracks_json['items']:
            index += 1
            track = track_from_spotify_json(json['track'])
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


def update_playlist(data):
    try:
        playlist = Playlist.objects.get(playlist_id=int(data['playlist']))
    except (KeyError, ValueError):
        return
    try:
        added = [int(i) for i in json.loads(data['added'])]
    except (KeyError, ValueError):
        added = []
    try:
        removed = [int(i) for i in json.loads(data['removed'])]
    except (KeyError, ValueError):
        removed = []
    try:
        new_name = data['playlist_name']
    except KeyError:
        pass
    else:
        if new_name != playlist.name:
            playlist.name = new_name
            playlist.save()
    # TODO update the indices of elements and calculate the index of new elements so that indices are sequential
    for r in removed:
        PlaylistTrack.objects.filter(track=Track.objects.get(track_id=r)).delete()
    last_index = PlaylistTrack.objects.filter(playlist=playlist).last()
    last_index = 0 if last_index is None else last_index.index
    for a in added:
        last_index += 1
        PlaylistTrack.objects.create(playlist=playlist, track=Track.objects.get(track_id=a), index=last_index)
