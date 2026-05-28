import json
import logging
from typing import List, Optional

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing_extensions import Literal

from preferences_helper import load_preferences, save_preferences
from secrets_helper import get_openai_api_key
from state import AgentState

logger = logging.getLogger(__name__)


class SupervisorDecision(BaseModel):
    response: str = Field(description="Natural language response to show the customer")
    route: Optional[Literal["music", "invoice", "end"]] = Field(
        default=None,
        description=(
            "Routing decision: 'music' for catalog questions, 'invoice' for billing/orders, "
            "'end' when the customer says goodbye or is done, null to show the menu and wait"
        ),
    )
    liked_genres: List[str] = Field(
        default_factory=list,
        description=(
            "Music genres the customer EXPLICITLY said they like or love "
            "(e.g. ['jazz', 'rock']). Empty if no explicit preference stated."
        ),
    )
    liked_artists: List[str] = Field(
        default_factory=list,
        description=(
            "Artists the customer EXPLICITLY said they like or love "
            "(e.g. ['AC/DC', 'Beethoven']). Empty if no explicit preference stated."
        ),
    )


SYSTEM_PROMPT = """You are the supervisor agent for JP Music Store.

Verified customer profile:
{customer_info}

Customer's saved music preferences:
{preferences}

Your role:
1. Greet the customer by their first name ({first_name}) when they first arrive after verification,
   then show the menu. For subsequent turns, use their name sparingly and naturally.
2. Classify each request and route it:
   - Questions about songs, albums, artists, or genres → route = "music"
   - Questions about invoices, orders, purchases, or billing → route = "invoice"
   - Customer says goodbye / thank you / done → route = "end"
   - No specific request yet, or request is unclear → route = null, show the menu:
     Hello {first_name}, Welcome to JP Music Store! How can I help you today?
      • Browse our music catalog (songs, albums, artists, genres)
      • Check your orders and invoices"
3. If a request is completely off-topic (unrelated to music or orders), politely explain
   you can only help with music catalog and order enquiries, and ask again.
4. Detect preference statements: only count EXPLICIT statements such as
   "I love jazz", "I like rock music", "my favourite artist is AC/DC".
   Do NOT count questions like "do you have jazz?" as preferences.
"""


def supervisor_node(state: AgentState) -> dict:
    logger.info("supervisor_node called, next_agent=%s", state.get("next_agent"))
    # Returning from a sub-agent — just ask "What else?" and end the turn
    if state.get("next_agent") == "answered":
        return {
            "messages": [AIMessage(content="Is there anything else I can help you with?")],
            "next_agent": "",
        }

    customer_info = state.get("customer_info") or {}
    customer_id = str(customer_info.get("customerId", ""))

    preferences = state.get("preferences")
    if preferences is None:
        preferences = load_preferences(customer_id)

    api_key = get_openai_api_key()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)
    structured_llm = llm.with_structured_output(SupervisorDecision)

    first_name = customer_info.get("firstName", "")
    system = SystemMessage(content=SYSTEM_PROMPT.format(
        customer_info=json.dumps(customer_info, ensure_ascii=False),
        preferences=json.dumps(preferences),
        first_name=first_name,
    ))
    messages = [system] + list(state["messages"])

    decision: SupervisorDecision = structured_llm.invoke(messages)
    logger.info("Supervisor decision: route=%s", decision.route)

    # Persist any newly detected preferences
    updated_prefs = {
        "genres": sorted(set(preferences.get("genres", []) + decision.liked_genres)),
        "artists": sorted(set(preferences.get("artists", []) + decision.liked_artists)),
    }
    if updated_prefs != preferences and customer_id:
        save_preferences(customer_id, updated_prefs)

    return {
        "messages": [AIMessage(content=decision.response)],
        "preferences": updated_prefs,
        "next_agent": decision.route or "",
    }
