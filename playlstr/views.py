from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db.models import Q
import json

from .models import *
from .playlist_import import import_spotify


def index(request):
    return render(request, 'playlstr/index.html', {'newest_playlist_list': Playlist.objects.order_by('-edit_date')})


def playlist(request, playlist_id):
    return render(request, 'playlstr/playlist.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id)})


def track(request, track_id):
    return render(request, 'playlstr/track.html', {'track': Track.objects.get(track_id=track_id)})


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


def track_autocomplete(request):
    if not request.is_ajax():
        return HttpResponse("Invalid")
    try:
        term = request.POST['term']
    except KeyError:
        return HttpResponse('None')
    try:
        start = int(request.POST['start'])
    except (KeyError, ValueError):
        start = 0
    try:
        results_count = int(request.POST['count'])
    except (KeyError, ValueError):
        results_count = 25
    '''
    query_set = Track.objects.filter(Q(title__icontains=term) | Q(artist__icontains=term) | Q(album__icontains=term))[
                start:start + results_count]
    '''
    query_set = Track.objects.filter(title__icontains=term)[start: start + results_count]
    values = [{
        'id': r.track_id,
        'title': r.title,
        'artist': r.artist,
        'album': r.album
    } for r in query_set]
    return JsonResponse(json.dumps(values), safe=False)
