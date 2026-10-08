# Open-Source Agent QA Defect Report

This report documents confirmed QA findings from the open-source LangGraph
customer-support agent evaluation.

## Sources Used for Analysis

These sources were used to confirm the QA findings.

- `evaluation_output.txt` — contains the saved metric results, actual agent
  outputs, failed checks, and trajectory comparison evidence.
- `open_source_agent_test_cases.csv` — contains the test inputs and expected
  values used for comparison.
- `agent_behavior_matrix.md` — defines the expected behavior rules used to
  review whether the CSV expectations are correct.
- `open_source_agent_under_test/src/knowledge_base.py` — contains the support
  policy content used by the agent.
- `open_source_agent_under_test/src/nodes.py` — contains the workflow routing,
  escalation, and review-gate logic.
- `open_source_agent_under_test/src/llm_helpers.py` — contains the classifier
  and resolver prompts used by the agent.

## Summary

| Defect ID | Test Case | Finding Type | Severity | Status | Short Description |
| --- | --- | --- | --- | --- | --- |
| `DEF-TC-001` | `OS_AGENT_TC_003` | TaskCompletionMetric finding | Medium | Needs developer review | For document upload crash, the agent did not fully complete the expected bug-handling flow. |
| `DEF-TC-002` | `OS_AGENT_TC_004` | TaskCompletionMetric finding | Medium | Needs developer review | For order status, the agent asked for missing details but did not complete the order-status resolution. |
| `DEF-TRJ-001` | `OS_AGENT_TC_006` | Deterministic trajectory/state finding | High | Confirmed | For vague account help, the agent should escalate after asking details, but it resolved the case. |
| `DEF-TRJ-002` | `OS_AGENT_TC_007` | Deterministic trajectory/state finding | High | Confirmed | For unsupported support request, the agent should escalate, but it handled it as a normal general question. |

## TaskCompletionMetric Findings

`TaskCompletionMetric` is an LLM-judge-based metric. These findings come from
the saved TaskCompletion report and should be reviewed with the actual agent
output, expected behavior, and source policy before being converted into
developer issues.

### `DEF-TC-001` — `OS_AGENT_TC_003`

- **Input:** `My application crashes whenever I try to upload a document.`
- **Expected:** Request diagnostic details and escalate because required crash
  details are missing.
- **Actual:** Agent gave troubleshooting guidance; `TaskCompletionMetric`
  marked the case as failed.
- **Evidence:** `TaskCompletionMetric` failed in `evaluation_output.txt`.
- **Impact:** Missing crash details may block proper technical investigation.
- **Area to investigate:** Technical crash handling when diagnostic details are
  missing.

### `DEF-TC-002` — `OS_AGENT_TC_004`

- **Input:** `Where is my order and when should it arrive?`
- **Expected:** Ask for order ID/email first, then explain the 24-hour tracking
  window and logistics escalation condition.
- **Actual:** Agent asked for order details; `TaskCompletionMetric` marked the
  case as failed because no actual order status was provided.
- **Evidence:** `TaskCompletionMetric` failed in `evaluation_output.txt`.
- **Impact:** Order-status handling may be judged incomplete when required
  order identifiers are missing.
- **Area to investigate:** Missing-order-detail clarification behavior.

## Custom Trajectory Findings

The custom trajectory evaluation is deterministic. It compares the expected
workflow path and expected state values against the actual workflow path and
state returned by the agent.

### `DEF-TRJ-001` — `OS_AGENT_TC_006`

- **Input:** `Please help me with my account.`
- **Expected:** Ask for missing account details and set
  `needs_escalation=true`.
- **Actual:** Agent asked for account details but returned
  `needs_escalation=false`.
- **Expected trajectory:** `classify_ticket → approval_gate → retrieve_knowledge
  → draft_resolution → final_review_gate → escalate_case`
- **Actual trajectory:** `classify_ticket → approval_gate → retrieve_knowledge
  → draft_resolution → final_review_gate → resolve_case`
- **Evidence:** Failed `trajectory_match` and `escalation_match` in
  `evaluation_output.txt`.
- **Impact:** Account requests with missing verification may be resolved instead
  of escalated.
- **Area to investigate:** Resolver escalation decision for vague account
  requests.

### `DEF-TRJ-002` — `OS_AGENT_TC_007`

- **Input:** `I need help with something that is not covered by the support policies.`
- **Expected:** Classify as `other`, route to `escalate`, and send to human
  support.
- **Actual:** Agent classified as `general_question`, routed to `retrieve`, and
  resolved the case.
- **Expected trajectory:** `classify_ticket → approval_gate → escalate_case`
- **Actual trajectory:** `classify_ticket → approval_gate → retrieve_knowledge
  → draft_resolution → final_review_gate → resolve_case`
- **Evidence:** Failed `trajectory_match`, `intent_match`, `route_match`, and
  `escalation_match` in `evaluation_output.txt`.
- **Impact:** Unsupported requests may be handled as normal general questions.
- **Area to investigate:** Classifier/routing behavior for out-of-policy
  requests.

## Evaluation Stability Note

`TaskCompletionMetric` is LLM-judge based, so its score can vary between runs.
The deterministic checks and custom trajectory evaluation are rule-based for
the same actual output and are therefore more stable for workflow defect
tracking.

