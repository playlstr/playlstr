from re import match
from requests import get
from django.db.models import Q

from .models import *


def import_spotify(info):
    url = info['playlist_url']
    # Validate URL
    if not (isinstance(url, str) and match(r'^http(s?)://open\.spotify\.com/playlist/.{22}/?', url)):
        return 'Invalid URL'
    playlist_id = url[-23:0] if url[-1] == '/' else url[-22:]
    # Get playlist tracks
    query_url = 'https://api.spotify.com/v1/playlists/' + playlist_id
    query_headers = {'Authorization': 'Bearer {}'.format(info['access_token'])}
    tracks_json = get(query_url + '/tracks', headers=query_headers).json()
    # TODO handle expired/invalid access token
    # Get list of tracks
    tracks = []
    while 'next' in tracks_json and tracks_json['next'] is not None:
        for json in tracks_json['items']:
            json = json['track']
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
            tracks.append(track)
        tracks_json = get(tracks_json['next'], headers=query_headers).json()
    playlist_json = get(query_url, headers=query_headers).json()
    playlist = Playlist.objects.get_or_create(spotify_id=playlist_id)[0]
    playlist.name = playlist_json['name']
    playlist.tracks.set(tracks)
    playlist.last_sync_spotify = datetime.now()
    playlist.save()
    return playlist.playlist_id
