import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

CUSTOMER_ROW = {
    "customerId": "2", "firstName": "Leonie", "lastName": "Köhler",
    "email": "leonekohler@surfeu.de", "company": None,
    "city": "Stuttgart", "country": "Germany", "phone": "+49 0711 2842222",
}


class TestHandler(unittest.TestCase):

    def _mock_graph_result(self, verified=False, customer_info=None, reply="Hello!"):
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content=reply)],
            "customer_info": customer_info,
            "verified": verified,
        }

    @patch("index.create_graph")
    def test_unverified_response(self, mock_create_graph):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = self._mock_graph_result(
            verified=False, reply="Please provide your ID, email, or phone."
        )
        mock_create_graph.return_value = mock_graph

        import index
        event = {"messages": [{"role": "user", "content": "Hello"}], "verified": False}
        result = index.handler(event, None)

        self.assertFalse(result["verified"])
        self.assertIsNone(result["customer_info"])
        self.assertEqual(result["messages"][0]["role"], "assistant")

    @patch("index.create_graph")
    def test_verified_response(self, mock_create_graph):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = self._mock_graph_result(
            verified=True, customer_info=CUSTOMER_ROW, reply="Welcome, Leonie!"
        )
        mock_create_graph.return_value = mock_graph

        import index
        event = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Please provide your info."},
                {"role": "user", "content": "My email is leonekohler@surfeu.de"},
            ],
            "verified": False,
        }
        result = index.handler(event, None)

        self.assertTrue(result["verified"])
        self.assertEqual(result["customer_info"]["customerId"], "2")

    @patch("index.create_graph")
    def test_already_verified_skips_node(self, mock_create_graph):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = self._mock_graph_result(
            verified=True, customer_info=CUSTOMER_ROW
        )
        mock_create_graph.return_value = mock_graph

        import index
        event = {
            "messages": [],
            "customer_info": CUSTOMER_ROW,
            "verified": True,
        }
        result = index.handler(event, None)

        # Graph is invoked with verified=True so the entry router skips verify_info
        call_args = mock_graph.invoke.call_args[0][0]
        self.assertTrue(call_args["verified"])

    @patch("index.create_graph")
    def test_empty_messages_handled(self, mock_create_graph):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = self._mock_graph_result()
        mock_create_graph.return_value = mock_graph

        import index
        result = index.handler({}, None)

        self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main()
