from django.db import models
from datetime import datetime

UNKNOWN_ALBUM = 'Unknown album'
UNKNOWN_ARTIST = 'Unknown artist'


class Track(models.Model):
    """
    A single track
    """
    # Fundamental track info
    track_id = models.AutoField(primary_key=True)  # Internal DB ID
    title = models.CharField(max_length=255, null=False)
    album = models.CharField(max_length=255, default=UNKNOWN_ALBUM)
    artist = models.CharField(max_length=255, default=UNKNOWN_ARTIST)
    # Additional track info
    is_single = models.BooleanField(default=False)
    album_artist = models.CharField(max_length=255, default=None, blank=True, null=True)
    release_date = models.DateField(default=None, blank=True, null=True)
    image_url = models.CharField(max_length=512, default=None, blank=True, null=True)
    # External identifiers
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    deezer_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    isrc = models.CharField(max_length=12, default=None, null=True, blank=True)
    mb_id = models.CharField(max_length=36, default=None, null=True, blank=True)


class Playlist(models.Model):
    """
    A playlist
    """
    playlist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    tracks = models.ManyToManyField(Track)
    create_date = models.DateTimeField(default=datetime.now)
    edit_date = models.DateTimeField(default=datetime.now)
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    last_sync_spotify = models.DateTimeField(max_length=64, default=datetime.now)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)
