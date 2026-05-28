from langgraph.graph import StateGraph, END

from state import AgentState
from nodes.verify_info_node import verify_info_node
from nodes.supervisor_node import supervisor_node
from nodes.music_agent_node import music_agent_node
from nodes.invoice_agent_node import invoice_agent_node


def _entry_router(state: AgentState) -> str:
    return "supervisor" if state.get("verified") else "verify_info"


def _after_verify_router(state: AgentState) -> str:
    return "supervisor" if state.get("verified") else END


def _supervisor_router(state: AgentState) -> str:
    next_agent = state.get("next_agent", "")
    if next_agent == "music":
        return "music_agent"
    elif next_agent == "invoice":
        return "invoice_agent"
    else:
        return END


def create_graph(checkpointer=None):
    builder = StateGraph(AgentState)

    builder.add_node("verify_info", verify_info_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("music_agent", music_agent_node)
    builder.add_node("invoice_agent", invoice_agent_node)

    builder.set_conditional_entry_point(
        _entry_router,
        {"verify_info": "verify_info", "supervisor": "supervisor"},
    )
    builder.add_conditional_edges("verify_info", _after_verify_router, {
        "supervisor": "supervisor",
        END: END,
    })
    builder.add_conditional_edges("supervisor", _supervisor_router, {
        "music_agent": "music_agent",
        "invoice_agent": "invoice_agent",
        END: END,
    })
    # Sub-agents loop back to supervisor so it can ask "What else?"
    builder.add_edge("music_agent", "supervisor")
    builder.add_edge("invoice_agent", "supervisor")

    return builder.compile(checkpointer=checkpointer)
