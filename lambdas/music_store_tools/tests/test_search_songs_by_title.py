import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search_songs_by_title import search_songs_by_title

SAMPLE_ROW = {
    "trackName": "For Those About To Rock (We Salute You)",
    "albumTitle": "For Those About To Rock We Salute You",
    "artist": "AC/DC",
    "genre": "Rock",
    "mediaType": "MPEG audio file",
    "composer": "Angus Young, Malcolm Young, Brian Johnson",
    "milliseconds": 343719,
    "bytes": 11170334,
    "unitPrice": 0.99,
}


class TestSearchSongsByTitle(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("search_songs_by_title.get_connection")
    def test_found_songs(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = search_songs_by_title("Rock")

        self.assertEqual(result["trackInput"], "Rock")
        self.assertEqual(len(result["tracks"]), 1)
        self.assertEqual(result["tracks"][0]["trackName"], "For Those About To Rock (We Salute You)")

    @patch("search_songs_by_title.get_connection")
    def test_title_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = search_songs_by_title("xyznotexist")

        self.assertEqual(result, {"message": "Cannot find any song from title xyznotexist"})

    @patch("search_songs_by_title.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Query failed")

        result = search_songs_by_title("Rock")

        self.assertIn("Error", result["message"])
        self.assertIn("Query failed", result["message"])


if __name__ == "__main__":
    unittest.main()
