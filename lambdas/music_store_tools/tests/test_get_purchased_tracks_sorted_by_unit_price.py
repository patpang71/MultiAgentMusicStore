import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_purchased_tracks_sorted_by_unit_price import get_purchased_tracks_sorted_by_unit_price

SAMPLE_ROW = {
    "trackId":   1,
    "trackName": "For Those About To Rock (We Salute You)",
    "artist":    "AC/DC",
    "album":     "For Those About To Rock We Salute You",
    "unitPrice": 0.99,
}


class TestGetPurchasedTracksSortedByUnitPrice(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_purchased_tracks_sorted_by_unit_price.get_connection")
    def test_found_tracks(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = get_purchased_tracks_sorted_by_unit_price()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        track = result[0]
        self.assertEqual(track["trackId"], "1")
        self.assertEqual(track["trackName"], "For Those About To Rock (We Salute You)")
        self.assertEqual(track["artist"], "AC/DC")
        self.assertEqual(track["unitPrice"], "0.99")

    @patch("get_purchased_tracks_sorted_by_unit_price.get_connection")
    def test_no_tracks_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = get_purchased_tracks_sorted_by_unit_price()

        self.assertEqual(result, {"message": "Cannot find any purchased tracks"})

    @patch("get_purchased_tracks_sorted_by_unit_price.get_connection")
    def test_input_ignored(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = get_purchased_tracks_sorted_by_unit_price("ignored_value")

        self.assertIsInstance(result, list)

    @patch("get_purchased_tracks_sorted_by_unit_price.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("DB unavailable")

        result = get_purchased_tracks_sorted_by_unit_price()

        self.assertIn("Error", result["message"])
        self.assertIn("DB unavailable", result["message"])


if __name__ == "__main__":
    unittest.main()
