"""Programmatic entry point for the open-source agent under test."""

from pathlib import Path
import sys
import uuid

from langgraph.types import Command
from deepeval.tracing import observe
from deepeval.tracing.context import update_current_trace


# Add the cloned agent folder to Python's import path because its source files
# use absolute imports such as ``from src.graph import build_graph``.
PROJECT_ROOT = Path(__file__).resolve().parent
OPEN_SOURCE_AGENT_ROOT = PROJECT_ROOT / "open_source_agent_under_test"

if str(OPEN_SOURCE_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(OPEN_SOURCE_AGENT_ROOT))

from src.graph import build_graph  # noqa: E402


WORKFLOW_NODES = (
    "classify_ticket",
    "approval_gate",
    "retrieve_knowledge",
    "draft_resolution",
    "final_review_gate",
    "resolve_case",
    "escalate_case",
)


def _capture_execution_path(graph, config: dict) -> list[str]:
    """Read the executed node names from the graph's saved checkpoints."""
    observed = []

    for snapshot in graph.get_state_history(config):
        metadata = getattr(snapshot, "metadata", {}) or {}
        writes = metadata.get("writes", {})
        if not isinstance(writes, dict):
            continue

        for node_name in writes:
            if node_name in WORKFLOW_NODES and node_name not in observed:
                observed.append(node_name)

    # LangGraph returns state history newest-first.
    return list(reversed(observed))


@observe(name="open_source_agent_evaluation")
def run_open_source_agent(
    customer_id: str,
    customer_message: str,
    db_path: str = "open_source_agent_checkpoints.db",
    review_decisions: dict | None = None,
):
    """Run the original agent and resume its human-review interruptions.

    The original agent pauses at human-review gates by design.  The adapter
    supplies deterministic review decisions so automated tests can complete
    the real workflow without changing the agent source code.

    ``review_decisions`` may override the defaults with decisions keyed by
    interrupt stage, for example::

        {
            "classification_review": {"decision": "approved"},
            "final_response_review": {"decision": "approve"},
        }

    The returned state contains ``_review_events`` for later evaluation and
    debugging.
    """
    graph = build_graph(db_path=db_path)

    thread_id = f"{customer_id}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    ticket_input = {
        "customer_id": customer_id,
        "customer_message": customer_message,
    }

    result = graph.invoke(ticket_input, config=config)
    review_events = []
    review_decisions = review_decisions or {}

    while True:
        interrupts = result.get("__interrupt__")
        if not interrupts:
            break

        interrupt_obj = interrupts[0]
        interrupt_value = (
            interrupt_obj.value
            if hasattr(interrupt_obj, "value")
            else interrupt_obj
        )
        stage = interrupt_value.get("stage", "unknown")

        interrupted_node = {
            "classification_review": "approval_gate",
            "final_response_review": "final_review_gate",
        }.get(stage)

        default_decision = (
            {"decision": "approved", "notes": "Automated evaluation approval"}
            if stage == "classification_review"
            else {"decision": "approve", "notes": "Automated evaluation approval"}
        )
        human_reply = review_decisions.get(stage, default_decision)

        review_events.append(
            {
                "stage": stage,
                "node": interrupted_node,
                "prompt": interrupt_value,
                "response": human_reply,
            }
        )
        result = graph.invoke(Command(resume=human_reply), config=config)

    completed_state = dict(result)
    execution_path = _capture_execution_path(graph, config)

    # Checkpoint metadata normally contains every node. Add the interrupted
    # gate explicitly as a fallback because an interrupt can occur before the
    # gate writes its normal state update.
    for event in review_events:
        node_name = event.get("node")
        if node_name and node_name not in execution_path:
            execution_path.append(node_name)

    # Keep the recorded path in the agent's declared workflow order.
    execution_path = [
        node_name
        for node_name in WORKFLOW_NODES
        if node_name in execution_path
    ]

    completed_state["_execution_path"] = execution_path
    completed_state["_review_events"] = review_events

    update_current_trace(
        input={
            "customer_id": customer_id,
            "customer_message": customer_message,
        },
        output=completed_state.get("final_response", ""),
        metadata={
            "execution_path": execution_path,
            "review_events": review_events,
            "completed_state": completed_state,
        },
    )

    return completed_state
