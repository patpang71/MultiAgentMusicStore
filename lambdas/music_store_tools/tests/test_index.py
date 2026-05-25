import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import index


class TestHandler(unittest.TestCase):

    @patch("index.get_albums_by_artist")
    def test_routes_get_albums_by_artist(self, mock_tool):
        mock_tool.return_value = {"artistNameInput": "AC/DC", "results": []}
        event = {"tool": "get_albums_by_artist", "input": "AC/DC"}

        result = index.handler(event, None)

        mock_tool.assert_called_once_with("AC/DC")
        self.assertEqual(result["artistNameInput"], "AC/DC")

    @patch("index.search_tracks_by_artist")
    def test_routes_search_tracks_by_artist(self, mock_tool):
        mock_tool.return_value = {"artist": "AC/DC", "tracks": []}
        event = {"tool": "search_tracks_by_artist", "input": "AC/DC"}

        result = index.handler(event, None)

        mock_tool.assert_called_once_with("AC/DC")

    @patch("index.get_songs_by_genre")
    def test_routes_get_songs_by_genre(self, mock_tool):
        mock_tool.return_value = {"genre": "Rock", "tracks": []}
        event = {"tool": "get_songs_by_genre", "input": "Rock"}

        result = index.handler(event, None)

        mock_tool.assert_called_once_with("Rock")

    @patch("index.search_songs_by_title")
    def test_routes_search_songs_by_title(self, mock_tool):
        mock_tool.return_value = {"trackInput": "Rock", "tracks": []}
        event = {"tool": "search_songs_by_title", "input": "Rock"}

        result = index.handler(event, None)

        mock_tool.assert_called_once_with("Rock")

    @patch("index.get_track_details_by_id")
    def test_routes_get_track_details_by_id(self, mock_tool):
        mock_tool.return_value = {"trackName": "Some Track"}
        event = {"tool": "get_track_details_by_id", "input": 1}

        result = index.handler(event, None)

        mock_tool.assert_called_once_with(1)

    def test_missing_tool_field(self):
        result = index.handler({"input": "AC/DC"}, None)
        self.assertIn("missing required field: tool", result["message"])

    def test_unknown_tool(self):
        result = index.handler({"tool": "nonexistent_tool", "input": "x"}, None)
        self.assertIn("unknown tool", result["message"])

    def test_missing_input_field(self):
        result = index.handler({"tool": "get_albums_by_artist"}, None)
        self.assertIn("missing required field: input", result["message"])


if __name__ == "__main__":
    unittest.main()
