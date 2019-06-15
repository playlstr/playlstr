from .playlist import *


def export_playlist_text(playlist_id: int) -> str:
    try:
        playlist = Playlist.objects.get(playlist_id=playlist_id)
    except ObjectDoesNotExist:
        return 'invalid'
    tracks = PlaylistTrack.objects.filter(playlist=playlist).values_list('track', flat=True)
    text = ''
    for track in Track.objects.filter(track_id__in=tracks):
        text += track.as_export_text() + '\n'
    print(text)
    return text
