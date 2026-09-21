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
