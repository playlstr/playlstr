from django.test import TestCase
from ..playlist_import import *

from ..apikeys import *


class SpotifyImportBasicTestCase(TestCase):
    def test_invalid_access_token(self):
        result = import_spotify({'playlist_url': SPOTIFY_TEST_PLAYLIST_PUBLIC_URL, 'access_token': 'token'})
        self.assertEqual(result, 'Unauthorized')

    def test_malformed_playlist_url(self):
        result = import_spotify({'playlist_url': 'playlist', 'access_token': VALID_SPOTIFY_ACCESS_TOKEN})
        self.assertEqual(result, 'Invalid URL')

    '''
    It seems the API returns a valid playlist object even if you don't have permission to view the playlist
    TODO verify this and fix/remove this test case
    def test_missing_permission_playlist(self):
        """Importing a playlist which you don't have permissions for should give Unauthorized"""
        result = import_spotify(
            {'playlist_url': SPOTIFY_TEST_PLAYLIST_NO_PERMISSION, 'access_token': VALID_SPOTIFY_ACCESS_TOKEN})
        self.assertEqual(result, 'Unauthorized')
    '''


class SpotifyImportPublicTestCase(TestCase):
    def setUp(self):
        # Imported playlist's id
        self.pid = import_spotify(
            {'playlist_url': SPOTIFY_TEST_PLAYLIST_PUBLIC_URL, 'access_token': VALID_SPOTIFY_ACCESS_TOKEN})
        self.assertIsInstance(self.pid, int, 'Created valid playlist id')
        self.assertGreaterEqual(self.pid, 0, 'Created valid playlist id')
        self.playlist = Playlist.objects.get(playlist_id=self.pid)
        self.assertIsInstance(self.playlist, Playlist, "Only one playlist with playlist ID")

    def test_import_creates_playlist(self):
        self.assertTrue(Playlist.objects.filter(playlist_id=self.pid).exists())

    def test_import_correct_playlist_metadata(self):
        """Import correct playlist ID and name"""
        playlist = self.playlist
        self.assertEqual(playlist.spotify_id, SPOTIFY_TEST_PLAYLIST_PUBLIC_ID, 'Import correct spotify ID')
        self.assertEqual(playlist.name, SPOTIFY_TEST_PLAYLIST_PUBLIC_NAME, 'Import correct playlist name')

    def test_import_creates_first_page_tracks(self):
        """Create tracks 0-100 of the playlist in the database (1st api call)"""
        playlist = Playlist.objects.get(playlist_id=self.pid)

    def test_import_creates_all_tracks(self):
        """Create all tracks in the database (requires more than 1 api call for 101+ tracks"""
        pass

    def test_import_doesnt_duplicate_tracks(self):
        """If an imported track is already in the database use that"""
        pass

    def test_import_updates_track_spotify_ids(self):
        """If an imported track is already in the database without a Spotify ID update the track's Spotify ID"""
        pass

