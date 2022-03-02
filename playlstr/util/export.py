from .playlist import *


def export_as_text(playlist_name: str, tracks: list) -> str:
    text = playlist_name + "\n\n"
    for track in Track.objects.filter(track_id__in=tracks):
        text += track.as_export_text() + "\n"
    return text


def export_as_m3u(playlist_name: str, tracks: list) -> str:
    # TODO
    raise ValueError


def tracks_matching_criteria(playlist_id: int, criteria: dict) -> list:
    try:
        playlist = Playlist.objects.get(playlist_id=playlist_id)
    except ObjectDoesNotExist:
        raise ValueError
    tracks = PlaylistTrack.objects.filter(playlist=playlist).values_list(
        "track", flat=True
    )
    query = Q(track_id__in=tracks)
    if "excluded_genres" in criteria:
        for genre in criteria["excluded_genres"]:
            query &= ~Q(genres__icontains=genre)
    if "excluded_artists" in criteria:
        for artist in criteria["excluded_artists"]:
            query &= ~Q(artist=artist)
    if "excluded_albums" in criteria:
        for album in criteria["excluded_albums"]:
            query &= ~Q(album=album)
    if "explicit" in criteria and not criteria["explicit"]:
        query &= Q(explicit=False)
    return Track.objects.filter(query)
