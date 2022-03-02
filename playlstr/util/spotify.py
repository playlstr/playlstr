import re
from typing import Optional

from django.db.models import Q
from django.db.utils import IntegrityError

from playlstr.models import *
from playlstr.util.track import *

from threading import Thread


def import_spotify(info: dict) -> str:
    """
    Import Spotify playlist and return playlist ID or cause of error if unsuccessful
    :param info: dict where playlist_url is the url of the playlist and access_token is the Spotify access token
    :return: playlist ID or cause of error if unsuccessful
    """
    url = info["playlist_url"]
    # Validate URL
    if not (
        isinstance(url, str)
        and re.match(r"^http(s?)://open\.spotify\.com/playlist/[a-zA-Z\d]*/?", url)
    ):
        return "invalid"
    playlist_id = url[-23:0] if url[-1] == "/" else url[-22:]
    query_url = "https://api.spotify.com/v1/playlists/" + playlist_id
    query_headers = {"Authorization": "Bearer {}".format(info["access_token"])}
    # Get/create playlist
    playlist_json = requests.get(query_url, headers=query_headers).json()
    playlist = Playlist(
        name=playlist_json["name"],
        last_sync_spotify=timezone.now(),
        spotify_id=playlist_id,
    )
    if "user" in info:
        playlist.owner = PlaylstrUser.objects.filter(id=info["user"]).first()
    if "owner" in playlist_json:
        playlist.spotify_creator_id = playlist_json["owner"]["id"]
        playlist.spotify_creator_name = playlist_json["owner"]["display_name"]
    playlist.save()
    # Get playlist tracks
    tracks_response = requests.get(query_url + "/tracks", headers=query_headers)
    if tracks_response.status_code != 200:
        return tracks_response.reason
    tracks_json = tracks_response.json()
    try:
        return "Error: " + tracks_json["error_description"]
    except KeyError:
        pass
    # Get list of tracks
    index = -1
    while "next" in tracks_json and tracks_json["next"] is not None:
        for j in tracks_json["items"]:
            index += 1
            track = track_from_spotify_json(j["track"])
            try:
                PlaylistTrack.objects.create(
                    playlist=playlist, track=track, index=index
                )
            except IntegrityError as e:
                print("Error adding track {}: {}".format(str(track), str(e)))
                continue
        tracks_json = requests.get(tracks_json["next"], headers=query_headers).json()
    return str(playlist.playlist_id)


def track_from_spotify_json(
    track_json: dict, match_gplay: bool = False, match_deezer: bool = False
) -> Track:
    """
    Return a track matching Spotify track JSON
    :param track_json: the Spotify track JSON
    :param match_gplay: if true try to link a Google Play ID for the new track
    :param match_deezer: if true try to link a Deezer ID for the new track
    :return: Track matching Spotify JSON
    """
    # Check if track exists with the same Spotify ID
    if track_json["id"] is None:
        track = None
    else:
        query = Q(spotify_id=track_json["id"])
        try:
            query.add(Q(isrc=track_json["external_ids"]["isrc"]), Q.OR)
        except KeyError:
            pass
        track = Track.objects.filter(query).first()
    if track is None:
        title = track_json["name"]
        try:
            isrc = track_json["external_ids"]["isrc"]
        except KeyError:
            isrc = None
        # Create new track
        track = Track.objects.create(title=title)
    track.spotify_id = track_json["id"]
    # Get track attributes
    try:
        track.artist = track_json["artists"][0]["name"]
    except KeyError:
        pass
    try:
        track.album = track_json["album"]["name"]
    except KeyError:
        pass
    try:
        track.duration = round(track_json["duration_ms"] * 1000)
    except KeyError:
        pass
    track.save()
    if match_gplay and (not track.gplay_id or not track.gplay_album_id):
        gplay_thread = Thread(target=match_track_gplay, args=(track,))
        gplay_thread.start()
    if match_deezer and not track.deezer_id:
        deezer_thread = Thread(target=match_track_deezer, args=(track,))
        deezer_thread.start()
    return track


def valid_spotify_token(token: str) -> bool:
    """
    Return true iff token is a valid Spotify access token
    :param token: access token to test
    :return: whether token is a valid Spotify access token
    """
    test_url = "https://api.spotify.com/v1/tracks/11dFghVXANMlKmJXsNCbNl"
    headers = {"Authorization": "Bearer {}".format(token)}
    response = requests.get(test_url, headers=headers)
    return response.status_code == 200


def get_user_spotify_token(user: PlaylstrUser) -> dict:
    """
    Get Spotify access token and expiry of the user PlaylstrUser
    :param user: user to get access token of
    :return: dict containing access token and time from now until the access token expires on success or an error
    reason at the key 'error'
    """
    if not user.spotify_linked():
        return {"error": "spotify not linked"}
    if user.spotify_token_expiry is None or user.spotify_token_expiry <= timezone.now():
        updated_token = user.update_spotify_tokens()
        if updated_token != "success":
            return {"error": updated_token}
    return {
        "access_token": user.spotify_access_token,
        "expires_in": floor(
            (user.spotify_token_expiry - timezone.now()).total_seconds()
        ),
    }


def spotify_parse_code(info: dict) -> Optional[str]:
    """
    Set up access token and refresh token for user given access code
    :param info: the post data for the spotify code parsing and the user who the code corresponds to
    :return: None on success or an error reason on failure
    """
    data = info["post"]
    user = info["user"]
    headers = {
        "Authorization": "Basic {}".format(
            b64encode(
                (SPOTIFY_CLIENT_ID + ":" + SPOTIFY_CLIENT_SECRET).encode()
            ).decode()
        )
    }
    body = {
        "grant_type": "authorization_code",
        "code": data["code"],
        "redirect_uri": data["redirect_uri"],
    }
    response = requests.post(
        "https://accounts.spotify.com/api/token", headers=headers, data=body
    )
    if response.status_code != 200:
        return response.text
    try:
        info = response.json()
    except json.JSONDecodeError:
        return "invalid json"
    if "access_token" not in info or "refresh_token" not in info:
        return ""
    if "expires_in" not in info:
        info["expires_in"] = 3600
    user.spotify_refresh_token = info["refresh_token"]
    user.spotify_access_token = info["access_token"]
    try:
        user.spotify_token_expiry = timezone.now() + timezone.timedelta(
            seconds=int(info["expires_in"])
        )
    except ValueError:
        return "Invalid expiry date"
    user.update_spotify_info()
    user.save()
    return None


def spotify_create_playlist(
    playlist_name: str,
    access_token: str,
    user_spotify_id: str,
    public: bool = True,
    description: str = None,
) -> str:
    """
    Create a playlist on Spotify
    :param playlist_name: name of the playlist
    :param access_token: Spotify access token to create playlist with
    :param user_spotify_id: Spotify id of user who will own the playlist
    :param public: whether the playlist should be public
    :param description: description of the playlist on spotify
    :return: spotify id of created playlist or an error message starting with 'Error ' on error
    """
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Content-Type": "application/json",
    }
    body = {"name": playlist_name, "public": public}
    if description is not None:
        body["description"] = description
    response = requests.post(
        "https://api.spotify.com/v1/users/{}/playlists".format(user_spotify_id),
        headers=headers,
        json=body,
    )
    if response.status_code != 200 and response.status_code != 201:
        return "Error {}".format(response.text)
    return response.json()["id"]


def add_tracks_to_spotify_playlist(
    tracks: list, playlist_spotify_id: str, access_token: str
) -> Optional[str]:
    """
    Add list of tracks to spotify playlist
    :param tracks: list of Track to add to the playlist
    :param playlist_spotify_id: spotify id of the playlist
    :param access_token: Spotify access token of user who can add tracks to the playlist
    :return: error reason on failure or None on success
    """
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Content-Type": "application/json",
    }
    # Add tracks 100 at a time per Spotify API docs
    for i in range(0, len(tracks), 100):
        last = min(i + 100, len(tracks))
        uris = []
        for t in tracks[i:last]:
            if t.spotify_id:
                uris.append("spotify:track:{}".format(t.spotify_id))
            elif match_track_spotify(t, access_token):
                uris.append("spotify:track:{}".format(t.spotify_id))
        response = requests.post(
            "https://api.spotify.com/v1/playlists/{}/tracks".format(
                playlist_spotify_id
            ),
            headers=headers,
            json={"uris": uris},
        )
        if response.status_code != 200 and response.status_code != 201:
            return "Error: {}".format(response.text)
        if last == len(tracks):
            break
    return None


def spotify_playlist_as_json_tracks(playlist_id: int, access_token: str) -> list:
    """
    Return list of track json for all tracks in Spotify playlist
    :param playlist_id: Spotify id of playlist to get
    :param access_token: Spotify access token of user with access to the playlist
    :return: list of dicts which are spotify track json objects
    """
    query_url = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
    query_headers = {"Authorization": "Bearer {}".format(access_token)}
    # Get playlist tracks
    tracks_response = requests.get(query_url, headers=query_headers)
    if tracks_response.status_code != 200:
        return tracks_response.reason
    tracks_json = tracks_response.json()
    if "error_description" in tracks_json:
        return []
    # Get list of tracks
    tracks = []
    while "next" in tracks_json and tracks_json["next"] is not None:
        for t in tracks_json["items"]:
            tracks.append(t["track"])
        tracks_json = requests.get(tracks_json["next"], headers=query_headers).json()
    return tracks


def spotify_id_from_token(access_token: str) -> Optional[str]:
    """
    Return Spotify ID of the user corresponding to access token or None on error
    :param access_token: access token to get spotify ID of
    :return: Spotify id of access token or None if an error occurred
    """
    if access_token is None:
        return None
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.post("https://api.spotify.com/v1/me", headers=headers)
    if response.status_code != 200:
        return None
    user = response.json()
    if "id" not in user:
        return None
    return user["id"]


def spotify_track_search(query: str, access_token: str) -> dict:
    """
    Get results of spotify search for query
    :param query: query to send to spotify
    :param access_token: access token to search with
    :return: dict containing spotify track json objects or 'error' and 'status' on error
    """
    response = requests.get(
        "https://api.spotify.com/v1/search?q={}&type=track".format(query),
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    if (
        response.status_code == 200
        and "tracks" in response.text
        and "items" in response.text
    ):
        return json.loads(response.text)["tracks"]["items"]
    return {"error": response.reason, "status": response.status_code}


def match_track_spotify(
    track: Track,
    access_token: str,
    match_title=True,
    match_album=True,
    match_artist=True,
    *match_custom
) -> bool:
    """
    Find Spotify track matching the track info and update the Track with Spotify info if specified attributes are the same
    :param track: Track to find matching info for
    :param access_token: Spotify access token to use when searching
    :param match_title: whether to require matching track title to update track
    :param match_album: whether to require matching track album to update track
    :param match_artist: whether to require matching track artist to update track
    :param match_custom: Track attributes which must be the same as the Spotify attribute
    :return: whether the track was updated
    :raises AttributeError: if a key in match_custom is not in track or a Spotify track
    """
    # Make sure all the custom attributes are valid
    for req in match_custom:
        if not hasattr(track, req):
            raise AttributeError
    spotify_results = spotify_track_search(
        "{} {}".format(track.title, track.artist)
        if track.artist != UNKNOWN_ARTIST
        else track.title,
        access_token,
    )
    if "error" in spotify_results:
        print("error {} {}".format(spotify_results["status"], spotify_results["error"]))
        return False
    for strack in spotify_results:
        if match_title and strack["name"] != track.title:
            continue
        if match_artist and strack["artists"][0]["name"] != track.artist:
            continue
        if match_album and strack["album"]["name"] != track.album:
            continue
        reqs_matched = False if match_custom else True
        for req in match_custom:
            if req not in strack:
                raise AttributeError
            if strack[req] != getattr(track, req):
                reqs_matched = False
                break
        if not reqs_matched:
            continue
        track.spotify_id = strack["id"]
        track.save()
        return True
    return False
