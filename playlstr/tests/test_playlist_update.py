from django.test import TestCase

from playlstr.util.playlist import *


# https://stackoverflow.com/a/51423725
def dict_to_querydict(dictionary):
    from django.http import QueryDict
    from django.utils.datastructures import MultiValueDict

    qdict = QueryDict('', mutable=True)

    for key, value in dictionary.items():
        d = {key: value}
        qdict.update(MultiValueDict(d) if isinstance(value, list) else d)

    return qdict


class PlaylistUpdateTestCase(TestCase):
    def setUp(self):
        self.playlist = Playlist.objects.create()
        self.track1 = Track.objects.create(title='1')
        self.track1.save()
        self.track2 = Track.objects.create(title='2')
        self.track2.save()
        self.track3 = Track.objects.create(title='3')
        self.track3.save()

    def test_invalid_playlist(self):
        data = dict_to_querydict({})
        self.assertEqual(update_playlist(data), 'invalid playlist')

    def test_invalid_access_token_returns_error(self):
        data = dict_to_querydict({'playlist': self.playlist.playlist_id, 'token': 'asdf', 'spotify_new': '[1, 2]'})
        self.assertEqual(update_playlist(data), 'invalid token', 'Invalid token returns error')

    def test_invalid_access_token_doesnt_change_db(self):
        # TODO
        pass

    def test_add_tracks(self):
        data = dict_to_querydict({'playlist': self.playlist.playlist_id,
                                  'added': '[{}, {}]'.format(self.track1.track_id, self.track2.track_id)})
        self.assertEqual('success', update_playlist(data), 'No error adding tracks')
        ptracks = PlaylistTrack.objects.filter(playlist=self.playlist).all()
        tracks = [t.track for t in ptracks]
        self.assertTrue(self.track1 in tracks, 'Add track')
        self.assertTrue(self.track2 in tracks, 'Add 2nd track')
        self.assertTrue(len(tracks) == 2)
        self.assertFalse(self.track3 in tracks, 'Don\'t add extra tracks')

    def test_delete_tracks(self):
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.track1, index=0)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.track2, index=1)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.track3, index=2)
        data = dict_to_querydict({'playlist': self.playlist.playlist_id,
                                  'removed': '[{}, {}]'.format(self.track1.track_id, self.track2.track_id)})
        self.assertEqual('success', update_playlist(data), 'No error deleting tracks')
        ptracks = PlaylistTrack.objects.filter(playlist=self.playlist).all()
        tracks = [t.track for t in ptracks]
        self.assertFalse(self.track1 in tracks, 'Delete track')
        self.assertFalse(self.track2 in tracks, 'Delete 2nd track')
        self.assertTrue(self.track3 in tracks, 'Don\'t delete extra tracks')
