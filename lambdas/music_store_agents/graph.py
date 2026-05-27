from langgraph.graph import StateGraph, END

from state import AgentState
from nodes.verify_info_node import verify_info_node


def _entry_router(state: AgentState) -> str:
    """Skip verify_info if the customer is already verified."""
    return END if state.get("verified") else "verify_info"


def create_graph():
    builder = StateGraph(AgentState)
    builder.add_node("verify_info", verify_info_node)
    builder.set_conditional_entry_point(
        _entry_router,
        {"verify_info": "verify_info", END: END},
    )
    builder.add_edge("verify_info", END)
    return builder.compile()
