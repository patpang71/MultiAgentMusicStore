import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_songs_by_genre import get_songs_by_genre

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


class TestGetSongsByGenre(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_songs_by_genre.get_connection")
    def test_found_songs(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = get_songs_by_genre("Rock")

        self.assertEqual(result["genre"], "Rock")
        self.assertEqual(len(result["tracks"]), 1)
        track = result["tracks"][0]
        self.assertEqual(track["genre"], "Rock")
        self.assertEqual(track["milliseconds"], "343719")

    @patch("get_songs_by_genre.get_connection")
    def test_genre_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = get_songs_by_genre("UnknownGenre")

        self.assertEqual(result, {"message": "Cannot find any genre"})

    @patch("get_songs_by_genre.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Timeout")

        result = get_songs_by_genre("Rock")

        self.assertIn("Error", result["message"])
        self.assertIn("Timeout", result["message"])


if __name__ == "__main__":
    unittest.main()
