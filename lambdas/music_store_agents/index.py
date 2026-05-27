from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from graph import create_graph


def _deserialize_messages(raw: list) -> list:
    """Convert dict messages from the Lambda event into LangChain objects."""
    result = []
    for msg in raw:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
        # tool messages from previous turns are skipped (they are regenerated each turn)
    return result


def _serialize_messages(messages: list) -> list:
    """Convert LangChain message objects back to JSON-serialisable dicts."""
    role_map = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}
    result = []
    for msg in messages:
        if hasattr(msg, "type"):
            role = role_map.get(msg.type, msg.type)
            result.append({"role": role, "content": msg.content})
        elif isinstance(msg, dict):
            result.append(msg)
    return result


def handler(event, context):
    state = {
        "messages": _deserialize_messages(event.get("messages", [])),
        "customer_info": event.get("customer_info"),
        "verified": event.get("verified", False),
        "preferences": event.get("preferences"),   # None on first login; loaded from DynamoDB by supervisor
        "next_agent": "",                           # Always reset at the start of each Lambda invocation
    }

    graph = create_graph()
    result = graph.invoke(state)

    return {
        "messages": _serialize_messages(result["messages"]),
        "customer_info": result.get("customer_info"),
        "verified": result.get("verified", False),
        "preferences": result.get("preferences"),
        "next_agent": result.get("next_agent", ""),
    }
