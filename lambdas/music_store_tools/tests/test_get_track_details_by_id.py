import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_track_details_by_id import get_track_details_by_id

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


class TestGetTrackDetailsById(unittest.TestCase):

    def _make_conn(self, row):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.return_value = row
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_track_details_by_id.get_connection")
    def test_found_track(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_track_details_by_id(1)

        self.assertEqual(result["trackName"], "For Those About To Rock (We Salute You)")
        self.assertEqual(result["artist"], "AC/DC")
        self.assertEqual(result["milliseconds"], "343719")
        self.assertEqual(result["bytes"], "11170334")
        self.assertEqual(result["unitPrice"], "0.99")

    @patch("get_track_details_by_id.get_connection")
    def test_track_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(None)

        result = get_track_details_by_id(99999)

        self.assertEqual(result, {"message": "Cannot find any song from track Id 99999"})

    @patch("get_track_details_by_id.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("DB connection lost")

        result = get_track_details_by_id(1)

        self.assertIn("Error", result["message"])
        self.assertIn("DB connection lost", result["message"])


if __name__ == "__main__":
    unittest.main()
