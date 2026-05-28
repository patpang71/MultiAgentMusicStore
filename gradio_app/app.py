import os
import sys
import time
import uuid

import gradio as gr
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

# Agent source is mounted at /app/agents inside the container.
# When running locally from the project root, fall back to the Lambda source tree.
_AGENTS_DIR = os.path.join(os.path.dirname(__file__), "agents")
if not os.path.isdir(_AGENTS_DIR):
    _AGENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "lambdas", "music_store_agents")
sys.path.insert(0, os.path.abspath(_AGENTS_DIR))

from graph import create_graph  # noqa: E402

# One shared in-memory checkpointer; conversations are isolated by thread_id.
_checkpointer = MemorySaver()
_graph = create_graph(checkpointer=_checkpointer)


def _last_ai_message(messages: list) -> str | None:
    """Return the content of the last AI message in the list, or None."""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            return msg.content
    return None


def send_message(user_message: str, history: list, thread_id: str):
    if not user_message.strip():
        yield history, thread_id, "Ready", gr.update(value="")
        return

    # Show the user's message immediately — before the LLM responds.
    history = history + [{"role": "user", "content": user_message}]
    yield history, thread_id, "⏳ Processing…", gr.update(value="")

    config = {"configurable": {"thread_id": thread_id}}
    start = time.monotonic()

    try:
        snapshot = _graph.get_state(config)
        state_input: dict = {
            "messages": [HumanMessage(content=user_message)],
            # Always reset routing so a previous agent decision doesn't bleed into the new turn.
            "next_agent": "",
        }
        if not snapshot.values:
            # Brand-new thread: seed the required non-Optional fields.
            state_input.update({"verified": False, "customer_info": None, "preferences": None})

        result = _graph.invoke(state_input, config=config)
        elapsed = time.monotonic() - start

        ai_reply = _last_ai_message(result.get("messages", []))

        # Check whether the graph paused mid-run (human-in-the-loop interrupt point).
        post_snapshot = _graph.get_state(config)
        if post_snapshot.next:
            status = "⏸ Waiting for your input"
        elif ai_reply:
            status = f"✅ Response in {elapsed:.1f}s"
        else:
            status = "✅ Done"

        if ai_reply:
            history = history + [{"role": "assistant", "content": ai_reply}]

        yield history, thread_id, status, gr.update(value="")

    except Exception as exc:
        elapsed = time.monotonic() - start
        history = history + [
            {"role": "assistant", "content": "Sorry, something went wrong. Please try again."}
        ]
        yield history, thread_id, f"❌ Error after {elapsed:.1f}s: {exc}", gr.update(value="")


def new_conversation():
    """Start a completely fresh session with a new thread ID."""
    return [], str(uuid.uuid4()), "🆕 New conversation started", gr.update(value="")


# ---------------------------------------------------------------------------
# Gradio Blocks layout
# ---------------------------------------------------------------------------
with gr.Blocks(title="Music Store Assistant") as demo:
    gr.Markdown("## 🎵 Music Store Assistant")
    gr.Markdown(
        "Ask me about artists, albums, and tracks — or check your purchase history.  \n"
        "I'll ask you to verify your identity first."
    )

    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                height=520,
                placeholder="Your conversation will appear here…",
            )
        with gr.Column(scale=1, min_width=180):
            status_box = gr.Textbox(
                label="Status",
                value="Ready",
                interactive=False,
                lines=3,
            )
            gr.Markdown("---")
            reset_btn = gr.Button("🔄 New Conversation", variant="secondary", size="sm")

    with gr.Row():
        msg_input = gr.Textbox(
            placeholder="Type your message and press Enter…",
            show_label=False,
            scale=5,
            container=False,
            autofocus=True,
        )
        send_btn = gr.Button("Send ➤", variant="primary", scale=1, min_width=80)

    # gr.State with a factory function gives each browser session a unique UUID.
    thread_id = gr.State(lambda: str(uuid.uuid4()))

    for trigger in (send_btn.click, msg_input.submit):
        trigger(
            send_message,
            inputs=[msg_input, chatbot, thread_id],
            outputs=[chatbot, thread_id, status_box, msg_input],
        )

    reset_btn.click(
        new_conversation,
        outputs=[chatbot, thread_id, status_box, msg_input],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        show_error=True,
        theme=gr.themes.Soft(),
    )
