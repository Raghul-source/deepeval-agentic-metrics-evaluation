# Implementation Plan

## Open-Source Agent Under Test

Repository: https://github.com/niti007/langgraph-customer-support-agent

## Open-Source Agent Evaluation Plan

### Completed inspection

1. `config.py`
   - Checked API-key loading.
   - Identified the model provider and model.
   - Checked model parameters such as temperature.
   - Confirmed how the model is configured.

2. `models.py`
   - Checked the structured output models.
   - Reviewed `Literal` values for category and intent.
   - Reviewed data types such as `float`, `bool`, and `str`.
   - Identified required fields returned by the model.

3. `state.py`
   - Identified the state object used by the workflow.
   - Recorded the data passed between agent steps.
   - Noted fields such as ticket input, category, intent, priority, context, response, approval, and escalation.

### Remaining inspection

4. `knowledge_base.py`

   - Understand how knowledge is stored.
   - Identify how retrieval works.
   - Record the retrieval input and returned context.

5. `llm_helpers.py`

   - Find the model-call functions.
   - Read the prompts sent to the model.
   - Check how the model response is converted into structured data.

6. `nodes.py`

   - Identify every workflow step.
   - Record classification, retrieval, drafting, approval, escalation, and resolution functions.
   - Identify which functions call the model and which update the state.

7. `graph.py`

   - Understand the complete execution order.
   - Identify the agent entry point and final output.
   - Find the correct location for tracing or callback integration.

### Implementation after inspection

8. Create a separate evaluation adapter in the existing DeepEval project.

   - Do not modify the open-source agent source code.
   - Call the agent through its existing entry point.
   - Capture the final response and agent execution trace.

9. Create QA test data for:

   - Correct classification
   - Incorrect classification
   - Missing information
   - Knowledge retrieval failure
   - Incorrect response
   - High-priority escalation
   - Approval-gate failure
   - Unnecessary steps

10. Connect the captured execution data to DeepEval.

11. Evaluate the real agent using:

```text
TaskCompletionMetric
ToolCorrectnessMetric
ArgumentCorrectnessMetric
StepEfficiencyMetric
PlanAdherenceMetric
PlanQualityMetric
```

12. Record for every test case:

```text
input
expected result
actual result
actual tool calls
metric score
pass/fail status
reason
```

13. Analyse failed cases and identify the root cause.

14. Document the defects, evidence, and recommendations in the README.

15. If a fix is required, apply it separately and run the same test cases again to verify the result.


## Configuration File (`config.py`) Inspection Checklist

- **Environment Key Loading:** Verify that API keys are loaded dynamically from environment variables (e.g., using `os.environ` and `.env`) rather than being hardcoded, ensuring security and proper environment setup.
- **Model Parameters:** Check whether the model's hyperparameters (like `temperature`) are constant or dynamic. A constant value (e.g., `temperature=0`) ensures deterministic, repeatable outputs required for stable testing.
- **Framework & Library Identification:** Identify the client library being used to instantiate the model (e.g., `ChatOpenAI` from `langchain_openai`) to determine the correct corresponding tracing and callback integration techniques.

## `models.py` Inspection Checklist

When a developer hands you `models.py`, check these exact three things:

- **Step 1: Inspect `Literal` Boundaries**
  - *What to look at:* `category: Literal[...]` and `intent: Literal[...]`.
  - *QA Action:* Compare every string inside the brackets against your test dataset CSV/JSON. Ensure your test cases use the exact same words (e.g., `"technical"` vs `"tech"`).
- **Step 2: Inspect Data Types**
  - *What to look at:* `confidence: float`, `needs_escalation: bool`, `rationale: str`.
  - *QA Action:* Note these types so your test assertions know what to expect (e.g., knowing `confidence` is a number allows you to write math checks like `assert confidence > 0.8`).
- **Step 3: Inspect Required Fields**
  - *What to look at:* Check which fields are mandatory so you know what data the LLM is guaranteed to return for every single test case.

## Graph State File (`state.py`) Inspection Checklist & Notes

### What This File Does

- **Defines the Pipeline Memory (`SupportState`):** Acts as the centralized shared dictionary (built using `TypedDict, total=False`) that flows through every node of the LangGraph agent workflow like a relay baton.
- **Manages Optional State Initialization:** `total=False` ensures that keys are optional when the graph starts, preventing structural runtime crashes (like a `KeyError`) if a node reads a key before it has been populated.

---

### What a QA Engineer Needs to Inspect

- **Inspect State Schema & Key Names:**
  - Verify exact key names (e.g., `customer_message`, `intent`, `category`, `draft_response`, `needs_escalation`) so your test assertions and evaluation scripts look up the correct dictionary keys without typos.
- **Inspect Complex Data Structures (`retrieved_docs`):**
  - Locate complex types like `retrieved_docs: List[Dict[str, Any]]`.
  - **QA Action:** Ensure your test code loops through the list and accesses dictionary keys (e.g., `doc["content"]`) rather than treating retrieved documents as a plain string.
- **Inspect Data Types for Threshold & Conditional Assertions:**
  - Verify types like `resolution_confidence: float` and `needs_escalation: bool`.
  - **QA Action:** Confirm these types match your test assertions so you can safely run mathematical thresholds or boolean checks (e.g., `assert result["resolution_confidence"] >= 0.8` or `assert result["needs_escalation"] is False`) without causing Python `TypeError` crashes.

---

### How State Testing Works (The Relay Baton Concept)

1. **Input:** The test script triggers the graph with an initial payload (e.g., `graph.invoke({"customer_message": "..."})`), creating the blank state.
2. **Operations:** Each specialized node (Classifier, Retriever, Resolution) reads, updates, and passes the single dictionary forward.
3. **Capture & Assert:** The graph returns the fully filled `SupportState` dictionary. Your test script captures this return value and asserts rules against its exact keys and data types to automate quality checks.

## Graph Assembly File (`graph.py`) Inspection Checklist & Notes

### What This File Does

- **Defines the Overall Architecture:** Acts as the blueprint of the agent's execution workflow, assembling nodes, linear edges, and conditional routing branches.
- **Sets Up Persistence:** Connects a SQLite database checkpointer so state snapshots are saved after every step.
- **Defines the Entry Point & Construction:** `build_graph()` constructs the graph, where `START` connects directly to `"classify_ticket"` as the first node that executes when the graph starts.

---

### What a QA Engineer Needs to Inspect

- **Inspect the Entry Point:**
  - **Script lines:** `def build_graph(...)`, `builder.add_edge(START, "classify_ticket")`
  - **QA Action:** Understand that `build_graph()` initializes the graph architecture and `"classify_ticket"` is the absolute starting point where test executions begin.
- **Inspect Node Registration:**
  - **Script lines:** `builder.add_node("...", ...)`
  - **QA Action:** Verify that every functional node from `src.nodes` is explicitly registered. This acts as your test plan blueprint to ensure all processing and human-review gates are covered.
- **Inspect Edges & Path Coverage (Linear vs. Conditional):**
  - **Script lines:** `builder.add_edge(...)` and `builder.add_conditional_edges(...)`
  - **QA Action:** Map out all decision points and write separate test cases for **every possible path** (e.g., testing both branches of the approval gate).
- **Inspect Persistence & SQLite Connection:**
  - **Script lines:** `conn = sqlite3.connect(db_path, check_same_thread=False)`, `checkpointer = SqliteSaver(conn)`
- **QA Action:** Confirm SQLite persistence is present to support state capture and human-in-the-loop pause/resumption testing. *(Note: `check_same_thread=False` only allows the connection to be shared across threads; it does not automatically make parallel test execution safe from race conditions.)*

## Knowledge Base File (`knowledge_base.py`) Inspection Checklist & Notes

### What This File Does

- **Stores Support Policies:** Holds hardcoded reference articles (`KNOWLEDGE_BASE`) containing an `id`, `category`, `title`, and `content`.
- **Executes Scoring & Retrieval:** Implements `simple_retrieve()` to score articles via category matching and keyword overlap, sorting and returning the top-$k$ results (`top_k=3`) to the graph state (`retrieved_docs`) for the resolution node.

---

### What a QA Engineer Needs to Inspect

- **Inspect Categories vs. Model Literals:**
  - **Script lines:** `KNOWLEDGE_BASE` article dictionaries containing `"category": "..."`
  - **QA Action:** Ensure every category defined here matches the allowed string Literals in `models.py` and your test cases. If they don't match, retrieval still works, but the article does not receive the `+3` category-match bonus.

- **Inspect Scoring Logic (Category Comparison & Weighting):**
  - **Script lines:** `if doc["category"] == category: score += 3`
  - **QA Action:** Understand that the script compares the ticket category against the article category, adding an artificial weight of `+3` to prioritize category matches over pure keyword text matching.

- **Inspect Keyword Overlap & Word Matching:**
  - **Script lines:**

```python
query_words = set(query.lower().split())
content_words = set((doc["title"] + " " + doc["content"]).lower().split())
overlap = len(query_words.intersection(content_words))
score += overlap
```

  - **QA Action:** Ensure test queries share actual words with KB articles to accumulate score points. *(Note: This simplified custom script blindly counts all matching words including common filler words like "a", "the", or "is" without stop-word removal).*

- **Inspect Output Limits (Top-K & Filtering):**
  - **Script lines:** `docs = [doc for score, doc in scored if score > 0][:top_k]` where `top_k = 3`
- **QA Action:** Verify that articles with a score of zero (completely irrelevant) are dropped, and ensure test assertions expect a maximum of 3 retrieved documents (`top_k = 3`).

## LLM Helpers File (`llm_helpers.py`) Inspection Checklist & Notes

### What This File Does

- **Binds Structured Outputs:** Uses the shared LLM client from `config.py` to force LLM responses into specific Pydantic schemas (`TicketClassification` and `ResolutionDecision`).
- **Implements LLM Helper Functions:** Defines `classify_with_llm()` to parse raw customer messages into structured classification data and `resolve_with_llm()` to combine state data, retrieved knowledge base articles, and safety rules into an LLM prompt for resolution drafting.

---

### What a QA Engineer Needs to Inspect

- **Inspect Structured Output Binding & Schema Alignment:**
  - **Script lines:**

```python
classifier = llm.with_structured_output(TicketClassification)
resolver = llm.with_structured_output(ResolutionDecision)
```

  - **QA Action:** Verify that the wrapper models (`TicketClassification`, `ResolutionDecision`) match the master Pydantic class definitions in `models.py`. If field names mismatch, LLM parsing will crash during test execution.

- **Inspect Classification Prompt & Execution:**
  - **Script lines:**

```python
def classify_with_llm(customer_message: str) -> TicketClassification:
    prompt = f"...\nTicket:\n{customer_message}"
    return classifier.invoke(prompt)
```

  - **QA Action:** Verify that raw customer message strings are passed directly into the prompt template and that `.invoke(prompt)` correctly returns a structured classification object.

- **Inspect Resolution Context Mapping & State Fields:**
  - **Script lines:**

```python
kb_text = "\n\n".join([...])
prompt = f"...\nCustomer ID: {state.get('customer_id', '')}\nMessage: {state.get('customer_message', '')}\n..."
return resolver.invoke(prompt)
```

  - **QA Action:** Verify that every required state field (`customer_id`, `customer_message`, `category`, `intent`, `priority`, `sentiment`, `approval_notes`, and `retrieved_docs`) is correctly extracted from `SupportState` and injected into the prompt so the LLM has full context to write a response.

  - `retrieved_docs` is converted into `kb_text`, and `kb_text` is injected into the prompt.

- **Inspect Escalation Rules & Automated Human Review Triggers:**
  - **Script lines:**

```python
# Rules in resolver prompt:
# - If the issue involves security risk, missing verification, locked account, legal risk,
#   or insufficient information, set needs_escalation=true.
```

  - **QA Action:** Write test cases targeting these specific risk conditions, such as locked accounts or insufficient information, to verify that the LLM automatically sets `needs_escalation=True`.

  - When `needs_escalation=True`, the flow is:

```text
resolver
→ draft_resolution
→ final_review_gate
→ route_resolution_or_escalation()
→ escalate_case
```

  This routes the ticket to escalation through the final review flow, not the first `approval_gate`.

## Nodes and Execution Logic File (`nodes.py`) Inspection Checklist & Notes

### What This File Does

- **Defines Workflow Execution Logic:** Contains all core processing functions (nodes) that execute sequentially or conditionally when the agent runs.
- **Manages Human-in-the-Loop Gates:** Uses LangGraph's `interrupt()` function to pause execution and request human review at critical checkpoints (`approval_gate` and `final_review_gate`).
- **Executes Routing & Retrieval Integration:** Handles classification routing, calls `simple_retrieve()`, and manages resolution or escalation outcomes.

---

### What a QA Engineer Needs to Inspect

- **Inspect Classification Routing (`classify_ticket`):**

  - **Script lines:**

    ```python
    result = classify_with_llm(state["customer_message"])
    initial_route = "retrieve" if result.intent in routable_intents else "escalate"
    ```

  - **QA Action:** Verify that customer messages are correctly passed to the LLM classifier and that valid intents route to knowledge retrieval while unhandled intents route straight to escalation.

- **Inspect Human-in-the-Loop Gates (`approval_gate` and `final_review_gate`):**

  - **First gate (`approval_gate`) checks:**

    ```python
    state.get("priority") in ["high", "urgent"]
    or state.get("classification_confidence", 0) < 0.70
    or state.get("category") in ["billing", "account"]
    ```

  - **Final gate (`final_review_gate`) checks:**

    ```python
    state.get("needs_escalation", False)
    or state.get("resolution_confidence", 0) < 0.80
    or state.get("priority") in ["high", "urgent"]
    or state.get("category") in ["billing", "account"]
    ```

  - **QA Action:** Test boundary conditions for automatic versus manual reviews. Verify that high priorities, low confidence, or sensitive categories trigger `interrupt()` and wait for internal human operator input such as approve, edit, or escalate.

- **Inspect Knowledge Retrieval Integration (`retrieve_knowledge`):**

  - **Script lines:**

    ```python
    docs = simple_retrieve(
        query=state["customer_message"],
        category=state.get("category", "general"),
        top_k=3,
    )
    ```

  - **QA Action:** Confirm that the customer message and category are correctly forwarded to `simple_retrieve()` and stored in `state["retrieved_docs"]` for downstream LLM resolution.

- **Inspect Resolution and Escalation State Writing (`draft_resolution`, `final_review_gate`, `route_resolution_or_escalation`, and `escalate_case`):**

  - **Script lines:**

    ```python
    decision = resolve_with_llm(state)
    ```

    ```python
    escalation_msg = (
        "Your case has been escalated to a human support specialist. "
        f"Reason: {state.get('escalation_reason', 'Needs manual review')}."
    )
    ```

  - **QA Action:** Verify that LLM resolution decisions, draft responses, and escalation flags are correctly saved back to the state dictionary. Test escalation paths to ensure response messages include the specific escalation reason, or use `Needs manual review` when no reason is available.

  - When `needs_escalation=True`, the flow is:

    ```text
    draft_resolution
    → final_review_gate
    → route_resolution_or_escalation()
    → escalate_case
    ```
