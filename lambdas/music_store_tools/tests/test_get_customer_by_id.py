import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_customer_by_id import get_customer_by_id

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


class TestGetCustomerById(unittest.TestCase):

    def _make_conn(self, row):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.return_value = row
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_customer_by_id.get_connection")
    def test_found_customer(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_customer_by_id(2)

        self.assertEqual(result["customerId"], "2")
        self.assertEqual(result["firstName"], "Leonie")
        self.assertEqual(result["lastName"], "Köhler")
        self.assertEqual(result["email"], "leonekohler@surfeu.de")
        self.assertIsNone(result["company"])
        self.assertEqual(result["city"], "Stuttgart")
        self.assertEqual(result["country"], "Germany")
        self.assertEqual(result["phone"], "+49 0711 2842222")

    @patch("get_customer_by_id.get_connection")
    def test_customer_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(None)

        result = get_customer_by_id(99999)

        self.assertEqual(result, {"message": "Cannot find customer with id 99999"})

    def test_non_numeric_id(self):
        result = get_customer_by_id("abc")

        self.assertIn("Error", result["message"])
        self.assertIn("numeric", result["message"])

    @patch("get_customer_by_id.get_connection")
    def test_string_numeric_id_accepted(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_customer_by_id("2")

        self.assertEqual(result["customerId"], "2")

    @patch("get_customer_by_id.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection refused")

        result = get_customer_by_id(2)

        self.assertIn("Error", result["message"])
        self.assertIn("Connection refused", result["message"])


if __name__ == "__main__":
    unittest.main()
