import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search_tracks_by_artist import search_tracks_by_artist

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


class TestSearchTracksByArtist(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("search_tracks_by_artist.get_connection")
    def test_found_tracks(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = search_tracks_by_artist("AC/DC")

        self.assertEqual(result["artist"], "AC/DC")
        self.assertEqual(len(result["tracks"]), 1)
        track = result["tracks"][0]
        self.assertEqual(track["trackName"], "For Those About To Rock (We Salute You)")
        self.assertEqual(track["milliseconds"], "343719")
        self.assertEqual(track["bytes"], "11170334")
        self.assertEqual(track["unitPrice"], "0.99")

    @patch("search_tracks_by_artist.get_connection")
    def test_artist_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = search_tracks_by_artist("Unknown Artist")

        self.assertEqual(result, {"message": "Cannot find any artist"})

    @patch("search_tracks_by_artist.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("DB unavailable")

        result = search_tracks_by_artist("AC/DC")

        self.assertIn("Error", result["message"])
        self.assertIn("DB unavailable", result["message"])


if __name__ == "__main__":
    unittest.main()
