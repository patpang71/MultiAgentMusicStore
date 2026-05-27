import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.messages import HumanMessage, AIMessage

CUSTOMER_ROW = {"customerId": "2", "firstName": "Leonie", "lastName": "Köhler"}
INVOICES = [{"invoiceId": 10, "total": 5.94, "invoiceDate": "2021-01-01"}]
LINE_ITEMS = {"invoiceId": 10, "lineItems": [{"track": "Thunderstruck", "unitPrice": 0.99}]}


def _base_state():
    return {
        "messages": [HumanMessage(content="Show me my recent invoices")],
        "customer_info": CUSTOMER_ROW,
        "verified": True,
        "preferences": {"genres": [], "artists": []},
        "next_agent": "invoice",
    }


def _make_tool_call(name, args, call_id="call_inv"):
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


class TestInvoiceAgentNode(unittest.TestCase):

    @patch("nodes.invoice_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.invoice_agent_node.ChatOpenAI")
    @patch("nodes.invoice_agent_node.INVOICE_TOOL_MAP")
    def test_calls_invoice_tool_and_returns_answer(self, mock_tool_map, mock_llm_cls, _):
        tool_call = _make_tool_call("get_invoices_by_customer", {"customer_id": 2})
        final = _make_plain("Your most recent invoice is #10 for $5.94.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [tool_call, final]
        mock_llm_cls.return_value = mock_llm

        mock_fn = MagicMock()
        mock_fn.invoke.return_value = json.dumps(INVOICES)
        mock_tool_map.get.return_value = mock_fn

        from nodes.invoice_agent_node import invoice_agent_node
        result = invoice_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")
        mock_fn.invoke.assert_called_once_with({"customer_id": 2})

    @patch("nodes.invoice_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.invoice_agent_node.ChatOpenAI")
    def test_no_tool_call_still_sets_answered(self, mock_llm_cls, _):
        final = _make_plain("I couldn't find that invoice on your account.")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = final
        mock_llm_cls.return_value = mock_llm

        from nodes.invoice_agent_node import invoice_agent_node
        result = invoice_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")

    @patch("nodes.invoice_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.invoice_agent_node.ChatOpenAI")
    @patch("nodes.invoice_agent_node.INVOICE_TOOL_MAP")
    def test_customer_id_included_in_system_prompt(self, mock_tool_map, mock_llm_cls, _):
        """The system prompt must reference the customer's ID so the LLM scopes queries correctly."""
        final = _make_plain("Here are your invoices.")

        captured_messages = []

        def capture_invoke(messages):
            captured_messages.extend(messages)
            return final

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = capture_invoke
        mock_llm_cls.return_value = mock_llm

        from nodes.invoice_agent_node import invoice_agent_node
        invoice_agent_node(_base_state())

        system_content = captured_messages[0].content
        self.assertIn("2", system_content)  # customer ID appears in system prompt

    @patch("nodes.invoice_agent_node.get_openai_api_key", return_value="sk-fake")
    @patch("nodes.invoice_agent_node.ChatOpenAI")
    @patch("nodes.invoice_agent_node.INVOICE_TOOL_MAP")
    def test_drills_into_line_items(self, mock_tool_map, mock_llm_cls, _):
        call1 = _make_tool_call("get_invoices_by_customer", {"customer_id": 2}, "c1")
        call2 = _make_tool_call("get_invoice_line_items", {"invoice_id": 10}, "c2")
        final = _make_plain("Invoice #10 contains: Thunderstruck ($0.99).")

        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = [call1, call2, final]
        mock_llm_cls.return_value = mock_llm

        def get_tool(name):
            fn = MagicMock()
            fn.invoke.return_value = json.dumps(INVOICES if "invoices" in name else LINE_ITEMS)
            return fn

        mock_tool_map.get.side_effect = get_tool

        from nodes.invoice_agent_node import invoice_agent_node
        result = invoice_agent_node(_base_state())

        self.assertEqual(result["next_agent"], "answered")
        self.assertEqual(mock_llm.bind_tools.return_value.invoke.call_count, 3)


if __name__ == "__main__":
    unittest.main()
