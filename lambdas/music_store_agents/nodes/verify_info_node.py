import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage

from state import AgentState
from secrets_helper import get_openai_api_key
from tools.customer_lookup_tools import CUSTOMER_TOOLS, TOOL_MAP

SYSTEM_PROMPT = """You are a friendly customer verification agent for a music store.

When the conversation starts, greet the user warmly and ask them to provide ONE of the following \
to verify their identity:
  - Customer ID (a number)
  - Email address
  - Phone number (digits only after country code, e.g. +4907112842222)

Use the available tools to look up the customer based on what they provide.
- If the customer is found: greet them by name and confirm they are verified.
- If the customer is not found: apologise politely and ask them to try a different identifier.

Never ask for all three at once. Accept whichever the user chooses to give first.
"""


def verify_info_node(state: AgentState) -> dict:
    api_key = get_openai_api_key()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)
    llm_with_tools = llm.bind_tools(CUSTOMER_TOOLS)

    # Prepend the system prompt to the existing conversation
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])

    customer_info = state.get("customer_info")
    verified = state.get("verified", False)
    new_messages = []

    # First LLM call — may produce tool calls or a plain response
    response = llm_with_tools.invoke(messages)
    new_messages.append(response)

    # Execute any tool calls the LLM requested
    if response.tool_calls:
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_fn = TOOL_MAP.get(tool_call["name"])
            if tool_fn:
                tool_result_str = tool_fn.invoke(tool_call["args"])
                result_data = json.loads(tool_result_str)

                # A successful lookup always contains "customerId"
                if "customerId" in result_data and not verified:
                    customer_info = result_data
                    verified = True

                tool_messages.append(
                    ToolMessage(
                        content=tool_result_str,
                        tool_call_id=tool_call["id"],
                    )
                )

        new_messages.extend(tool_messages)

        # Second LLM call with tool results so it can compose the final reply
        final_response = llm_with_tools.invoke(messages + new_messages)
        new_messages.append(final_response)

    # When verified, inject the customer profile into state as a system message
    # so downstream nodes can read it without re-querying the database
    if verified and customer_info:
        customer_context = SystemMessage(
            content=f"Verified customer profile: {json.dumps(customer_info)}"
        )
        new_messages = [customer_context] + new_messages

    return {
        "messages": new_messages,
        "customer_info": customer_info,
        "verified": verified,
    }
