import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.messages import HumanMessage, AIMessage

CUSTOMER_ROW = {
    "customerId": "2", "firstName": "Leonie", "lastName": "Köhler",
    "email": "leonekohler@surfeu.de",
}
EMPTY_PREFS = {"genres": [], "artists": []}


def _base_state(next_agent="", prefs=None):
    return {
        "messages": [HumanMessage(content="Hello")],
        "customer_info": CUSTOMER_ROW,
        "verified": True,
        "preferences": prefs,
        "next_agent": next_agent,
    }


def _make_decision(response="OK", route=None, genres=None, artists=None):
    from nodes.supervisor_node import SupervisorDecision
    return SupervisorDecision(
        response=response,
        route=route,
        liked_genres=genres or [],
        liked_artists=artists or [],
    )


class TestSupervisorNode(unittest.TestCase):

    def test_answered_shortcut_skips_llm_and_returns_what_else(self):
        """When next_agent=='answered', no LLM call is made — just ask 'What else?'"""
        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state(next_agent="answered", prefs=EMPTY_PREFS))
        self.assertEqual(result["next_agent"], "")
        self.assertIn("anything else", result["messages"][0].content.lower())

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value=EMPTY_PREFS)
    @patch("nodes.supervisor_node.save_preferences")
    def test_routes_to_music(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision(
            response="Let me check the catalog!", route="music"
        )
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state())

        self.assertEqual(result["next_agent"], "music")
        mock_save.assert_not_called()

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value=EMPTY_PREFS)
    @patch("nodes.supervisor_node.save_preferences")
    def test_routes_to_invoice(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision(
            response="Let me check your invoices!", route="invoice"
        )
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state())

        self.assertEqual(result["next_agent"], "invoice")

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value=EMPTY_PREFS)
    @patch("nodes.supervisor_node.save_preferences")
    def test_no_route_shows_menu(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision(
            response="Welcome! How can I help?", route=None
        )
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state())

        self.assertEqual(result["next_agent"], "")

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value=EMPTY_PREFS)
    @patch("nodes.supervisor_node.save_preferences")
    def test_detected_genres_and_artists_are_saved(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision(
            response="Great, you love jazz and AC/DC!",
            route="music",
            genres=["jazz"],
            artists=["AC/DC"],
        )
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state())

        mock_save.assert_called_once()
        saved = mock_save.call_args[0][1]
        self.assertIn("jazz", saved["genres"])
        self.assertIn("AC/DC", saved["artists"])
        self.assertIn("jazz", result["preferences"]["genres"])

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value={"genres": ["rock"], "artists": []})
    @patch("nodes.supervisor_node.save_preferences")
    def test_new_preferences_merged_with_existing(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision(
            response="Sure!", route="music", genres=["jazz"]
        )
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        result = supervisor_node(_base_state())

        saved = mock_save.call_args[0][1]
        self.assertIn("rock", saved["genres"])
        self.assertIn("jazz", saved["genres"])

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences")
    @patch("nodes.supervisor_node.save_preferences")
    def test_loads_preferences_when_state_has_none(self, mock_save, mock_load, mock_llm_cls, _):
        mock_load.return_value = EMPTY_PREFS
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision()
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        supervisor_node(_base_state(prefs=None))

        mock_load.assert_called_once_with("2")

    @patch("nodes.supervisor_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.supervisor_node.ChatOpenAI")
    @patch("nodes.supervisor_node.load_preferences", return_value=EMPTY_PREFS)
    @patch("nodes.supervisor_node.save_preferences")
    def test_skips_load_when_preferences_already_in_state(self, mock_save, mock_load, mock_llm_cls, _):
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = _make_decision()
        mock_llm_cls.return_value = mock_llm

        from nodes.supervisor_node import supervisor_node
        supervisor_node(_base_state(prefs={"genres": ["rock"], "artists": []}))

        mock_load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
