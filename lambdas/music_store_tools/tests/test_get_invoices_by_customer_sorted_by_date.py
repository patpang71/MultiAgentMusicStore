import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_invoices_by_customer_sorted_by_date import get_invoices_by_customer_sorted_by_date

SAMPLE_ROW = {
    "invoiceId":      1,
    "customerId":     2,
    "invoiceDate":    "2021-01-01 00:00:00",
    "billingAddress": "Theodor-Heuss-Straße 34",
    "billingCity":    "Stuttgart",
    "billingState":   None,
    "billingCountry": "Germany",
}


class TestGetInvoicesByCustomerSortedByDate(unittest.TestCase):

    def _make_conn(self, rows):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_invoices_by_customer_sorted_by_date.get_connection")
    def test_found_invoices(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = get_invoices_by_customer_sorted_by_date(2)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        invoice = result[0]
        self.assertEqual(invoice["invoiceId"], "1")
        self.assertEqual(invoice["customerId"], "2")
        self.assertEqual(invoice["invoiceDate"], "2021-01-01 00:00:00")
        self.assertEqual(invoice["billingCity"], "Stuttgart")
        self.assertEqual(invoice["billingCountry"], "Germany")

    @patch("get_invoices_by_customer_sorted_by_date.get_connection")
    def test_no_invoices_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([])

        result = get_invoices_by_customer_sorted_by_date(99999)

        self.assertIn("message", result)
        self.assertIn("Cannot find any invoices", result["message"])

    def test_non_numeric_customer_id(self):
        result = get_invoices_by_customer_sorted_by_date("abc")

        self.assertIn("Error", result["message"])
        self.assertIn("numeric", result["message"])

    @patch("get_invoices_by_customer_sorted_by_date.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection refused")

        result = get_invoices_by_customer_sorted_by_date(2)

        self.assertIn("Error", result["message"])
        self.assertIn("Connection refused", result["message"])

    @patch("get_invoices_by_customer_sorted_by_date.get_connection")
    def test_string_numeric_customer_id_accepted(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn([SAMPLE_ROW])

        result = get_invoices_by_customer_sorted_by_date("2")

        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
