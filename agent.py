"""Real customer-support agent used by the DeepEval tracing evaluation.

The agent chooses tools through Groq tool calling.  The tools are local
support-service implementations for this evaluation project; no test result
is read from the CSV as the agent's actual tool call.
"""

import os
from typing import Any, Callable

from deepeval.test_case import ToolCall
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from deepeval.tracing.context import update_current_trace
from deepeval.integrations.langchain import CallbackHandler


MODEL_NAME = os.getenv("AGENT_MODEL", "openai/gpt-oss-20b")


ORDERS = {
    "ORD-1042": {"status": "Shipped", "eta": "2026-05-13", "category": "electronics"},
    "ORD-2099": {"status": "Delivered", "eta": "2026-05-08", "category": "clothing"},
    "ORD-7777": {"status": "Processing", "eta": "2026-05-15", "category": "food"},
    # Order fixtures referenced by agentic_metrics_dataset.csv.
    "ORD1001": {"status": "Processing", "eta": "2026-09-12", "category": "electronics"},
    "ORD1003": {"status": "Processing", "eta": "2026-09-14", "category": "clothing"},
    "ORD1004": {"status": "Processing", "eta": "2026-09-15", "category": "electronics"},
    "ORD1006": {"status": "Shipped", "eta": "2026-09-11", "category": "electronics"},
    "ORD1007": {"status": "Shipped", "eta": "2026-09-13", "category": "electronics"},
    "ORD1016": {"status": "Processing", "eta": "2026-09-16", "category": "clothing"},
    "ORD2001": {"status": "Shipped", "eta": "2026-09-12", "category": "electronics"},
    "ORD2002": {"status": "Processing", "eta": "2026-09-17", "category": "electronics"},
    "ORD2003": {"status": "Delivered", "eta": "2026-09-05", "category": "clothing"},
    "ORD2005": {"status": "Shipped", "eta": "2026-09-10", "category": "electronics"},
    "ORD2007": {"status": "Delivered", "eta": "2026-09-04", "category": "electronics"},
    "ORD2033": {"status": "Delivered", "eta": "2026-09-01", "category": "clothing"},
}


@tool(description="Track an order using its order ID.")
def track_order_tool(order_id: str) -> str:
    order = ORDERS.get(order_id.upper())
    if not order:
        return f"No order was found for {order_id}."
    return f"Order {order_id} is {order['status']}. Estimated delivery: {order['eta']}."


@tool(description="Find the refund policy for a product category.")
def refund_policy_tool(category: str) -> str:
    policies = {
        "electronics": "Electronics can be returned within 15 days if unopened.",
        "clothing": "Clothing can be returned within 30 days with tags attached.",
        "food": "Food items are non-returnable for safety reasons.",
    }
    return policies.get(category.lower(), f"No refund policy is available for {category}.")


@tool(description="Change the delivery address before shipment.")
def change_address_tool(order_id: str, new_address: str) -> str:
    if not new_address.strip():
        return "A new delivery address is required."
    return f"The delivery address for {order_id} can be changed before shipment."


@tool(description="Request cancellation of an order before shipment.")
def cancel_order_tool(order_id: str) -> str:
    return f"Cancellation was requested for {order_id}. The request will be checked before shipment."


@tool(description="Check the possible cancellation fee for an order.")
def cancellation_fee_tool(order_id: str) -> str:
    return f"The cancellation fee for {order_id} depends on its shipment status."


@tool(description="Find the estimated delivery date for an order.")
def delivery_estimate_tool(order_id: str) -> str:
    order = ORDERS.get(order_id.upper())
    return f"Estimated delivery for {order_id}: {order['eta']}." if order else f"No estimate is available for {order_id}."


@tool(description="List the available delivery options.")
def delivery_options_tool() -> str:
    return "Available delivery options are standard, express, and scheduled delivery."


@tool(description="Find the invoice for an order.")
def get_invoice_tool(order_id: str) -> str:
    return f"The invoice for {order_id} is available in the customer's order account."


@tool(description="Record or investigate a payment issue.")
def payment_issue_tool(issue: str) -> str:
    return f"Payment support will review this issue: {issue}."


@tool(description="List the accepted payment methods.")
def payment_methods_tool() -> str:
    return "Accepted payment methods include cards, UPI, and supported digital wallets."


@tool(description="Explain the normal refund processing timeline.")
def refund_timeline_tool() -> str:
    return "Approved refunds are normally processed within 5 to 7 business days."


@tool(description="Track a refund using its refund ID.")
def track_refund_tool(refund_id: str) -> str:
    return f"Refund status for {refund_id}: processing."


@tool(description="Create a return request for an order.")
def return_request_tool(order_id: str, reason: str) -> str:
    return f"A return request was created for {order_id}. Reason recorded: {reason}."


@tool(description="Start password recovery for an account.")
def recover_password_tool(email: str) -> str:
    return f"Password recovery instructions will be sent to {email}."


@tool(description="Prepare an account field for updating.")
def edit_account_tool(field: str, value: str) -> str:
    return f"The account field '{field}' is ready to be updated."


@tool(description="Start the account deletion process.")
def delete_account_tool() -> str:
    return "Account deletion requires identity verification before completion."


@tool(description="Subscribe or unsubscribe a customer from the newsletter.")
def newsletter_subscription_tool(action: str) -> str:
    return f"Newsletter subscription action '{action}' was recorded."


@tool(description="Record a customer complaint.")
def complaint_tool(issue: str) -> str:
    return f"The complaint was recorded for review: {issue}."


@tool(description="Submit a customer review for an order.")
def review_tool(order_id: str, review: str) -> str:
    return f"Your review for {order_id} was submitted."


@tool(description="Transfer a request to a human support representative.")
def human_handoff_tool(reason: str) -> str:
    return f"A support representative will handle this request. Reason: {reason}."


TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    name: function
    for name, function in globals().items()
    if name.endswith("_tool") and callable(function)
}


def _tool_schema(
    name: str,
    description: str,
    properties: dict[str, dict[str, str]] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    """Create the schema Groq needs in order to select and call a tool."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


TOOL_SCHEMAS = [
    _tool_schema(
        "track_order_tool",
        "Track an order using its order ID.",
        {"order_id": {"type": "string", "description": "The order ID."}},
        ["order_id"],
    ),
    _tool_schema(
        "refund_policy_tool",
        "Find the refund policy for a product category.",
        {"category": {"type": "string", "description": "The product category."}},
        ["category"],
    ),
    _tool_schema(
        "change_address_tool",
        "Change the delivery address before shipment.",
        {
            "order_id": {"type": "string", "description": "The order ID."},
            "new_address": {"type": "string", "description": "The new delivery address."},
        },
        ["order_id", "new_address"],
    ),
    _tool_schema(
        "cancel_order_tool",
        "Request cancellation of an order before shipment.",
        {"order_id": {"type": "string", "description": "The order ID."}},
        ["order_id"],
    ),
    _tool_schema(
        "cancellation_fee_tool",
        "Check the possible cancellation fee for an order.",
        {"order_id": {"type": "string", "description": "The order ID."}},
        ["order_id"],
    ),
    _tool_schema(
        "delivery_estimate_tool",
        "Find the estimated delivery date for an order.",
        {"order_id": {"type": "string", "description": "The order ID."}},
        ["order_id"],
    ),
    _tool_schema("delivery_options_tool", "List the available delivery options."),
    _tool_schema(
        "get_invoice_tool",
        "Find the invoice for an order.",
        {"order_id": {"type": "string", "description": "The order ID."}},
        ["order_id"],
    ),
    _tool_schema(
        "payment_issue_tool",
        "Record or investigate a payment issue.",
        {"issue": {"type": "string", "description": "The payment issue."}},
        ["issue"],
    ),
    _tool_schema("payment_methods_tool", "List the accepted payment methods."),
    _tool_schema("refund_timeline_tool", "Explain the normal refund processing timeline."),
    _tool_schema(
        "track_refund_tool",
        "Track a refund using its refund ID.",
        {"refund_id": {"type": "string", "description": "The refund ID."}},
        ["refund_id"],
    ),
    _tool_schema(
        "return_request_tool",
        "Create a return request for an order.",
        {
            "order_id": {"type": "string", "description": "The order ID."},
            "reason": {"type": "string", "description": "The return reason."},
        },
        ["order_id", "reason"],
    ),
    _tool_schema(
        "recover_password_tool",
        "Start password recovery for an account.",
        {"email": {"type": "string", "description": "The account email."}},
        ["email"],
    ),
    _tool_schema(
        "edit_account_tool",
        "Prepare an account field for updating.",
        {
            "field": {"type": "string", "description": "The account field."},
            "value": {"type": "string", "description": "The new value."},
        },
        ["field", "value"],
    ),
    _tool_schema("delete_account_tool", "Start the account deletion process."),
    _tool_schema(
        "newsletter_subscription_tool",
        "Subscribe or unsubscribe a customer from the newsletter.",
        {"action": {"type": "string", "description": "Subscribe or unsubscribe."}},
        ["action"],
    ),
    _tool_schema(
        "complaint_tool",
        "Record a customer complaint.",
        {"issue": {"type": "string", "description": "The complaint details."}},
        ["issue"],
    ),
    _tool_schema(
        "review_tool",
        "Submit a customer review for an order.",
        {
            "order_id": {"type": "string", "description": "The order ID."},
            "review": {"type": "string", "description": "The review text."},
        },
        ["order_id", "review"],
    ),
    _tool_schema(
        "human_handoff_tool",
        "Transfer a request to a human support representative.",
        {"reason": {"type": "string", "description": "The reason for handoff."}},
        ["reason"],
    ),
]


TOOL_DESCRIPTIONS = {
    schema["function"]["name"]: schema["function"]["description"]
    for schema in TOOL_SCHEMAS
}


LANGCHAIN_TOOLS = [
    track_order_tool,
    refund_policy_tool,
    change_address_tool,
    cancel_order_tool,
    cancellation_fee_tool,
    delivery_estimate_tool,
    delivery_options_tool,
    get_invoice_tool,
    payment_issue_tool,
    payment_methods_tool,
    refund_timeline_tool,
    track_refund_tool,
    return_request_tool,
    recover_password_tool,
    edit_account_tool,
    delete_account_tool,
    newsletter_subscription_tool,
    complaint_tool,
    review_tool,
    human_handoff_tool,
]

print("LangChain tools registered:", len(LANGCHAIN_TOOLS))


llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0,
)


langchain_agent = create_agent(
    model=llm,
    tools=LANGCHAIN_TOOLS,
    system_prompt=(
        "You are a customer-support agent. "
        "Choose the correct tool when needed and answer concisely."
    ),
)

print("LangChain Groq agent created.")


deepeval_callback = CallbackHandler()


def support_agent(user_input: str) -> str:
    """Run the LangChain agent and return its final response."""
    result = langchain_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_input,
                }
            ]
        },
        config={"callbacks": [deepeval_callback]},
    )

    answer = result["messages"][-1].content

    tool_calls = []
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            matching_result = next(
                (
                    tool_message
                    for tool_message in result["messages"]
                    if getattr(tool_message, "tool_call_id", None) == call.get("id")
                ),
                None,
            )
            tool_calls.append(
                ToolCall(
                    name=call["name"],
                    input_parameters=call.get("args", {}),
                    output=(
                        getattr(matching_result, "content", None)
                        if matching_result is not None
                        else None
                    ),
                )
            )

    update_current_trace(
        input=user_input,
        output=answer,
        tools_called=tool_calls,
    )

    return answer
