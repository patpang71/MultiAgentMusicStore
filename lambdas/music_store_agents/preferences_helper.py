import os

import boto3
from botocore.exceptions import ClientError

_DEFAULT_PREFS = {"genres": [], "artists": []}


def _table():
    name = os.environ.get("PREFERENCES_TABLE_NAME", "music-store-customer-preferences")
    return boto3.resource("dynamodb").Table(name)


def load_preferences(customer_id: str) -> dict:
    try:
        item = _table().get_item(Key={"customerId": customer_id}).get("Item")
        return item.get("preferences", dict(_DEFAULT_PREFS)) if item else dict(_DEFAULT_PREFS)
    except ClientError:
        return dict(_DEFAULT_PREFS)


def save_preferences(customer_id: str, preferences: dict) -> None:
    try:
        _table().put_item(Item={"customerId": customer_id, "preferences": preferences})
    except ClientError:
        pass
