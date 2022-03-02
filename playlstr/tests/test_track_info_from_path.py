import playlstr.util.track as util
from django.test import TestCase
import re


class TrackInfoFromPathTestCase(TestCase):
    """
    Test cases for guessing track information from filename
    """

    TEST_TRACK_NAME = "Test Track"
    TEST_TRACK_EXTENSION = "flac"
    TEST_TRACK_NUMBER = "01"
    TEST_TRACK_ARTIST = "Test Artist"
    TEST_TRACK_ALBUM = "Test Album"
    TEST_TRACK_YEAR = 1981

    def test_single_file(self):
        result = util.guess_info_from_path(
            "{} - {}.FLAC".format(self.TEST_TRACK_ARTIST, self.TEST_TRACK_NAME)
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )

    def test_dir_artist_hyphen_album(self):
        result = util.guess_info_from_path(
            "{} - {}/{} - {}.FLAC".format(
                self.TEST_TRACK_ARTIST,
                self.TEST_TRACK_ALBUM,
                self.TEST_TRACK_NUMBER,
                self.TEST_TRACK_NAME,
            )
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )
        self.assertEqual(result["album"], self.TEST_TRACK_ALBUM, "Correct album")
        self.assertEqual(
            result["track_number"], self.TEST_TRACK_NUMBER, "Correct track number"
        )

    def test_nested_dir_artist_hyphen_album(self):
        result = util.guess_info_from_path(
            "/test/dir/{} - {}/{} - {}.FLAC".format(
                self.TEST_TRACK_ARTIST,
                self.TEST_TRACK_ALBUM,
                self.TEST_TRACK_NUMBER,
                self.TEST_TRACK_NAME,
            )
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )
        self.assertEqual(result["album"], self.TEST_TRACK_ALBUM, "Correct album")
        self.assertEqual(
            result["track_number"], self.TEST_TRACK_NUMBER, "Correct track number"
        )

    def test_dir_artist_hyphen_album_parenth_year(self):
        result = util.guess_info_from_path(
            "{} - {} ({})/{} - {}.FLAC".format(
                self.TEST_TRACK_ARTIST,
                self.TEST_TRACK_ALBUM,
                self.TEST_TRACK_YEAR,
                self.TEST_TRACK_NUMBER,
                self.TEST_TRACK_NAME,
            )
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )
        self.assertEqual(result["album"], self.TEST_TRACK_ALBUM, "Correct album")
        self.assertEqual(
            result["track_number"], self.TEST_TRACK_NUMBER, "Correct track number"
        )
        self.assertEqual(result["year"], self.TEST_TRACK_YEAR, "Correct year")

    def test_dir_artist_hyphen_album_curly_year(self):
        result = util.guess_info_from_path(
            "{} - {} {{{}}}/{} - {}.FLAC".format(
                self.TEST_TRACK_ARTIST,
                self.TEST_TRACK_ALBUM,
                self.TEST_TRACK_YEAR,
                self.TEST_TRACK_NUMBER,
                self.TEST_TRACK_NAME,
            )
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )
        self.assertEqual(result["album"], self.TEST_TRACK_ALBUM, "Correct album")
        self.assertEqual(
            result["track_number"], self.TEST_TRACK_NUMBER, "Correct track number"
        )
        self.assertEqual(result["year"], self.TEST_TRACK_YEAR, "Correct year")

    def test_dir_year_hyphen_artist_hyphen_album(self):
        result = util.guess_info_from_path(
            "{} - {} - {}/{} - {}.FLAC".format(
                self.TEST_TRACK_YEAR,
                self.TEST_TRACK_ARTIST,
                self.TEST_TRACK_ALBUM,
                self.TEST_TRACK_NUMBER,
                self.TEST_TRACK_NAME,
            )
        )
        self.assertEqual(result["title"], self.TEST_TRACK_NAME, "Correct title")
        self.assertEqual(result["artist"], self.TEST_TRACK_ARTIST, "Correct artist")
        self.assertEqual(
            result["source"], self.TEST_TRACK_EXTENSION.lower(), "Correct source"
        )
        self.assertEqual(result["album"], self.TEST_TRACK_ALBUM, "Correct album")
        self.assertEqual(
            result["track_number"], self.TEST_TRACK_NUMBER, "Correct track number"
        )
        self.assertEqual(result["year"], self.TEST_TRACK_YEAR, "Correct year")
