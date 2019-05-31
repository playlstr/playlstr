from django.contrib import admin

from .models import *

admin.site.register(Track)
admin.site.register(Playlist)
admin.site.register(PlaylistTrack)
