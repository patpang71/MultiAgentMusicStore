import json
import logging

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from secrets_helper import get_openai_api_key

logger = logging.getLogger(__name__)
from state import AgentState
from tools.music_catalog_tools import MUSIC_TOOL_MAP, MUSIC_TOOLS

SYSTEM_PROMPT = """You are the music catalog agent for JP Music Store.

Answer the customer's music-related questions using ONLY the tools provided.
Do NOT make up information. Do NOT search the internet or use any knowledge outside the tools.

Rules:
- If a song, album, or artist is not found by the tools, respond with:
  "We don't have [that song / that album / that artist] in our catalog.
   Please try a different title or artist name."
- Use multiple tool calls if needed (e.g. search by artist first, then get track details).
- Include helpful details in your answer: track name, album, artist, genre, and unit price where available.
- Keep responses concise and easy to read.

After answering, end with: "Is there anything else you'd like to know about our music catalog?"
"""


def music_agent_node(state: AgentState) -> dict:
    logger = logging.getLogger(__name__)
    logger.info("music_agent_node called")
    api_key = get_openai_api_key()
    llm = ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0)
    llm_with_tools = llm.bind_tools(MUSIC_TOOLS)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    new_messages = []

    while True:
        response = llm_with_tools.invoke(messages + new_messages)
        new_messages.append(response)

        if not response.tool_calls:
            break

        for call in response.tool_calls:
            tool_fn = MUSIC_TOOL_MAP.get(call["name"])
            logger.info("Calling tool: %s with args: %s", call["name"], call["args"])
            result = (
                tool_fn.invoke(call["args"])
                if tool_fn
                else json.dumps({"error": f"unknown tool: {call['name']}"})
            )
            new_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    logger.info("music_agent_node completed")
    return {
        "messages": new_messages,
        "next_agent": "answered",
    }
