from django.db import models
from sortedm2m.fields import SortedManyToManyField
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import json

UNKNOWN_ALBUM = 'Unknown album'
UNKNOWN_ARTIST = 'Unknown artist'


class Track(models.Model):
    """
    A single track
    """
    # Fundamental track info
    track_id = models.AutoField(primary_key=True)
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
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    deezer_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    isrc = models.CharField(max_length=24, default=None, null=True, blank=True, unique=True)
    mb_id = models.CharField(max_length=36, default=None, null=True, blank=True, unique=True)

    def __str__(self):
        return "({}) {} - {}".format(self.track_id, self.artist, self.title)


class Playlist(models.Model):
    """
    A playlist
    """
    playlist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, default="Playlist {}".format(playlist_id))
    create_date = models.DateTimeField(default=timezone.now)
    edit_date = models.DateTimeField(default=timezone.now)
    sublists = models.ManyToManyField("self", blank=True)
    privacy = models.SmallIntegerField(
        choices=(
            (0, "Public"),  # Shows up everywhere (search results, latest updates, etc.)
            (1, "Unlisted"),  # Doesn't show up anywhere but viewable by anybody if you have the link
            (2, "Private")  # Only shows up to owner/editors
        ), default=0, null=False
    )
    # Creator of this playlist
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owner')
    editors = models.ManyToManyField(User, related_name='editors', blank=True)  # Users who can modify this playlist
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    last_sync_spotify = models.DateTimeField(max_length=64, default=timezone.now)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)


class PlaylistTrack(models.Model):
    """
    A track within a playlist
    """
    pt_id = models.AutoField(primary_key=True)
    track = models.ForeignKey(Track, null=False, blank=False, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, null=False, blank=False, on_delete=models.CASCADE)
    index = models.PositiveIntegerField(null=False, blank=False)  # Index within playlist
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    add_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['index']
        constraints = [
            models.UniqueConstraint(fields=['track', 'playlist'], name='unique playlist+track'),
            models.UniqueConstraint(fields=['playlist', 'index'], name='unique track index'),
        ]
