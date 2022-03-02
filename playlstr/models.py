import json
import random
import string
from base64 import b64encode
from math import floor

import requests
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from .apikeys import *

UNKNOWN_ALBUM = "Unknown album"
UNKNOWN_ARTIST = "Unknown artist"


class PlaylstrUser(AbstractUser):
    spotify_id = models.CharField(max_length=128, null=True, blank=True)
    spotify_username = models.CharField(max_length=128, null=True, blank=True)
    spotify_country = models.CharField(max_length=3, null=True, blank=True)
    spotify_access_token = models.CharField(max_length=256, null=True, blank=True)
    spotify_refresh_token = models.CharField(max_length=256, null=True, blank=True)
    spotify_token_expiry = models.DateTimeField(null=True, blank=True)
    linked_clients = ArrayField(
        models.CharField(max_length=20, null=False, blank=False),
        null=False,
        default=list,
    )
    link_code = models.CharField(max_length=6, null=True, blank=True)
    link_code_generated = models.DateTimeField(null=True, blank=True)

    def get_link_code(self):
        self.link_code = "".join(
            random.choice(string.ascii_lowercase + string.digits) for i in range(6)
        )
        while PlaylstrUser.objects.filter(link_code=self.link_code).exists():
            self.link_code = "".join(
                random.choice(string.ascii_lowercase + string.digits) for i in range(6)
            )
        self.link_code_generated = timezone.now()
        self.save()
        return self.link_code

    def spotify_info(self):
        if not self.spotify_linked():
            return {"error": "unauthorized"}
        if (
            self.spotify_token_expiry is None
            or self.spotify_token_expiry <= timezone.now()
        ):
            updated_token = self.update_spotify_tokens()
            if updated_token != "success":
                return {"error": updated_token}
        if not self.spotify_id:
            self.update_spotify_info()
        return {
            "access_token": self.spotify_access_token,
            "expires_in": floor(
                (self.spotify_token_expiry - timezone.now()).total_seconds()
            ),
            "spotify_id": self.spotify_id,
        }

    def spotify_token(self):
        if not self.spotify_linked():
            return ""
        if self.spotify_token_expiry >= timezone.now():
            self.update_spotify_tokens()
        return self.spotify_access_token

    def spotify_linked(self):
        return (
            self.spotify_access_token is not None
            and self.spotify_refresh_token is not None
        )

    def spotify_token_expired(self):
        return self.spotify_token_expiry >= timezone.now()

    def update_spotify_info(self) -> str:
        """
        Updates spotify_username and spotify_id for user
        :return: empty string if update successful else error information
        """
        if self.spotify_token_expiry:
            self.update_spotify_tokens()
        headers = {"Authorization": "Bearer {}".format(self.spotify_access_token)}
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        if response.status_code != 200:
            return "{}: {}".format(response.status_code, response.reason)
        user = response.json()
        if "country" in user:
            self.spotify_country = user["country"]
        if "display_name" in user and user["display_name"]:
            self.spotify_username = user["display_name"]
        self.spotify_id = user["id"]
        self.save()
        return ""

    def update_spotify_tokens(self) -> str:
        body = {
            "grant_type": "refresh_token",
            "refresh_token": self.spotify_refresh_token,
        }
        headers = {
            "Authorization": "Basic {}".format(
                b64encode(
                    (SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET).encode()
                ).decode()
            )
        }
        response = requests.post(
            "https://accounts.spotify.com/api/token", headers=headers, data=body
        )
        if response.status_code != 200:
            return "server responded with {} {}".format(
                response.status_code, response.reason
            )
        try:
            info = response.json()
        except json.JSONDecodeError:
            return "json error"
        if "access_token" not in info:
            return "access token error"
        if "expires_in" not in info:
            info["expires_in"] = 3600
        if "refresh_token" in info:
            self.spotify_refresh_token = info["refresh_token"]
        self.spotify_access_token = info["access_token"]
        try:
            self.spotify_token_expiry = timezone.now() + timezone.timedelta(
                seconds=int(info["expires_in"])
            )
        except ValueError:
            return "invalid expiry"
        self.save()
        return "success"


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
    genres = ArrayField(
        models.CharField(max_length=20, blank=False, null=False), null=True, blank=True
    )
    album_release = models.CharField(max_length=64, blank=True, null=True, unique=True)
    explicit = models.BooleanField(default=False)
    source = models.SmallIntegerField(
        choices=(
            (0, "Manual"),
            (1, "Spotify"),
            (2, "Local file"),
            (3, "Google Play"),
            (4, "Musicbrainz"),
            (5, "Deezer"),
        ),
        default=0,
        null=False,
    )
    md5 = models.CharField(max_length=32, blank=True, null=True, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    # External identifiers
    spotify_id = models.CharField(
        max_length=64, default=None, null=True, blank=True, unique=False
    )
    gplay_id = models.CharField(
        max_length=64, default=None, null=True, blank=True, unique=False
    )
    gplay_album_id = models.CharField(
        max_length=64, default=None, null=True, blank=True, unique=False
    )
    deezer_id = models.CharField(
        max_length=64, default=None, null=True, blank=True, unique=False
    )
    isrc = models.CharField(
        max_length=24, default=None, null=True, blank=True, unique=True
    )
    mb_id = models.CharField(
        max_length=36, default=None, null=True, blank=True, unique=True
    )
    youtube_id = models.CharField(
        max_length=11, default=None, null=True, blank=True, unique=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "album", "artist", "album_release", "duration"],
                name="unique tracks",
            )
        ]

    def __str__(self):
        return "({}) {} - {}".format(self.track_id, self.artist, self.title)

    def as_export_text(self):
        return "{} - {} ({}{})".format(
            self.artist,
            self.title,
            self.album,
            "" if self.year is None else ", {}".format(self.year),
        )

    def json(self):
        return {
            "title": self.title,
            "id": self.track_id,
            "album": self.album,
            "artist": self.artist,
            "spotify_id": self.spotify_id,
            "year": self.year,
            "name": self.title,
        }


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
            (
                1,
                "Unlisted",
            ),  # Doesn't show up anywhere but viewable by anybody if you have the link
            (2, "Private"),  # Only shows up to owner/editors
        ),
        default=0,
        null=False,
    )
    forked_from = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    # Creator of this playlist
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owner",
    )
    spotify_creator_id = models.CharField(
        max_length=64, null=True, blank=True, default=None
    )
    spotify_creator_name = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="editors", blank=True
    )  # Users who can modify this playlist
    spotify_id = models.CharField(max_length=64, default=None, null=True, blank=True)
    last_sync_spotify = models.DateTimeField(max_length=64, default=timezone.now)
    gplay_id = models.CharField(max_length=64, default=None, null=True, blank=True)

    def get_absolute_url(self):
        return "/list/{}/".format(self.playlist_id)


class PlaylistTrack(models.Model):
    """
    A track within a playlist
    """

    pt_id = models.AutoField(primary_key=True)
    track = models.ForeignKey(Track, null=False, blank=False, on_delete=models.CASCADE)
    playlist = models.ForeignKey(
        Playlist, null=False, blank=False, on_delete=models.CASCADE
    )
    index = models.PositiveIntegerField(
        null=False, blank=False
    )  # Index within playlist
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    add_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["index"]
        constraints = [
            models.UniqueConstraint(
                fields=["track", "playlist"], name="track only in playlist once"
            ),
            models.UniqueConstraint(
                fields=["playlist", "index"], name="unique track index"
            ),
        ]
