import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_customer_by_email import get_customer_by_email

SAMPLE_ROW = {
    "CustomerId":   2,
    "FirstName":    "Leonie",
    "LastName":     "Köhler",
    "Email":        "leonekohler@surfeu.de",
    "Company":      None,
    "Address":      "Theodor-Heuss-Straße 34",
    "City":         "Stuttgart",
    "State":        None,
    "Country":      "Germany",
    "PostalCode":   "70174",
    "Phone":        "+49 0711 2842222",
    "Fax":          None,
    "SupportRepId": 5,
}


class TestGetCustomerByEmail(unittest.TestCase):

    def _make_conn(self, row):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.return_value = row
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_customer_by_email.get_connection")
    def test_found_customer(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_customer_by_email("leonekohler@surfeu.de")

        self.assertEqual(result["customerId"], "2")
        self.assertEqual(result["email"], "leonekohler@surfeu.de")
        self.assertEqual(result["firstName"], "Leonie")
        self.assertEqual(result["country"], "Germany")

    @patch("get_customer_by_email.get_connection")
    def test_customer_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(None)

        result = get_customer_by_email("nobody@nowhere.com")

        self.assertEqual(result, {"message": "Cannot find customer with email nobody@nowhere.com"})

    @patch("get_customer_by_email.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("DB unavailable")

        result = get_customer_by_email("leonekohler@surfeu.de")

        self.assertIn("Error", result["message"])
        self.assertIn("DB unavailable", result["message"])


if __name__ == "__main__":
    unittest.main()
