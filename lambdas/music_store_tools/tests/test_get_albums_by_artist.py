import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_albums_by_artist import get_albums_by_artist


class TestGetAlbumsByArtist(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_albums_by_artist.get_connection")
    def test_found_single_artist(self, mock_get_conn):
        rows = [
            {"artist": "Alanis Morissette", "album": "Jagged Little Pill"},
            {"artist": "Alice In Chains", "album": "Facelift"},
        ]
        mock_get_conn.return_value = self._make_conn(rows)

        result = get_albums_by_artist("Al")

        self.assertEqual(result["artistNameInput"], "Al")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["results"][0]["artist"], "Alanis Morissette")
        self.assertEqual(result["results"][0]["albums"], ["Jagged Little Pill"])
        self.assertEqual(result["results"][1]["artist"], "Alice In Chains")
        self.assertEqual(result["results"][1]["albums"], ["Facelift"])

    @patch("get_albums_by_artist.get_connection")
    def test_artist_with_multiple_albums(self, mock_get_conn):
        rows = [
            {"artist": "AC/DC", "album": "For Those About To Rock We Salute You"},
            {"artist": "AC/DC", "album": "Let There Be Rock"},
        ]
        mock_get_conn.return_value = self._make_conn(rows)

        result = get_albums_by_artist("AC/DC")

        self.assertEqual(result["artistNameInput"], "AC/DC")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(len(result["results"][0]["albums"]), 2)

    @patch("get_albums_by_artist.get_connection")
    def test_no_artist_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = get_albums_by_artist("zzz_unknown")

        self.assertEqual(result, {"message": "Cannot find any artists"})

    @patch("get_albums_by_artist.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection refused")

        result = get_albums_by_artist("AC/DC")

        self.assertIn("Error", result["message"])
        self.assertIn("Connection refused", result["message"])


if __name__ == "__main__":
    unittest.main()
