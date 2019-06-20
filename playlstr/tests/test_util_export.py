from django.test import TestCase

from playlstr.util.export import *


class TracksMatchingCriteriaTestCase(TestCase):
    def setUp(self):
        Track.objects.all().delete()
        PlaylistTrack.objects.all().delete()
        Playlist.objects.all().delete()
        self.g1 = Track.objects.create(title='g1', genres=['g1'], explicit=False, artist='a1', album='a1')
        self.g1g2 = Track.objects.create(title='g1g2', genres=['g1', 'g2'], explicit=False, artist='a12', album='a12')
        self.g2 = Track.objects.create(title='g2', genres=['g2'], artist='a2', album='a2')
        self.g1_explicit = Track.objects.create(title='g1 explicit', genres=['g1'], explicit=True, artist='a1',
                                                album='a1')
        self.g1g2_explicit = Track.objects.create(title='g1g2 explicit', genres=['g1', 'g2'], explicit=True,
                                                  artist='a12', album='a12')
        self.g2_explicit = Track.objects.create(title='g2 explicit', genres=['g2'], explicit=True, artist='a2',
                                                album='a2')
        self.g3 = Track.objects.create(title='g3', genres=['g3'], artist='a3', album='a3')
        self.playlist = Playlist.objects.create()
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g1, index=0)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g1_explicit, index=1)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g2, index=2)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g2_explicit, index=3)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g1g2, index=4)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g1g2_explicit, index=5)
        PlaylistTrack.objects.create(playlist=self.playlist, track=self.g3, index=6)

    def test_explicit_criteria(self):
        # Test for explicit = False
        result = tracks_matching_criteria(self.playlist.playlist_id, {'explicit': False})
        expected = {self.g1, self.g2, self.g1g2, self.g3}
        self.assertEqual(set(result), expected, 'Include all tracks matching criteria when explicit is False')
        self.assertNotIn(self.g1_explicit, result, 'Don\'t return explicit tracks if not explicit')
        self.assertNotIn(self.g2_explicit, result, 'Don\'t return explicit tracks if not explicit')
        self.assertNotIn(self.g1g2_explicit, result, 'Don\'t return explicit tracks if not explicit')
        # Test for explicit = True
        result = tracks_matching_criteria(self.playlist.playlist_id, {'explicit': True})
        expected = {self.g1, self.g2, self.g1g2, self.g1_explicit, self.g2_explicit, self.g1g2_explicit, self.g3}
        self.assertEqual(set(result), expected, 'Include all tracks matching criteria when explicit is True')

    def test_genre_exclusion_criteria(self):
        result = tracks_matching_criteria(self.playlist.playlist_id, {'excluded_genres': ['g1']})
        expected = {self.g2, self.g3, self.g2_explicit}
        self.assertEqual(set(result), expected, 'Include all tracks matching criteria')
        self.assertNotIn(self.g1g2, result, 'Don\'t include multi-genre tracks matching excluded genres')
        self.assertNotIn(self.g1g2_explicit, result, 'Don\'t include multi-genre tracks matching excluded genres')
        self.assertNotIn(self.g1, result, 'Exclude tracks with excluded genre')
        self.assertNotIn(self.g1_explicit, result, 'Exclude tracks with excluded genre')
        result = tracks_matching_criteria(self.playlist.playlist_id, {'excluded_genres': ['g2', 'g3']})
        expected = {self.g1, self.g1_explicit}
        self.assertEqual(set(result), expected, 'Include all tracks matching criteria')
        self.assertNotIn(self.g1g2, result, 'Don\'t include multi-genre tracks matching excluded genres')
        self.assertNotIn(self.g1g2_explicit, result, 'Don\'t include multi-genre tracks matching excluded genres')
        self.assertNotIn(self.g2, result, 'Exclude tracks with excluded genre')
        self.assertNotIn(self.g2_explicit, result, 'Exclude tracks with excluded genre')
        self.assertNotIn(self.g3, result, 'Exclude tracks with excluded genre')

    def test_artist_exclusion_criteria(self):
        result = tracks_matching_criteria(self.playlist.playlist_id, {'excluded_artists': ['a1', 'a12']})
        expected = {self.g2, self.g2_explicit, self.g3}
        self.assertEqual(set(result), expected, 'Include tracks whose artist isn\'t excluded')
        self.assertNotIn(self.g1, result, 'Exclude tracks whose artist is excluded')
        self.assertNotIn(self.g1_explicit, result, 'Exclude tracks whose artist is excluded')
        self.assertNotIn(self.g1g2, result, 'Exclude tracks whose artist is excluded')
        self.assertNotIn(self.g1g2_explicit, result, 'Exclude tracks whose artist is excluded')

    def test_album_exclusion_criteria(self):
        result = tracks_matching_criteria(self.playlist.playlist_id, {'excluded_albums': ['a1', 'a2']})
        expected = {self.g1g2, self.g1g2_explicit, self.g3}
        self.assertEqual(set(result), expected, 'Include tracks whose album isn\'t excluded')
        self.assertNotIn(self.g1, result, 'Exclude tracks whose album is excluded')
        self.assertNotIn(self.g2, result, 'Exclude tracks whose album is excluded')
        self.assertNotIn(self.g1_explicit, result, 'Exclude tracks whose album is excluded')
        self.assertNotIn(self.g2_explicit, result, 'Exclude tracks whose album is excluded')
