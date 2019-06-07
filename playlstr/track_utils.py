import json

from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from .models import *


def create_custom_track(data):
    info = json.loads(data)
    if 'title' not in info:
        return 'invalid title'
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
    if 'duration_ms' in info:
        track.duration_ms = int(info['duration_ms'])
    track.save()
    return 'success'
