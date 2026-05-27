import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.messages import HumanMessage, AIMessage

ALBUMS = [{"album": "Back in Black", "artist": "AC/DC"}]
CUSTOMER_ROW = {"customerId": "2", "firstName": "Leonie"}


def _base_state():
    return {
        "messages": [HumanMessage(content="Show me AC/DC albums")],
        "customer_info": CUSTOMER_ROW,
        "verified": True,
        "preferences": {"genres": [], "artists": []},
        "next_agent": "music",
    }


def _make_tool_call(name, args, call_id="call_abc"):
    msg = MagicMock(spec=AIMessage)
    msg.type = "ai"
    msg.content = ""
    msg.tool_calls = [{"name": name, "args": args, "id": call_id}]
    return msg


def _make_plain(content):
    msg = MagicMock(spec=AIMessage)
    msg.type = "ai"
    msg.content = content
    msg.tool_calls = []
    return msg


class TestMusicAgentNode(unittest.TestCase):

    @patch("nodes.music_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.music_agent_node.ChatOpenAI")
    @patch("nodes.music_agent_node.MUSIC_TOOL_MAP")
    def test_calls_tool_and_returns_answer(self, mock_tool_map, mock_llm_cls, _):
        tool_call = _make_tool_call("get_albums_by_artist", {"artist_name": "AC/DC"})
        final = _make_plain("AC/DC has these albums: Back in Black, Highway to Hell.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_call, final]
        mock_llm_cls.return_value = mock_llm

        mock_fn = MagicMock()
        mock_fn.invoke.return_value = json.dumps(ALBUMS)
        mock_tool_map.get.return_value = mock_fn

        from nodes.music_agent_node import music_agent_node
        result = music_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")
        self.assertGreater(len(result["messages"]), 0)
        mock_fn.invoke.assert_called_once_with({"artist_name": "AC/DC"})

    @patch("nodes.music_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.music_agent_node.ChatOpenAI")
    def test_no_tool_call_still_sets_answered(self, mock_llm_cls, _):
        final = _make_plain("We don't have that artist in our catalog.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = final
        mock_llm_cls.return_value = mock_llm

        from nodes.music_agent_node import music_agent_node
        result = music_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")
        self.assertEqual(len(result["messages"]), 1)

    @patch("nodes.music_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.music_agent_node.ChatOpenAI")
    @patch("nodes.music_agent_node.MUSIC_TOOL_MAP")
    def test_unknown_tool_returns_error_json(self, mock_tool_map, mock_llm_cls, _):
        tool_call = _make_tool_call("nonexistent_tool", {})
        final = _make_plain("Sorry, I couldn't help with that.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_call, final]
        mock_llm_cls.return_value = mock_llm
        mock_tool_map.get.return_value = None  # unknown tool

        from nodes.music_agent_node import music_agent_node
        result = music_agent_node(_base_state())

        # Should still complete without raising
        self.assertEqual(result["next_agent"], "answered")

    @patch("nodes.music_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.music_agent_node.ChatOpenAI")
    @patch("nodes.music_agent_node.MUSIC_TOOL_MAP")
    def test_multiple_tool_calls_in_sequence(self, mock_tool_map, mock_llm_cls, _):
        call1 = _make_tool_call("search_tracks_by_artist", {"artist_name": "AC/DC"}, "c1")
        call2 = _make_tool_call("get_track_details_by_id", {"track_id": 1}, "c2")
        final = _make_plain("Here are the details for that track.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [call1, call2, final]
        mock_llm_cls.return_value = mock_llm

        mock_fn = MagicMock()
        mock_fn.invoke.return_value = json.dumps({"track": "Thunderstruck"})
        mock_tool_map.get.return_value = mock_fn

        from nodes.music_agent_node import music_agent_node
        result = music_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")
        self.assertEqual(mock_llm.bind_tools.return_value.invoke.call_count, 3)


if __name__ == "__main__":
    unittest.main()
