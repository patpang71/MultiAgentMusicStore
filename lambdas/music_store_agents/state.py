from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    customer_info: Optional[dict]
    verified: bool
    preferences: Optional[dict]   # {"genres": [...], "artists": [...]}
    next_agent: str               # "", "music", "invoice", "end", "answered"
