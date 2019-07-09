from .playlist import *
from django.core.exceptions import ObjectDoesNotExist


def export_as_text(playlist_name: str, tracks: list) -> str:
    text = playlist_name + '\n\n'
    for track in Track.objects.filter(track_id__in=tracks):
        text += track.as_export_text() + '\n'
    return text


def export_as_m3u(playlist_name: str, tracks: list) -> str:
    # TODO
    raise ValueError


def export_spotify(playlist_id: int, user_id: int, **info) -> str:
    """
    Create playlist playlist_id on Spotify as user user_id

    pre: user_id is a valid user who has linked their Spotify
    :param playlist_id: id of playlist being exported
    :param user_id: internal id of the user who will create the playlist on spotify
    :return: url of created playlist or error message beginning with 'Error' on error
    """
    info['playlist_id'] = playlist_id
    info['user_id'] = user_id
    try:
        spotify_id = spotify_create_playlist(info)
        copy_tracks_to_spotify(PlaylistTrack.objects.filter(playlist__playlist_id=playlist_id).all(), spotify_id,
                               user_id)
        return 'http://open.spotify.com/playlist/{}'.format(spotify_id)
    except ValueError as e:
        return 'Error {}'.format(str(e))


def tracks_matching_criteria(playlist_id: int, criteria: dict) -> list:
    try:
        playlist = Playlist.objects.get(playlist_id=playlist_id)
    except ObjectDoesNotExist:
        raise ValueError
    tracks = PlaylistTrack.objects.filter(playlist=playlist).values_list('track', flat=True)
    query = Q(track_id__in=tracks)
    if 'excluded_genres' in criteria:
        for genre in criteria['excluded_genres']:
            query &= ~Q(genres__icontains=genre)
    if 'excluded_artists' in criteria:
        for artist in criteria['excluded_artists']:
            query &= ~Q(artist=artist)
    if 'excluded_albums' in criteria:
        for album in criteria['excluded_albums']:
            query &= ~Q(album=album)
    if 'explicit' in criteria and not criteria['explicit']:
        query &= Q(explicit=False)
    return Track.objects.filter(query)
