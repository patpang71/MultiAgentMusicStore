import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from get_customer_by_phone import get_customer_by_phone, _normalize_phone

SAMPLE_ROW = {
    "CustomerId":        2,
    "FirstName":         "Leonie",
    "LastName":          "Köhler",
    "Email":             "leonekohler@surfeu.de",
    "Company":           None,
    "Address":           "Theodor-Heuss-Straße 34",
    "City":              "Stuttgart",
    "State":             None,
    "Country":           "Germany",
    "PostalCode":        "70174",
    "Phone":             "+49 0711 2842222",
    "Fax":               None,
    "SupportRepId":      5,
    "PhoneNormalized":   "+4907112842222",
}


class TestNormalizePhone(unittest.TestCase):

    def test_strips_spaces(self):
        self.assertEqual(_normalize_phone("+49 0711 2842222"), "+4907112842222")

    def test_strips_parentheses(self):
        self.assertEqual(_normalize_phone("+55 (12) 3923-5555"), "+551239235555")

    def test_strips_dashes(self):
        self.assertEqual(_normalize_phone("+1-650-253-0000"), "+16502530000")

    def test_already_normalized(self):
        self.assertEqual(_normalize_phone("+4907112842222"), "+4907112842222")


class TestGetCustomerByPhone(unittest.TestCase):

    def _make_conn(self, row):
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.return_value = row
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    @patch("get_customer_by_phone.get_connection")
    def test_found_with_already_normalized_input(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_customer_by_phone("+4907112842222")

        self.assertEqual(result["customerId"], "2")
        self.assertEqual(result["phone"], "+49 0711 2842222")

    @patch("get_customer_by_phone.get_connection")
    def test_found_with_spaced_input(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(SAMPLE_ROW)

        result = get_customer_by_phone("+49 0711 2842222")

        self.assertEqual(result["customerId"], "2")

    @patch("get_customer_by_phone.get_connection")
    def test_customer_not_found(self, mock_get_conn):
        mock_get_conn.return_value = self._make_conn(None)

        result = get_customer_by_phone("+10000000000")

        self.assertEqual(result, {"message": "Cannot find customer with phone +10000000000"})

    @patch("get_customer_by_phone.get_connection")
    def test_db_exception(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Timeout")

        result = get_customer_by_phone("+4907112842222")

        self.assertIn("Error", result["message"])
        self.assertIn("Timeout", result["message"])


if __name__ == "__main__":
    unittest.main()
