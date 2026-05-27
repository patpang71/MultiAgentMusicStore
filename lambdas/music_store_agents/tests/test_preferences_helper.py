import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from botocore.exceptions import ClientError

CUSTOMER_ID = "2"
PREFS = {"genres": ["jazz"], "artists": ["Miles Davis"]}
EMPTY_PREFS = {"genres": [], "artists": []}
_CLIENT_ERROR = ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": ""}}, "GetItem")


def _mock_table(get_item_return=None, put_item_raises=None, get_item_raises=None):
    table = MagicMock()
    if get_item_raises:
        table.get_item.side_effect = get_item_raises
    else:
        table.get_item.return_value = get_item_return or {}
    if put_item_raises:
        table.put_item.side_effect = put_item_raises
    return table


class TestLoadPreferences(unittest.TestCase):

    @patch("preferences_helper.boto3")
    def test_returns_saved_preferences_when_item_exists(self, mock_boto3):
        mock_boto3.resource.return_value.Table.return_value = _mock_table(
            get_item_return={"Item": {"customerId": CUSTOMER_ID, "preferences": PREFS}}
        )
        from preferences_helper import load_preferences
        self.assertEqual(load_preferences(CUSTOMER_ID), PREFS)

    @patch("preferences_helper.boto3")
    def test_returns_defaults_when_item_missing(self, mock_boto3):
        mock_boto3.resource.return_value.Table.return_value = _mock_table(get_item_return={})
        from preferences_helper import load_preferences
        self.assertEqual(load_preferences("unknown"), EMPTY_PREFS)

    @patch("preferences_helper.boto3")
    def test_returns_defaults_when_item_has_no_preferences_key(self, mock_boto3):
        mock_boto3.resource.return_value.Table.return_value = _mock_table(
            get_item_return={"Item": {"customerId": CUSTOMER_ID}}
        )
        from preferences_helper import load_preferences
        self.assertEqual(load_preferences(CUSTOMER_ID), EMPTY_PREFS)

    @patch("preferences_helper.boto3")
    def test_returns_defaults_on_client_error(self, mock_boto3):
        mock_boto3.resource.return_value.Table.return_value = _mock_table(
            get_item_raises=_CLIENT_ERROR
        )
        from preferences_helper import load_preferences
        result = load_preferences(CUSTOMER_ID)
        self.assertEqual(result, EMPTY_PREFS)


class TestSavePreferences(unittest.TestCase):

    @patch("preferences_helper.boto3")
    def test_puts_item_with_correct_payload(self, mock_boto3):
        table = _mock_table()
        mock_boto3.resource.return_value.Table.return_value = table
        from preferences_helper import save_preferences
        save_preferences(CUSTOMER_ID, PREFS)
        table.put_item.assert_called_once_with(
            Item={"customerId": CUSTOMER_ID, "preferences": PREFS}
        )

    @patch("preferences_helper.boto3")
    def test_silently_ignores_client_error(self, mock_boto3):
        put_error = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": ""}}, "PutItem"
        )
        mock_boto3.resource.return_value.Table.return_value = _mock_table(put_item_raises=put_error)
        from preferences_helper import save_preferences
        save_preferences(CUSTOMER_ID, PREFS)  # Must not raise


if __name__ == "__main__":
    unittest.main()
