from django.http import HttpResponse
from django.shortcuts import render

from .models import *
from .playlist_import import import_spotify


def index(request):
    return render(request, 'playlstr/index.html', {'newest_playlist_list': Playlist.objects.order_by('-edit_date')})


def playlist(request, playlist_id):
    return render(request, 'playlstr/playlist.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id)})


def track(request, track_id):
    return render(request, 'playlstr/track.html', {'track': Track.objects.get(track_id=track_id)})


def edit_playlist(request, playlist_id):
    return render(request, 'playlstr/edit_playlist.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id)})


def import_playlist(request):
    return render(request, 'playlstr/import_playlist.html')


def spotify_import(request):
    return HttpResponse(import_spotify(request.POST))


def create_playlist(request):
    name = request.POST['name']
    new_list = Playlist.objects.create()
    if len(name) > 0:
        new_list.name = name
    new_list.save()
    return HttpResponse(new_list.playlist_id)

