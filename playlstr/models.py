from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

UNKNOWN_ALBUM = 'Unknown album'
UNKNOWN_ARTIST = 'Unknown artist'


class PlaylstrUser(AbstractUser):
    spotify_access_token = models.CharField(max_length=256, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=256, null=True, blank=True)
    spotify_token_expiry = models.DateTimeField(null=True, blank=True)

    def spotify_linked(self):
        return self.spotify_access_token is not None and self.spotify_refresh_token is not None

    def spotify_token_expired(self):
        return self.spotify_token_expiry >= timezone.now()


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
    track_number = models.CharField(max_length=2, null=True, blank=True)
    album_artist = models.CharField(max_length=255, default=None, blank=True, null=True)
    year = models.IntegerField(default=None, blank=True, null=True)
    release_date = models.DateField(default=None, blank=True, null=True)
    image_url = models.CharField(max_length=512, default=None, blank=True, null=True)
    duration = models.IntegerField(default=None, blank=True, null=True)
    genres = ArrayField(models.CharField(max_length=20, blank=False, null=False), null=True, blank=True)
    album_release = models.CharField(max_length=64, blank=True, null=True, unique=True)
    explicit = models.BooleanField(default=False)
    source = models.SmallIntegerField(
        choices=(
            (0, "Manual"),
            (1, "Spotify"),
            (2, "Local file"),
            (3, "Google Play"),
            (4, "Musicbrainz"),
            (5, "Deezer")
        ), default=0, null=False
    )
    md5 = models.CharField(max_length=32, blank=True, null=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    # External identifiers
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    deezer_id = models.CharField(max_length=64, default=None, null=True, blank=True, unique=True)
    isrc = models.CharField(max_length=24, default=None, null=True, blank=True, unique=True)
    mb_id = models.CharField(max_length=36, default=None, null=True, blank=True, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['title', 'album', 'artist', 'album_release', 'duration'],
                                    name='unique tracks')
        ]

    def __str__(self):
        return "({}) {} - {}".format(self.track_id, self.artist, self.title)

    def as_export_text(self):
        return '{} - {} ({}{})'.format(self.artist, self.title, self.album,
                                       '' if self.year is None else ', {}'.format(self.year))


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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='owner')
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='editors',
                                     blank=True)  # Users who can modify this playlist
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    last_sync_spotify = models.DateTimeField(max_length=64, default=timezone.now)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)

    def get_absolute_url(self):
        url = '/list/{}/'.format(self.playlist_id)
        print('loading url {}'.format(url))
        return url


class PlaylistTrack(models.Model):
    """
    A track within a playlist
    """
    pt_id = models.AutoField(primary_key=True)
    track = models.ForeignKey(Track, null=False, blank=False, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, null=False, blank=False, on_delete=models.CASCADE)
    index = models.PositiveIntegerField(null=False, blank=False)  # Index within playlist
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    add_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['index']
        constraints = [
            models.UniqueConstraint(fields=['track', 'playlist'], name='track only in playlist once'),
            models.UniqueConstraint(fields=['playlist', 'index'], name='unique track index'),
        ]
