import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ALBUMS = [{"album": "Back in Black", "artist": "AC/DC"}]
TRACKS = [{"trackId": 1, "name": "Thunderstruck", "genre": "Rock"}]
TRACK = {"trackId": 1, "name": "Thunderstruck", "album": "The Razors Edge", "unitPrice": 0.99}


def _make_lambda_response(payload: dict):
    mock = MagicMock()
    mock["Payload"].read.return_value = json.dumps(payload).encode()
    return mock


class TestMusicCatalogTools(unittest.TestCase):

    @patch("tools.music_catalog_tools.boto3")
    def test_get_songs_by_genre_returns_results(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(TRACKS)
        from tools.music_catalog_tools import get_songs_by_genre
        result = json.loads(get_songs_by_genre.invoke({"genre": "Rock"}))
        self.assertEqual(result, TRACKS)

    @patch("tools.music_catalog_tools.boto3")
    def test_get_track_details_by_id(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(TRACK)
        from tools.music_catalog_tools import get_track_details_by_id
        result = json.loads(get_track_details_by_id.invoke({"track_id": 1}))
        self.assertEqual(result["trackId"], 1)

    @patch("tools.music_catalog_tools.boto3")
    def test_get_albums_by_artist(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(ALBUMS)
        from tools.music_catalog_tools import get_albums_by_artist
        result = json.loads(get_albums_by_artist.invoke({"artist_name": "AC/DC"}))
        self.assertEqual(result[0]["artist"], "AC/DC")

    @patch("tools.music_catalog_tools.boto3")
    def test_search_tracks_by_artist(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(TRACKS)
        from tools.music_catalog_tools import search_tracks_by_artist
        result = json.loads(search_tracks_by_artist.invoke({"artist_name": "AC/DC"}))
        self.assertIsInstance(result, list)

    @patch("tools.music_catalog_tools.boto3")
    def test_search_songs_by_title(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(TRACKS)
        from tools.music_catalog_tools import search_songs_by_title
        result = json.loads(search_songs_by_title.invoke({"title": "Thunder"}))
        self.assertIsInstance(result, list)

    @patch("tools.music_catalog_tools.boto3")
    def test_correct_tool_name_and_input_sent_to_lambda(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(ALBUMS)
        from tools.music_catalog_tools import get_albums_by_artist

        get_albums_by_artist.invoke({"artist_name": "AC/DC"})

        payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(payload["tool"], "get_albums_by_artist")
        self.assertEqual(payload["input"], "AC/DC")

    @patch("tools.music_catalog_tools.boto3")
    def test_get_songs_by_genre_sends_correct_tool_name(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(TRACKS)
        from tools.music_catalog_tools import get_songs_by_genre

        get_songs_by_genre.invoke({"genre": "Jazz"})

        payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(payload["tool"], "get_songs_by_genre")
        self.assertEqual(payload["input"], "Jazz")


if __name__ == "__main__":
    unittest.main()
