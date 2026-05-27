import json
import os

import boto3
from langchain_core.tools import tool


def _function_name() -> str:
    return os.environ.get("MUSIC_STORE_TOOLS_FUNCTION_NAME", "music-store-tools")


def _invoke_tool(tool_name: str, input_value=None):
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=_function_name(),
        InvocationType="RequestResponse",
        Payload=json.dumps({"tool": tool_name, "input": input_value}),
    )
    return json.loads(response["Payload"].read())


@tool
def get_invoices_by_customer(customer_id: int) -> str:
    """Get all invoices for a customer sorted by date (newest first). Pass the customer's numeric ID."""
    return json.dumps(_invoke_tool("get_invoices_by_customer_sorted_by_date", customer_id))


@tool
def get_invoice_line_items(invoice_id: int) -> str:
    """Get the detailed line items (tracks, prices) for a specific invoice by its numeric InvoiceId."""
    return json.dumps(_invoke_tool("get_detail_line_item_for_invoice", invoice_id))


@tool
def get_purchased_tracks_by_price() -> str:
    """Get all tracks that have ever been purchased across the store, sorted by unit price (highest first).
    Use only for store-wide pricing questions, not for customer-specific purchase history."""
    return json.dumps(_invoke_tool("get_purchased_tracks_sorted_by_unit_price", None))


INVOICE_TOOLS = [
    get_invoices_by_customer,
    get_invoice_line_items,
    get_purchased_tracks_by_price,
]
INVOICE_TOOL_MAP = {t.name: t for t in INVOICE_TOOLS}
