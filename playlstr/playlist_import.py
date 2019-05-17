from re import match
from requests import get
from django.db.models import Q

from .models import *


def import_spotify(info):
    url = info['playlist_url']
    # Validate URL
    if not (isinstance(url, str) and match(r'^http(s?)://open\.spotify\.com/playlist/.{22}/?', url)):
        return 'Invalid URL'
    # Get playlist tracks
    query_url = 'https://api.spotify.com/v1/playlists/' + (
        url[-23:0] if url[-1] == '/' else url[-22:]) + '/tracks'
    query_headers = {'Authorization': 'Bearer {}'.format(info['access_token'])}
    # TODO parse more than 100 tracks
    tracks_json = get(query_url, headers=query_headers).json()
    #print(tracks_json)
    # Get list of tracks
    for json in tracks_json['items']:
        json = json['track']
        query = Q(spotify_id=json['id'])
        try:
            query.add(Q(isrc=json['external_ids']['isrc']), Q.OR)
        except:
            pass
        track = Track.objects.filter(query).first()
        if track is None:
            # Get track attributes
            title = json['name']
            try:
                artist = json['artists'][0]['name']
            except KeyError:
                artist = UNKNOWN_ARTIST
            try:
                album = json['album']['name']
            except KeyError:
                album = UNKNOWN_ARTIST
            try:
                isrc = json['external_ids']['isrc']
            except KeyError:
                isrc = None
            # Create new track
            print(title, artist, album, isrc)
            track = Track.objects.create(title=title, artist=artist, album=album, spotify_id=json['id'], isrc=isrc)
        else:
            # Ensure existing track has correct spotify id
            track.spotify_id = json['id']
        track.save()
