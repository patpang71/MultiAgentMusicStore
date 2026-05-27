import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

CUSTOMER_ROW = {
    "customerId": "2", "firstName": "Leonie", "lastName": "Köhler",
    "email": "leonekohler@surfeu.de", "company": None,
    "city": "Stuttgart", "country": "Germany", "phone": "+49 0711 2842222",
}


def _make_tool_call_response(tool_name: str, args: dict, call_id: str = "call_123"):
    """Build an AIMessage that contains a tool call."""
    response = MagicMock(spec=AIMessage)
    response.type = "ai"
    response.content = ""
    response.tool_calls = [{"name": tool_name, "args": args, "id": call_id}]
    return response


def _make_plain_response(content: str):
    """Build an AIMessage with no tool calls."""
    response = MagicMock(spec=AIMessage)
    response.type = "ai"
    response.content = content
    response.tool_calls = []
    return response


class TestVerifyInfoNode(unittest.TestCase):

    def _base_state(self, messages=None):
        return {
            "messages": messages or [HumanMessage(content="Hello")],
            "customer_info": None,
            "verified": False,
        }

    @patch("nodes.verify_info_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.verify_info_node.ChatOpenAI")
    @patch("nodes.verify_info_node.TOOL_MAP")
    def test_customer_found_sets_verified(self, mock_tool_map, mock_llm_cls, _):
        # LLM first calls get_customer_by_email, then replies
        tool_response = _make_tool_call_response("get_customer_by_email", {"email": "leonekohler@surfeu.de"})
        final_reply = _make_plain_response("Welcome, Leonie! You are now verified.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_response, final_reply]
        mock_llm_cls.return_value = mock_llm

        mock_tool_fn = MagicMock()
        mock_tool_fn.invoke.return_value = json.dumps(CUSTOMER_ROW)
        mock_tool_map.__getitem__ = MagicMock(return_value=mock_tool_fn)
        mock_tool_map.get = MagicMock(return_value=mock_tool_fn)

        from nodes.verify_info_node import verify_info_node
        result = verify_info_node(self._base_state())

        self.assertTrue(result["verified"])
        self.assertEqual(result["customer_info"]["customerId"], "2")

    @patch("nodes.verify_info_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.verify_info_node.ChatOpenAI")
    @patch("nodes.verify_info_node.TOOL_MAP")
    def test_customer_not_found_stays_unverified(self, mock_tool_map, mock_llm_cls, _):
        not_found = {"message": "Cannot find customer with email nobody@x.com"}
        tool_response = _make_tool_call_response("get_customer_by_email", {"email": "nobody@x.com"})
        final_reply = _make_plain_response("Sorry, I couldn't find that account. Please try again.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_response, final_reply]
        mock_llm_cls.return_value = mock_llm

        mock_tool_fn = MagicMock()
        mock_tool_fn.invoke.return_value = json.dumps(not_found)
        mock_tool_map.get = MagicMock(return_value=mock_tool_fn)

        from nodes.verify_info_node import verify_info_node
        result = verify_info_node(self._base_state())

        self.assertFalse(result["verified"])
        self.assertIsNone(result["customer_info"])

    @patch("nodes.verify_info_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.verify_info_node.ChatOpenAI")
    def test_greeting_on_first_message(self, mock_llm_cls, _):
        greeting = _make_plain_response("Hello! Please provide your customer ID, email, or phone.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = greeting
        mock_llm_cls.return_value = mock_llm

        from nodes.verify_info_node import verify_info_node
        result = verify_info_node(self._base_state([HumanMessage(content="Hi")]))

        self.assertFalse(result["verified"])
        self.assertIsNone(result["customer_info"])
        self.assertTrue(len(result["messages"]) > 0)

    @patch("nodes.verify_info_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.verify_info_node.ChatOpenAI")
    @patch("nodes.verify_info_node.TOOL_MAP")
    def test_verified_customer_gets_system_message(self, mock_tool_map, mock_llm_cls, _):
        tool_response = _make_tool_call_response("get_customer_by_id", {"customer_id": 2})
        final_reply = _make_plain_response("Welcome, Leonie!")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_response, final_reply]
        mock_llm_cls.return_value = mock_llm

        mock_tool_fn = MagicMock()
        mock_tool_fn.invoke.return_value = json.dumps(CUSTOMER_ROW)
        mock_tool_map.get = MagicMock(return_value=mock_tool_fn)

        from nodes.verify_info_node import verify_info_node
        result = verify_info_node(self._base_state())

        # The first new message should be the customer context system message
        first_msg = result["messages"][0]
        self.assertIsInstance(first_msg, SystemMessage)
        self.assertIn("Verified customer profile", first_msg.content)


if __name__ == "__main__":
    unittest.main()
