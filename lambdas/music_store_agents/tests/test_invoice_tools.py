import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

INVOICES = [{"invoiceId": 10, "total": 5.94, "invoiceDate": "2021-01-01"}]
LINE_ITEMS = {"invoiceId": 10, "lineItems": [{"track": "Thunderstruck", "unitPrice": 0.99}]}
TOP_TRACKS = [{"name": "Thunderstruck", "unitPrice": 1.99}]


def _make_lambda_response(payload: dict):
    mock = MagicMock()
    mock["Payload"].read.return_value = json.dumps(payload).encode()
    return mock


class TestInvoiceTools(unittest.TestCase):

    @patch("tools.invoice_tools.boto3")
    def test_get_invoices_by_customer(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(INVOICES)
        from tools.invoice_tools import get_invoices_by_customer
        result = json.loads(get_invoices_by_customer.invoke({"customer_id": 2}))
        self.assertEqual(result, INVOICES)

    @patch("tools.invoice_tools.boto3")
    def test_get_invoice_line_items(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(LINE_ITEMS)
        from tools.invoice_tools import get_invoice_line_items
        result = json.loads(get_invoice_line_items.invoke({"invoice_id": 10}))
        self.assertIn("lineItems", result)

    @patch("tools.invoice_tools.boto3")
    def test_get_purchased_tracks_by_price_sends_null_input(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(TOP_TRACKS)
        from tools.invoice_tools import get_purchased_tracks_by_price

        get_purchased_tracks_by_price.invoke({})

        payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(payload["tool"], "get_purchased_tracks_sorted_by_unit_price")
        self.assertIsNone(payload["input"])

    @patch("tools.invoice_tools.boto3")
    def test_correct_tool_name_sent_for_invoices(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(INVOICES)
        from tools.invoice_tools import get_invoices_by_customer

        get_invoices_by_customer.invoke({"customer_id": 2})

        payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(payload["tool"], "get_invoices_by_customer_sorted_by_date")
        self.assertEqual(payload["input"], 2)

    @patch("tools.invoice_tools.boto3")
    def test_correct_tool_name_sent_for_line_items(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(LINE_ITEMS)
        from tools.invoice_tools import get_invoice_line_items

        get_invoice_line_items.invoke({"invoice_id": 99})

        payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(payload["tool"], "get_detail_line_item_for_invoice")
        self.assertEqual(payload["input"], 99)


if __name__ == "__main__":
    unittest.main()
