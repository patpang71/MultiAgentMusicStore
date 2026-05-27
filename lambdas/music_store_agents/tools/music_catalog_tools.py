import json
import os

import boto3
from langchain_core.tools import tool


def _function_name() -> str:
    return os.environ.get("MUSIC_STORE_TOOLS_FUNCTION_NAME", "music-store-tools")


def _invoke_tool(tool_name: str, input_value=None):
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=_function_name(),
        InvocationType="RequestResponse",
        Payload=json.dumps({"tool": tool_name, "input": input_value}),
    )
    return json.loads(response["Payload"].read())


@tool
def get_songs_by_genre(genre: str) -> str:
    """Retrieve songs from the catalog filtered by genre name (e.g. 'Rock', 'Jazz')."""
    return json.dumps(_invoke_tool("get_songs_by_genre", genre))


@tool
def get_track_details_by_id(track_id: int) -> str:
    """Get full details of a single track by its numeric TrackId."""
    return json.dumps(_invoke_tool("get_track_details_by_id", track_id))


@tool
def get_albums_by_artist(artist_name: str) -> str:
    """Get all albums for an artist. Supports partial name matching."""
    return json.dumps(_invoke_tool("get_albums_by_artist", artist_name))


@tool
def search_tracks_by_artist(artist_name: str) -> str:
    """Search for tracks by artist name (exact match, up to 20 results)."""
    return json.dumps(_invoke_tool("search_tracks_by_artist", artist_name))


@tool
def search_songs_by_title(title: str) -> str:
    """Search for songs by title using partial matching (up to 10 results)."""
    return json.dumps(_invoke_tool("search_songs_by_title", title))


MUSIC_TOOLS = [
    get_songs_by_genre,
    get_track_details_by_id,
    get_albums_by_artist,
    search_tracks_by_artist,
    search_songs_by_title,
]
MUSIC_TOOL_MAP = {t.name: t for t in MUSIC_TOOLS}
