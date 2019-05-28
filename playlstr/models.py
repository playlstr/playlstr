from django.db import models
from sortedm2m.fields import SortedManyToManyField
from django.utils import timezone
from django.contrib.auth.models import User

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
    duration_ms = models.IntegerField(default=None, blank=True, null=True)
    # External identifiers
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    deezer_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    isrc = models.CharField(max_length=24, default=None, null=True, blank=True)
    mb_id = models.CharField(max_length=36, default=None, null=True, blank=True)


class Playlist(models.Model):
    """
    A playlist
    """
    playlist_id = models.AutoField(primary_key=True)  # Internal DB ID
    name = models.CharField(max_length=255, default="Playlist {}".format(playlist_id))
    tracks = SortedManyToManyField(Track)
    create_date = models.DateTimeField(default=timezone.now)
    edit_date = models.DateTimeField(default=timezone.now)
    sublists = models.ManyToManyField("self")
    '''
    privacy = models.SmallIntegerField(
        choices=(
            (0, "Public"),  # Shows up everywhere (search results, latest updates, etc.)
            (1, "Unlisted"),  # Doesn't show up anywhere but viewable by anybody if you have the link
            (2, "Private")  # Only shows up to owner/editors
        ), default=0, null=False
    )
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Creator of this playlist
    editors = models.ManyToManyField(User)  # Users who can modify this playlist
    '''
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    last_sync_spotify = models.DateTimeField(max_length=64, default=timezone.now)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)
