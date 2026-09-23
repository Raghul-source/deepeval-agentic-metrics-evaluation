"""Programmatic entry point for the open-source agent under test."""

from pathlib import Path
import sys
import uuid

from langgraph.types import Command


# Add the cloned agent folder to Python's import path because its source files
# use absolute imports such as ``from src.graph import build_graph``.
PROJECT_ROOT = Path(__file__).resolve().parent
OPEN_SOURCE_AGENT_ROOT = PROJECT_ROOT / "open_source_agent_under_test"

if str(OPEN_SOURCE_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(OPEN_SOURCE_AGENT_ROOT))

from src.graph import build_graph  # noqa: E402


def run_open_source_agent(
    customer_id: str,
    customer_message: str,
    db_path: str = "open_source_agent_checkpoints.db",
):
    """Start the original agent with a customer ID and message.

    This Stage 1 adapter does not evaluate metrics or automatically answer
    human-review interruptions. It returns the graph result so the next stage
    can add controlled interruption handling.
    """
    graph = build_graph(db_path=db_path)

    thread_id = f"{customer_id}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    ticket_input = {
        "customer_id": customer_id,
        "customer_message": customer_message,
    }

    return graph.invoke(ticket_input, config=config)
