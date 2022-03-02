from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import lxml.html

from playlstr.util.export import *
from playlstr.util.client import *
from playlstr.util.gplay import *
from .settings import LOGOUT_REDIRECT_URL


def index(request):
    return render(
        request,
        "playlstr/index.html",
        {"newest_playlist_list": Playlist.objects.order_by("-edit_date")},
    )


def playlist(request, playlist_id):
    return render(
        request,
        "playlstr/playlist.html",
        {
            "playlist": Playlist.objects.get(playlist_id=playlist_id),
            "tracks": [
                pt.track for pt in PlaylistTrack.objects.filter(playlist_id=playlist_id)
            ],
        },
    )


def track(request, track_id):
    return render(
        request, "playlstr/track.html", {"track": Track.objects.get(track_id=track_id)}
    )


def import_playlist(request):
    return render(request, "playlstr/import_playlist.html")


def spotify_import(request):
    params = {k: v[0] for (k, v) in dict(request.POST).items()}
    params["user"] = request.user.id
    params["access_token"] = request.COOKIES.get("spotify-token")
    result = import_spotify(params)
    if result == "invalid":
        return HttpResponse("Invalid URL", status=400)
    return HttpResponse(result)


def create_playlist(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    name = request.POST["name"]
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
        term = request.POST["term"]
    except KeyError:
        return HttpResponse("None")
    try:
        start = int(request.POST["start"])
    except (KeyError, ValueError):
        start = 0
    try:
        results_count = int(request.POST["count"])
    except (KeyError, ValueError):
        results_count = 25
    """
    query_set = Track.objects.filter(Q(title__icontains=term) | Q(artist__icontains=term) | Q(album__icontains=term))[
                start:start + results_count]
    """
    query_set = Track.objects.filter(title__icontains=term)[
        start : start + results_count
    ]
    values = [
        {"id": r.track_id, "title": r.title, "artist": r.artist, "album": r.album}
        for r in query_set
    ]
    return JsonResponse(json.dumps(values), safe=False)


def playlist_update(request):
    if not request.is_ajax() or "playlist" not in request.POST:
        return HttpResponse("Invalid", status=400)
    try:
        plist = Playlist.objects.get(playlist_id=request.POST["playlist"])
    except ObjectDoesNotExist:
        return HttpResponse("Invalid", status=400)
    if request.user not in plist.editors.all() and request.user != plist.owner:
        return HttpResponse("Unauthorized", status=401)
    update_result = update_playlist(request.POST)
    if update_result:
        return HttpResponse(update_result, status=400)
    return HttpResponse("success")


def logout_view(request):
    logout(request)
    return redirect(LOGOUT_REDIRECT_URL)


def user_spotify_token(request):
    if not request.is_ajax() or request.user is None:
        return HttpResponse("Invalid", status=400)
    json_resp = get_user_spotify_token(request.user)
    if "error" in json_resp:
        return HttpResponse(json_resp["error"], status=400)
    return JsonResponse(json_resp, safe=False)


def spotify_auth_user(request):
    if not request.is_ajax() or request.user is None:
        return HttpResponse("Invalid", status=400)
    return HttpResponse(
        spotify_parse_code({"post": request.POST, "user": request.user})
    )


def local_file_import(request):
    if (
        not request.is_ajax()
        or "playlist" not in request.POST
        or "name" not in request.POST
    ):
        return HttpResponse("Invalid", status=400)
    if not request.user:
        return HttpResponse("Unauthorized", status=401)
    result = import_playlist_from_string(
        request.POST["name"], request.POST["playlist"], request.user
    )
    return (
        HttpResponse(status=400, reason="Malformed or empty playlist")
        if result == "fail"
        else HttpResponse(result)
    )


def file_export(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    if "playlist_id" not in request.POST:
        return HttpResponse("Invalid", status=400)
    try:
        name = Playlist.objects.get(playlist_id=request.POST["playlist_id"]).name
    except ObjectDoesNotExist:
        return HttpResponse("Invalid", status=400)
    if request.POST.get("criteria"):
        tracks = tracks_matching_criteria(
            request.POST["playlist_id"], json.loads(request.POST["criteria"])
        )
    else:
        tracks = PlaylistTrack.objects.filter(
            playlist=request.POST["playlist_id"]
        ).values("track")
    try:
        if "filetype" in request.POST:
            if request.POST["filetype"] == "m3u":
                return HttpResponse(
                    export_as_m3u(name, tracks),
                    content_type="application/octet-stream",
                    status=200,
                )
            else:
                return HttpResponse(
                    export_as_text(name, tracks), content_type="text/plain"
                )
        else:
            return HttpResponse(export_as_text(name, tracks), content_type="text/plain")
    except ValueError:
        return HttpResponse("Invalid", status=400)


def spotify_login_redirect(request):
    return render(request, "playlstr/spotify_redirect.html")


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
    return render(
        request,
        "playlstr/export.html",
        {
            "playlist": Playlist.objects.get(playlist_id=playlist_id),
            "genres": list(genres),
            "explicit": explicit,
            "albums": list(albums),
            "artists": list(artists),
        },
    )


def my_profile(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    return redirect("/profile/{}/".format(request.user.id))


def profile(request, user_id):
    user = PlaylstrUser.objects.get(id=user_id)
    show_all = request.user == user
    owned = (
        Playlist.objects.filter(owner=user_id)
        if show_all
        else Playlist.objects.filter(owner=user_id, privacy=0)
    )
    return render(
        request,
        "playlstr/profile.html",
        {
            "username": user.get_username(),
            "my_profile": show_all,
            "owned_playlists": owned.all(),
            "editable_playlists": Playlist.objects.filter(editors__id=user_id).all(),
        },
    )


def fork_playlist(request, playlist_id):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    try:
        old_list = Playlist.objects.get(playlist_id=playlist_id)
    except ObjectDoesNotExist:
        return HttpResponse("Invalid playlist", status=401)
    new_list = Playlist.objects.create(
        name="Fork of {}".format(old_list.name),
        forked_from=old_list,
        owner=request.user,
    )
    idx = 0
    for ctrack in [
        pt.track for pt in PlaylistTrack.objects.filter(playlist=old_list).all()
    ]:
        PlaylistTrack.objects.create(playlist=new_list, track=ctrack, index=idx)
        idx += 1
    return redirect(new_list.get_absolute_url())


def create_track(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    if (
        not request.is_ajax()
        or not request.POST
        or "title" not in request.POST
        or request.POST["title"] is None
    ):
        return HttpResponse("Invalid", status=400)
    # Try to suggest a similar track if one exists
    track = get_similar_track(request.POST)
    if track is not None and (
        "force_creation" not in request.POST or not request.POST["force_creation"]
    ):
        return HttpResponse(
            "similar\n{}\n{}\n{}\n{}".format(
                track.track_id, track.title, track.artist, track.album
            )
        )
    try:
        track = create_custom_track(request.POST)
        if request.COOKIES.get("spotify-token"):
            match_track_spotify(track, request.COOKIES.get("spotify-token"))
        match_track_gplay(track)
        match_track_deezer(track)
        return HttpResponse(
            "{}\n{}\n{}\n{}".format(
                track.track_id, track.title, track.artist, track.album
            )
        )
    except KeyError:
        return HttpResponse("Invalid", status=400)


def search(request):
    if not request.GET.get("q"):
        return HttpResponse("No search query", status=400)
    playlists = Playlist.objects.filter(name__contains=request.GET.get("q")).all()
    return render(request, "playlstr/search_results.html", {"results": playlists})


def export_spotify(request):
    if not request.POST.get("playlist_id"):
        return HttpResponse("No playlist", status=400)
    user = PlaylstrUser.objects.filter(id=request.user.id).first()
    if user is None or not user.spotify_linked():
        access_token = request.COOKIES.get("spotify-token")
        spotify_id = spotify_id_from_token(access_token)
        if access_token is None or spotify_id is None:
            return HttpResponse("No Spotify token", status=400)
    else:
        access_token = user.spotify_token()
        spotify_id = user.spotify_id
        if spotify_id is None:
            if not user.update_spotify_info():
                return HttpResponse("Error getting Spotify ID", status=500)
            spotify_id = user.spotify_id
    if request.POST.get("criteria"):
        tracks = tracks_matching_criteria(
            request.POST["playlist_id"], json.loads(request.POST["criteria"])
        )
    else:
        tracks = PlaylistTrack.objects.filter(
            playlist=request.POST["playlist_id"]
        ).values("track")
    if len(tracks) == 0:
        return HttpResponse("Empty playlist", status=400)

    spotify_playlist = spotify_create_playlist(
        Playlist.objects.get(playlist_id=request.POST.get("playlist_id")).name,
        access_token,
        spotify_id,
    )
    if spotify_playlist.startswith("Error"):
        return HttpResponse(
            "Couldn't create playlist: ".format(spotify_playlist), status=500
        )
    if not add_tracks_to_spotify_playlist(tracks, spotify_playlist, access_token):
        return HttpResponse("Couldn't add tracks", status=500)
    return HttpResponse("https://open.spotify.com/playlist/{}".format(spotify_playlist))


@csrf_exempt
def client_import(request):
    if not request.POST.get("client_id"):
        return HttpResponse("No client id", status=400)
    user = PlaylstrUser.objects.filter(
        linked_clients__contains=[request.POST["client_id"]]
    ).first()
    if user is None:
        return HttpResponse("No user linked to client", status=400)
    try:
        tracks = json.loads(request.POST["tracks"])
    except KeyError:
        return HttpResponse("No tracks received", status=400)
    except json.JSONDecodeError:
        return HttpResponse("Invalid tracks json", status=400)
    else:
        try:
            name = request.POST["playlist_name"]
        except KeyError:
            name = None
        return HttpResponse(client_import_parse(name, tracks, user))


def client_code(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=401)
    return render(
        request,
        "playlstr/link.html",
        {"link_code": PlaylstrUser.objects.get(id=request.user.id).get_link_code()},
    )


@csrf_exempt
def client_link(request):
    link_code = request.POST.get("link")
    client_id = request.POST.get("client")
    if client_id is None:
        return HttpResponse("Invalid client id", status=400)
    if link_code is None:
        return HttpResponse("No link code given", status=400)
    try:
        link_client_code(link_code, client_id)
    except ValueError as e:
        return HttpResponse(str(e), status=400)
    return HttpResponse("Success")


def clear_linked_clients(request):
    if not request.user or not request.user.is_authenticated:
        return HttpResponse("Login first", status=400)
    if not request.is_ajax():
        return HttpResponse("", status=400)
    try:
        user = PlaylstrUser.objects.get(id=request.user.id)
    except ObjectDoesNotExist:
        return HttpResponse("Invalid user", status=400)
    user.linked_clients.clear()
    user.save()
    return HttpResponse("Success")


@login_required
def update_profile(request):
    if not (request.user and request.is_ajax() and request.POST.get("changes")):
        return HttpResponse("", status=400)
    try:
        user = PlaylstrUser.objects.get(id=request.user.id)
    except ObjectDoesNotExist:
        return HttpResponse("Invalid user", status=400)
    try:
        changes = json.loads(request.POST.get("changes"))
    except (json.JSONDecodeError, KeyError):
        return HttpResponse("Invalid changes", status=400)
    if "firstname" in changes:
        user.first_name = changes["firstname"]
    if "lastname" in changes:
        user.last_name = changes["lastname"]
    if "email" in changes:
        user.email = changes["email"]
    if "username" in changes:
        user.username = changes["username"]
    user.save()
    return HttpResponse("Success")


def gplay_import(request):
    if not request.is_ajax():
        return HttpResponse("", status=400)
    playlist = request.POST.get("playlist_url")
    if not playlist or not re.match(
        "^https?://play\.google\.com/music/preview/pl/.*", playlist
    ):
        return HttpResponse("Invalid playlist", status=400)
    response = requests.get(playlist)
    if response.status_code != 200:
        return HttpResponse(
            "Error getting playlist ({})".format(response.reason), status=400
        )
    html = lxml.html.fromstring(response.content)
    result = import_gplay_playlist(html)
    if not result:
        return HttpResponse("Error importing", status=500)
    return HttpResponse(result)
