import json
import os
import boto3
from langchain_core.tools import tool

# Resolved at call time so tests can override the env var
def _function_name() -> str:
    return os.environ.get("MUSIC_STORE_TOOLS_FUNCTION_NAME", "music-store-tools")


def _invoke_music_store_tool(tool_name: str, input_value) -> dict:
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=_function_name(),
        InvocationType="RequestResponse",
        Payload=json.dumps({"tool": tool_name, "input": input_value}),
    )
    return json.loads(response["Payload"].read())


@tool
def get_customer_by_id(customer_id: int) -> str:
    """Look up a music store customer by their numeric customer ID."""
    result = _invoke_music_store_tool("get_customer_by_id", customer_id)
    return json.dumps(result)


@tool
def get_customer_by_email(email: str) -> str:
    """Look up a music store customer by their email address."""
    result = _invoke_music_store_tool("get_customer_by_email", email)
    return json.dumps(result)


@tool
def get_customer_by_phone(phone: str) -> str:
    """Look up a music store customer by phone number.
    Format: country code followed by digits, no spaces or symbols.
    Example: +4907112842222
    """
    result = _invoke_music_store_tool("get_customer_by_phone", phone)
    return json.dumps(result)


CUSTOMER_TOOLS = [get_customer_by_id, get_customer_by_email, get_customer_by_phone]
TOOL_MAP = {t.name: t for t in CUSTOMER_TOOLS}
