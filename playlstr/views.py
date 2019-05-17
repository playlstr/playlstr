from django.http import HttpResponse
from django.shortcuts import render, render_to_response

from .models import *


def index(request):
    latest_playlist_list = Playlist.objects.order_by('edit_date')
    return render(request, 'playlstr/index.html', {'latest_playlist_list': latest_playlist_list})


def playlist(request, playlist_id):
    return render(request, 'playlstr/playlist.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id)})


def track(request, track_id):
    return render(request, 'playlstr/track.html', {'track': Track.objects.get(track_id=track_id)})


def edit_playlist(request, playlist_id):
    return HttpResponse("Editing ".format(playlist_id))
