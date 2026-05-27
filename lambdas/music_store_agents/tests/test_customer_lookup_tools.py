import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../tools"))

CUSTOMER_ROW = {
    "customerId": "2", "firstName": "Leonie", "lastName": "Köhler",
    "email": "leonekohler@surfeu.de", "company": None,
    "city": "Stuttgart", "country": "Germany", "phone": "+49 0711 2842222",
}
NOT_FOUND = {"message": "Cannot find customer with id 99"}


def _make_lambda_response(payload: dict):
    mock_response = MagicMock()
    mock_response["Payload"].read.return_value = json.dumps(payload).encode()
    return mock_response


class TestCustomerLookupTools(unittest.TestCase):

    @patch("tools.customer_lookup_tools.boto3")
    def test_get_customer_by_id_found(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(CUSTOMER_ROW)
        from tools.customer_lookup_tools import get_customer_by_id

        result = json.loads(get_customer_by_id.invoke({"customer_id": 2}))

        self.assertEqual(result["customerId"], "2")
        self.assertEqual(result["firstName"], "Leonie")

    @patch("tools.customer_lookup_tools.boto3")
    def test_get_customer_by_id_not_found(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(NOT_FOUND)
        from tools.customer_lookup_tools import get_customer_by_id

        result = json.loads(get_customer_by_id.invoke({"customer_id": 99}))

        self.assertIn("message", result)

    @patch("tools.customer_lookup_tools.boto3")
    def test_get_customer_by_email_found(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(CUSTOMER_ROW)
        from tools.customer_lookup_tools import get_customer_by_email

        result = json.loads(get_customer_by_email.invoke({"email": "leonekohler@surfeu.de"}))

        self.assertEqual(result["email"], "leonekohler@surfeu.de")

    @patch("tools.customer_lookup_tools.boto3")
    def test_get_customer_by_phone_found(self, mock_boto3):
        mock_boto3.client.return_value.invoke.return_value = _make_lambda_response(CUSTOMER_ROW)
        from tools.customer_lookup_tools import get_customer_by_phone

        result = json.loads(get_customer_by_phone.invoke({"phone": "+4907112842222"}))

        self.assertEqual(result["customerId"], "2")

    @patch("tools.customer_lookup_tools.boto3")
    def test_correct_tool_name_sent_to_lambda(self, mock_boto3):
        mock_client = mock_boto3.client.return_value
        mock_client.invoke.return_value = _make_lambda_response(CUSTOMER_ROW)
        from tools.customer_lookup_tools import get_customer_by_email

        get_customer_by_email.invoke({"email": "test@test.com"})

        call_payload = json.loads(mock_client.invoke.call_args[1]["Payload"])
        self.assertEqual(call_payload["tool"], "get_customer_by_email")
        self.assertEqual(call_payload["input"], "test@test.com")


if __name__ == "__main__":
    unittest.main()
