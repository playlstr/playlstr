from django.test import TestCase
from ..playlist_utils import *


class PlaylistUpdateTestCase(TestCase):
    def setUp(self):
        self.playlist = Playlist.objects.create()

    def test_add_tracks(self):
        # TODO
        pass

    def test_delete_tracks(self):
        # TODO
        pass

    def test_no_change(self):
        # TODO
        pass
