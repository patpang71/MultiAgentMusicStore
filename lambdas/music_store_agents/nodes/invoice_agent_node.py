import json

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from secrets_helper import get_openai_api_key
from state import AgentState
from tools.invoice_tools import INVOICE_TOOL_MAP, INVOICE_TOOLS

SYSTEM_PROMPT = """You are the invoice agent for JP Music Store.

Verified customer: {customer_info}
Customer ID: {customer_id}

Answer the customer's invoice and order questions using ONLY the tools provided.

Rules:
- ONLY answer questions about this customer's own orders (customer ID {customer_id}).
  Use get_invoices_by_customer with customer_id={customer_id} — this scopes the results automatically.
- Never discuss invoices belonging to other customers.
- If an invoice is not found: "I couldn't find that invoice on your account."
- If a track or purchase is not found in their history: "I couldn't find that purchase in your order history."
- get_purchased_tracks_by_price is a store-wide list; only use it when the customer asks
  about store pricing (e.g. "what are the most expensive tracks?"), not for personal order lookups.
- Do NOT make up information. Only use the tools.

After answering, end with: "Is there anything else I can help you with regarding your orders?"
"""


def invoice_agent_node(state: AgentState) -> dict:
    customer_info = state.get("customer_info") or {}
    customer_id = customer_info.get("customerId", "")

    api_key = get_openai_api_key()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)
    llm_with_tools = llm.bind_tools(INVOICE_TOOLS)

    system = SystemMessage(content=SYSTEM_PROMPT.format(
        customer_info=json.dumps(customer_info, ensure_ascii=False),
        customer_id=customer_id,
    ))
    messages = [system] + list(state["messages"])
    new_messages = []

    while True:
        response = llm_with_tools.invoke(messages + new_messages)
        new_messages.append(response)

        if not response.tool_calls:
            break

        for call in response.tool_calls:
            tool_fn = INVOICE_TOOL_MAP.get(call["name"])
            result = (
                tool_fn.invoke(call["args"])
                if tool_fn
                else json.dumps({"error": f"unknown tool: {call['name']}"})
            )
            new_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    return {
        "messages": new_messages,
        "next_agent": "answered",
    }
