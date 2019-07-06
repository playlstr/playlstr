from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from playlstr.util.export import *
from .settings import LOGOUT_REDIRECT_URL


def index(request):
    return render(request, 'playlstr/index.html', {'newest_playlist_list': Playlist.objects.order_by('-edit_date')})


def playlist(request, playlist_id):
    return render(request, 'playlstr/playlist.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id),
                                                      'tracks': [pt.track for pt in
                                                                 PlaylistTrack.objects.filter(playlist_id=playlist_id)]
                                                      })


def track(request, track_id):
    return render(request, 'playlstr/track.html', {'track': Track.objects.get(track_id=track_id)})


def import_playlist(request):
    return render(request, 'playlstr/import_playlist.html')


def spotify_import(request):
    params = request.POST
    params['user'] = request.user
    return HttpResponse(import_spotify(params))


def create_playlist(request):
    name = request.POST['name']
    new_list = Playlist.objects.create()
    if len(name) > 0:
        new_list.name = name
    new_list.owner = request.user
    new_list.save()
    return HttpResponse(new_list.playlist_id)


def track_autocomplete(request):
    if not request.is_ajax():
        return HttpResponse("Invalid", status=400)
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


def playlist_update(request):
    if not request.is_ajax() or 'playlist' not in request.POST:
        return HttpResponse("Invalid", status=400)
    try:
        plist = Playlist.objects.get(playlist_id=request.POST['playlist'])
    except ObjectDoesNotExist:
        return HttpResponse("Invalid", status=400)
    if request.user not in plist.editors.all() and request.user != plist.owner:
        return HttpResponse("Unauthorized", status=401)
    return HttpResponse(update_playlist(request.POST))


def logout_view(request):
    logout(request)
    return redirect(LOGOUT_REDIRECT_URL)


def get_spotify_token(request):
    if not request.is_ajax() or request.user is None:
        return HttpResponse("Invalid", status=400)
    return JsonResponse(json.dumps(get_user_spotify_token(request.user)), safe=False)


def spotify_auth_user(request):
    if not request.is_ajax() or request.user is None:
        return HttpResponse("Invalid", status=400)
    return HttpResponse(spotify_parse_code({'post': request.POST, 'user': request.user}))


def local_file_import(request):
    if not request.is_ajax() or 'playlist' not in request.POST or 'name' not in request.POST:
        return HttpResponse('Invalid', status=400)
    if not request.user:
        return HttpResponse('Unauthorized', status=401)
    result = import_playlist_from_string(request.POST['name'], request.POST['playlist'], request.user)
    return HttpResponse(status=400, reason='Malformed or empty playlist') if result == 'fail' else HttpResponse(result)


def file_export(request):
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    if 'playlist_id' not in request.POST:
        return HttpResponse('Invalid', status=400)
    try:
        name = Playlist.objects.get(playlist_id=request.POST['playlist_id']).name
    except ObjectDoesNotExist:
        return HttpResponse('Invalid', status=400)
    if request.POST.get('criteria'):
        tracks = tracks_matching_criteria(request.POST['playlist_id'], json.loads(request.POST['criteria']))
    else:
        tracks = PlaylistTrack.objects.filter(playlist=request.POST['playlist_id']).values('track')
    try:
        if 'filetype' in request.POST:
            if request.POST['filetype'] == 'm3u':
                return HttpResponse(export_as_m3u(name, tracks), content_type='application/octet-stream', status=200)
            else:
                return HttpResponse(export_as_text(name, tracks), content_type='text/plain')
        else:
            return HttpResponse(export_as_text(name, tracks), content_type='text/plain')
    except ValueError:
        return HttpResponse('Invalid', status=400)


def spotify_login_redirect(request):
    return render(request, 'playlstr/spotify_redirect.html')


def export_playlist(request, playlist_id):
    tracks = [pt.track for pt in PlaylistTrack.objects.filter(playlist_id=playlist_id)]
    genres = set()
    albums = set()
    artists = set()
    explicit = False
    for track in tracks:
        if track.explicit:
            explicit = True
        if track.genres is not None:
            for genre in track.genres:
                genres.add(genre)
        albums.add(track.album)
        artists.add(track.artist)
    return render(request, 'playlstr/export.html', {'playlist': Playlist.objects.get(playlist_id=playlist_id),
                                                    'genres': list(genres),
                                                    'explicit': explicit,
                                                    'albums': list(albums),
                                                    'artists': list(artists)
                                                    })


def my_profile(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse('Not logged in', status=404)
    return redirect('/profile/{}/'.format(request.user.id))


def profile(request, user_id):
    user = PlaylstrUser.objects.get(id=user_id)
    show_all = request.user == user
    owned = Playlist.objects.filter(owner=user_id) if show_all else Playlist.objects.filter(owner=user_id, privacy=0)
    return render(request, 'playlstr/profile.html',
                  {'username': user.get_username(), 'my_profile': show_all, 'owned_playlists': owned.all(),
                   'editable_playlists': Playlist.objects.filter(editors__id=user_id).all()})


def fork_playlist(request, playlist_id):
    if not request.user.is_authenticated:
        return HttpResponse('Not logged in', status=403)
    try:
        old_list = Playlist.objects.get(playlist_id=playlist_id)
    except ObjectDoesNotExist:
        return HttpResponse('Invalid playlist', status=401)
    new_list = Playlist.objects.create(name='Fork of {}'.format(old_list.name), forked_from=old_list,
                                       owner=request.user)
    idx = 0
    for ctrack in [pt.track for pt in PlaylistTrack.objects.filter(playlist=old_list).all()]:
        PlaylistTrack.objects.create(playlist=new_list, track=ctrack, index=idx)
        idx += 1
    return redirect(new_list.get_absolute_url())


def create_track(request):
    if not request.is_ajax() or not request.POST or 'title' not in request.POST or request.POST['title'] is None:
        return HttpResponse('Invalid', status=400)
    # Try to suggest a similar track if one exists
    track = get_similar_track(request.POST)
    if track is not None and ('force_creation' not in request.POST or not request.POST['force_creation']):
        return HttpResponse('similar\n{}\n{}\n{}\n{}'.format(track.track_id, track.title, track.artist, track.album))
    try:
        track = create_custom_track(request.POST)
        return HttpResponse('{}\n{}\n{}\n{}'.format(track.track_id, track.title, track.artist, track.album))
    except KeyError:
        return HttpResponse('Invalid', status=400)


def search(request):
    if not request.GET.get('q'):
        return HttpResponse('No search query', status=400)
    playlists = Playlist.objects.filter(name__contains=request.GET.get('q')).all()
    return render(request, 'playlstr/search_results.html', {'results': playlists})


@csrf_exempt
def client_import(request):
    try:
        tracks = json.loads(request.POST['tracks'])
    except KeyError:
        return HttpResponse('No tracks received', status=400)
    except json.JSONDecodeError:
        return HttpResponse('Invalid tracks json', status=400)
    else:
        try:
            name = request.POST['playlist_name']
        except KeyError:
            name = None
        return HttpResponse(client_import_parse(name, tracks))
