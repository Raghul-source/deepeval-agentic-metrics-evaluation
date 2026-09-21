# Open Source Agent Smoke Testing Flow

## Purpose of This Smoke Test

The purpose of this smoke test is to confirm that the existing open-source customer-support agent works correctly with Groq before connecting DeepEval.

This test checks whether the agent can:

```text
start successfully
→ receive a customer ticket
→ classify the ticket
→ pause for human review when required
→ retrieve knowledge
→ draft a response
→ pause for final response review when required
→ resolve or escalate the ticket
→ return a final result
```

This is a manual smoke test. It is not a DeepEval metric evaluation yet.

## Why `main.py` Was Run

`main.py` is the command-line entry point of the open-source agent.

It does the following:

1. Calls `build_graph()` to create the LangGraph workflow.
2. Asks the tester for the customer ID and customer message.
3. Sends those values into the graph.
4. Handles human-review interruptions.
5. Resumes the graph after each human decision.
6. Prints the final status and response.

The important execution line is:

```python
result = graph.invoke(ticket_input, config=config)
```

This sends the test input into the real agent workflow.

## Why the Agent Needs a Customer ID

`main.py` asks for a customer ID because the agent state contains a `customer_id` field.

The ID is used to create a workflow thread identifier:

```python
thread_id = f"{customer_id}-{uuid.uuid4().hex[:8]}"
```

It is also included in the input state:

```python
ticket_input = {
    "customer_id": customer_id,
    "customer_message": customer_message,
}
```

The customer ID is used for ticket identification, thread naming, and checkpoint context. The current agent does not use it to search a real customer database.

For testing, a dummy ID such as the following is sufficient:

```text
TEST_001
```

If an incorrect customer ID is entered, the agent still processes the customer message. The ID will only be stored or displayed incorrectly; it does not change the classification result.

## Input Used in the Smoke Test

The following values were entered:

```text
Customer ID: CUST_1001
```

```text
Customer message: I was charged twice for my subscription and I want a refund.
```

The customer message is the important functional input. It represents a billing and refund request.

## What the Agent Does With the Customer Message

The workflow sends the customer message to the classification function:

```text
customer message
→ classify_with_llm()
→ Groq model
→ TicketClassification result
→ shared agent state
```

The classification function asks the model to identify:

- category
- intent
- priority
- sentiment
- confidence
- rationale

## Classification Result

For the smoke-test message, the agent produced:

```text
category: billing
intent: refund_request
priority: high
sentiment: negative
confidence: 0.95
```

The model also produced a rationale explaining that the customer reported a duplicate subscription charge and requested a refund.

## Where the Allowed Keys and Values Come From

The allowed classification keys and values are defined in `src/models.py` using the `TicketClassification` Pydantic model.

### Category Values

```python
category: Literal["billing", "technical", "order", "account", "general"]
```

The model must return one of these category values.

### Intent Values

```python
intent: Literal[
    "refund_request",
    "payment_issue",
    "bug_report",
    "password_reset",
    "order_status",
    "account_access",
    "complaint",
    "general_question",
    "other",
]
```

The model must return one of these intent values.

### Priority Values

```python
priority: Literal["low", "medium", "high", "urgent"]
```

### Sentiment Values

```python
sentiment: Literal["positive", "neutral", "negative", "frustrated"]
```

### Other Classification Fields

```python
confidence: float
rationale: str
```

The model chooses the classification values based on the customer message. The Pydantic model checks that the returned values use the expected structure and allowed types.

The Python workflow does not manually set `billing`, `refund_request`, `high`, or `negative` for this test. The model returns those values, and the workflow stores them in the shared state.

## How the First Approval Works

After classification, the `approval_gate` checks whether the ticket needs human review.

Human review is required when any of these conditions is true:

```text
priority is high or urgent
classification confidence is below 0.70
category is billing or account
```

The smoke-test ticket had:

```text
priority: high
category: billing
```

Therefore, the agent paused at the first human-review gate.

The first review asked the human to check:

```text
Is the ticket classification correct?
Should the ticket continue through the normal route or be escalated?
```

The response entered was:

```json
{"decision": "approved", "notes": "Proceed"}
```

This means the classification was accepted and the ticket could continue.

The response was stored as:

```text
approval_decision = approved
approval_notes = Proceed
```

The routing logic then checked the decision. Because the decision was not `escalate` and the intent was supported, the workflow continued to knowledge retrieval.

## Knowledge Retrieval and Drafting

The retrieval node searched the knowledge base using:

- the customer message
- the classified category
- a request for the top three relevant documents

The retrieved knowledge was then passed to the resolution model together with:

- customer ID
- customer message
- category
- intent
- priority
- sentiment
- approval notes
- retrieved knowledge

The resolution model generated a draft response. The draft explained that the duplicate charge would need to be verified and asked for account and payment details.

## How the Second Approval Works

After the draft was created, the `final_review_gate` checked whether the final response needed human review.

Final review is required when any of these conditions is true:

```text
the model flags escalation
resolution confidence is below 0.80
priority is high or urgent
category is billing or account
```

The smoke-test ticket again matched the review conditions because it was:

```text
priority: high
category: billing
```

Therefore, the agent paused a second time.

The second review asked the human to decide whether the drafted response should be:

```text
approved
edited
escalated
```

The response entered was:

```json
{"decision": "approve", "notes": "Proceed"}
```

This means the draft was accepted without changes and should be used as the final response.

The second approval is different from the first approval:

```text
First approval  → checks classification and routing
Second approval → checks the drafted final response
```

## How the Workflow Finished

After the second approval, the workflow checked whether escalation was needed.

The value was:

```text
needs_escalation: False
```

Because escalation was not requested, the graph moved to the `resolve_case` node.

That node set:

```text
status: resolved
```

`main.py` then detected that there were no more interruptions and printed the final result.

The final output was:

```text
Status: resolved
```

This is how we know the workflow reached its final node successfully.

## Smoke-Test Result

The smoke test confirmed:

- The project dependencies installed successfully.
- The agent started successfully.
- The Groq connection worked.
- The customer message was accepted.
- The ticket was classified.
- The first human-review gate worked.
- Knowledge retrieval and response drafting worked.
- The second human-review gate worked.
- The final response was produced.
- The workflow ended with `status: resolved`.
- No runtime error occurred during the completed run.

## What This Test Did Not Do

This test did not:

- issue a real refund
- search a real customer account
- validate DeepEval metrics
- compare expected and actual agent behaviour
- test multiple positive and negative scenarios

It only confirmed that the existing open-source agent can run successfully with Groq from start to finish.

## Next QA Stage

After this smoke test, the next work is to:

1. Record the input, classifications, approvals, final output, and status.
2. Inspect only the files involved in this flow.
3. Create a separate DeepEval evaluation adapter.
4. Prepare QA test cases for different classifications, routes, approvals, escalations, and final responses.
5. Capture the real execution trace.
6. Evaluate the agent using agentic metrics.
