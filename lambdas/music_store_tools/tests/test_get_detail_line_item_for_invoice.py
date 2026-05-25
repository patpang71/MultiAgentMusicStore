import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_detail_line_item_for_invoice import get_detail_line_item_for_invoice

SAMPLE_ROW_1 = {
    "invoiceId":         1,
    "customerId":        2,
    "invoiceDate":       "2021-01-01 00:00:00",
    "billingAddress":    "Theodor-Heuss-Straße 34",
    "billingCity":       "Stuttgart",
    "billingState":      None,
    "billingCountry":    "Germany",
    "billingPostalCode": "70174",
    "total":             1.98,
    "invoiceLineId":     1,
    "trackId":           2,
    "trackName":         "Balls to the Wall",
    "unitPrice":         0.99,
    "quantity":          1,
}

SAMPLE_ROW_2 = {**SAMPLE_ROW_1, "invoiceLineId": 2, "trackId": 4, "trackName": "Restless and Wild"}


class TestGetDetailLineItemForInvoice(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_detail_line_item_for_invoice.get_connection")
    def test_found_invoice_with_multiple_line_items(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW_1, SAMPLE_ROW_2])

        result = get_detail_line_item_for_invoice(1)

        self.assertEqual(result["invoiceId"], "1")
        self.assertEqual(result["customerId"], "2")
        self.assertEqual(result["billingCity"], "Stuttgart")
        self.assertEqual(result["total"], "1.98")
        self.assertEqual(len(result["lineItems"]), 2)

        line = result["lineItems"][0]
        self.assertEqual(line["invoiceLineId"], "1")
        self.assertEqual(line["trackName"], "Balls to the Wall")
        self.assertEqual(line["unitPrice"], "0.99")
        self.assertEqual(line["quantity"], "1")

    @patch("get_detail_line_item_for_invoice.get_connection")
    def test_invoice_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = get_detail_line_item_for_invoice(99999)

        self.assertEqual(result, {"message": "Cannot find invoice 99999"})

    def test_non_numeric_invoice_id(self):
        result = get_detail_line_item_for_invoice("abc")

        self.assertIn("Error", result["message"])
        self.assertIn("numeric", result["message"])

    @patch("get_detail_line_item_for_invoice.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Timeout")

        result = get_detail_line_item_for_invoice(1)

        self.assertIn("Error", result["message"])
        self.assertIn("Timeout", result["message"])

    @patch("get_detail_line_item_for_invoice.get_connection")
    def test_string_numeric_invoice_id_accepted(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW_1])

        result = get_detail_line_item_for_invoice("1")

        self.assertEqual(result["invoiceId"], "1")


if __name__ == "__main__":
    unittest.main()
