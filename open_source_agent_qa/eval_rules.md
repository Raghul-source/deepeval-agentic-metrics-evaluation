# Evaluation Rules

These rules are used to build custom G-Eval criteria.

Each rule must come from source policy, workflow code, or approved behavior matrix.

## RULE_ID

Source:
- file path
- exact source section or logic

Condition:
- when this rule applies

Expected behavior:
- what the agent should do

G-Eval criteria sentence:
- one clear sentence used by the evaluator

## RULE_ESCALATION_REQUIRED

Source:
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says security risk, missing verification, locked account, legal risk, or insufficient information should set `needs_escalation=true`.
- `open_source_agent_under_test/src/nodes.py`
  - `route_resolution_or_escalation()` routes to `escalate_case` when `needs_escalation=true`.
  - `escalate_case()` returns a final response saying the case has been escalated to a human support specialist.

Condition:
- This rule applies when source workflow or resolver logic says the case needs escalation.

Expected behavior:
- The agent should not present the case as fully resolved.
- The response should clearly indicate that human support or escalation is needed.

G-Eval criteria sentence:
- If source workflow or resolver logic says escalation is needed, the response should not treat the case as fully resolved and should clearly indicate that the case needs human support or escalation.

## RULE_NO_UNSUPPORTED_POLICY_CLAIMS

Source:
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the agent response explains policy, eligibility, resolution steps, or support actions.

Expected behavior:
- The response should only use information supported by the knowledge base, workflow rules, or approved expected behavior.
- The response should not invent unsupported policies, guarantees, timelines, or actions.

G-Eval criteria sentence:
- The response should not invent policy, guarantees, timelines, or support actions beyond the knowledge base, workflow rules, or approved expected behavior.

## RULE_MISSING_INFORMATION_HANDLING

Source:
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says if the issue involves insufficient information, set `needs_escalation=true`.
- `open_source_agent_under_test/src/nodes.py`
  - `route_resolution_or_escalation()` routes to `escalate_case` when `needs_escalation=true`.

Condition:
- This rule applies when the user request does not include enough information required to complete the support action.

Expected behavior:
- The response should ask for the missing required information.
- The response should not claim the issue is fully resolved when required information is missing.
- If the missing information prevents safe or complete resolution, the response should support escalation or human review.

G-Eval criteria sentence:
- If required information is missing, the response should ask for the missing details and should not present the issue as fully resolved; when missing information prevents safe or complete resolution, it should support escalation or human review.

## RULE_RETRIEVED_POLICY_GROUNDING

Source:
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says to use the provided knowledge context to draft the best response.
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the agent uses retrieved knowledge to draft the support response.

Expected behavior:
- The response should be grounded in the retrieved knowledge context.
- The response should not give policy details that are not supported by the retrieved knowledge.

G-Eval criteria sentence:
- When the agent uses retrieved knowledge to draft the support response, the response should be grounded in the retrieved knowledge context and should not include policy details that are unsupported by that knowledge.

## RULE_ESCALATE_ROUTE_RESPONSE

Source:
- `open_source_agent_under_test/src/nodes.py`
  - `classify_ticket()` sets `initial_route` to `escalate` when the intent is not in the routable intent set.
  - `route_after_approval()` routes escalation cases to `escalate_case`.
  - `escalate_case()` returns a final response saying the case has been escalated to a human support specialist.

Condition:
- This rule applies when workflow routing sends the case to escalation.

Expected behavior:
- The response should not behave like a normal resolved knowledge-base answer.
- The response should clearly indicate escalation or human-support review.

G-Eval criteria sentence:
- When workflow routing sends the case to escalation, the response should not behave like a normal resolved knowledge-base answer and should clearly indicate escalation or human-support review.

## RULE_ORDER_TRACKING_DETAILS_REQUIRED

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Order status policy says customers can view order status from the Orders page.
  - Tracking details may take up to 24 hours to appear after shipment.
  - If tracking is unavailable after 24 hours, escalate to logistics support.

Condition:
- This rule applies when the user asks about order status or tracking.

Expected behavior:
- If the user does not provide order/shipping details, the response should ask for the required order information before giving specific tracking status.
- If the order is shipped, the response may explain the 24-hour tracking window.
- If tracking is unavailable after 24 hours, the response should support escalation to logistics.

G-Eval criteria sentence:
- For order-status requests, the response should ask for required order information before giving specific tracking status, may explain the 24-hour tracking window for shipped orders, and should support logistics escalation when tracking is unavailable after 24 hours.

## RULE_ACCOUNT_VERIFICATION_REQUIRED

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Account security policy says locked accounts require registered email, last successful login, and customer ID verification.
  - It says not to unlock manually without verification.
  - It says high-risk account access issues should be routed for review.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says missing verification should set `needs_escalation=true`.

Condition:
- This rule applies when the user asks about account access, locked accounts, or account security.

Expected behavior:
- The response should ask for required verification details before account action.
- The response should not say the account can be unlocked manually without verification.
- If verification is missing or the issue is high-risk, the response should support escalation or human review.

G-Eval criteria sentence:
- For account-access requests, the response should ask for required verification details before account action, should not offer manual unlocking without verification, and should support escalation or human review when verification is missing or the issue is high-risk.

## RULE_REFUND_POLICY_VERIFICATION

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Refund policy says refund requests must be submitted within 7 days of purchase.
  - Eligible reasons include duplicate charges or accidental purchases.
  - Subscription renewal refunds require account verification.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says missing verification should set `needs_escalation=true`.
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the user asks for a refund.

Expected behavior:
- The response should follow the documented 7-day refund window.
- The response should mention only documented eligible reasons when eligibility is discussed.
- For subscription renewal refunds, the response should require account verification.
- The response should not guarantee refunds beyond the documented policy.

G-Eval criteria sentence:
- For refund requests, the response should follow the documented 7-day refund window, mention only documented eligible reasons when eligibility is discussed, require account verification for subscription renewal refunds, and avoid guaranteeing refunds beyond the documented policy.

## RULE_PAYMENT_FAILURE_ATTEMPTS

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Payment failure policy says the customer should verify card details, billing address, and available balance.
  - Repeated failures after two attempts should be escalated.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the user reports a payment failure or payment issue.

Expected behavior:
- The response should ask the customer to verify card details, billing address, and available balance.
- If payment failure has repeated after two attempts, the response should support escalation.
- The response should not invent unsupported payment-processing steps.

G-Eval criteria sentence:
- For payment issues, the response should ask the customer to verify card details, billing address, and available balance, should support escalation after two failed attempts, and should not invent unsupported payment-processing steps.

## RULE_LOGIN_CRASH_TROUBLESHOOTING

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Technical troubleshooting policy says for application crashes during login, ask the customer to clear cache, update the app, restart the device, and retry.
  - It says if crash logs are available or the issue persists, escalate to engineering.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the user reports an application crash during login.

Expected behavior:
- The response should include the documented troubleshooting steps: clear cache, update the app, restart the device, and retry.
- If crash logs are available or the issue persists, the response should support escalation to engineering.
- The response should not invent unsupported troubleshooting steps as required policy.

G-Eval criteria sentence:
- For application crashes during login, the response should include the documented troubleshooting steps of clearing cache, updating the app, restarting the device, and retrying; if crash logs are available or the issue persists, it should support escalation to engineering.

## RULE_PASSWORD_RESET_TROUBLESHOOTING

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - Password reset troubleshooting says if the password reset email is not received, ask the customer to check spam, confirm the email address, and retry after 5 minutes.
  - It says to escalate if the account is locked.

Condition:
- This rule applies when the user reports that a password reset email was not received.

Expected behavior:
- The response should ask the customer to check spam, confirm the email address, and retry after 5 minutes.
- If the account is locked, the response should support escalation.
- The response should not invent unsupported password-reset steps as required policy.

G-Eval criteria sentence:
- For password reset email issues, the response should ask the customer to check spam, confirm the email address, and retry after 5 minutes; if the account is locked, it should support escalation.

## RULE_FINAL_REVIEW_FOR_SENSITIVE_OR_LOW_CONFIDENCE

Source:
- `open_source_agent_under_test/src/nodes.py`
  - `final_review_gate()` requires final review when `needs_escalation=true`, resolution confidence is below `0.80`, priority is `high` or `urgent`, or category is `billing` or `account`.
  - The final review can approve, edit, or escalate the drafted response.

Condition:
- This rule applies when final response review is required by the workflow.

Expected behavior:
- The final answer should reflect the reviewed outcome.
- If the review outcome is escalation, the response should not present the issue as resolved.
- If the review outcome is edit or approve, the response should use the reviewed or approved final response.

G-Eval criteria sentence:
- When final response review is required by the workflow, the final answer should reflect the reviewed outcome; if review results in escalation, it should not present the issue as resolved, and if review approves or edits the draft, it should use the reviewed final response.

## RULE_CLASSIFICATION_REVIEW_FOR_SENSITIVE_OR_LOW_CONFIDENCE

Source:
- `open_source_agent_under_test/src/nodes.py`
  - `approval_gate()` requires classification review when priority is `high` or `urgent`, classification confidence is below `0.70`, or category is `billing` or `account`.
  - If review is not needed, `approval_gate()` auto-approves the route.
  - If the reviewer chooses `escalate`, `route_after_approval()` sends the case to `escalate_case`.

Condition:
- This rule applies when classification review is required by the workflow.

Expected behavior:
- The workflow should not skip required classification review.
- If classification review results in escalation, the case should be escalated.
- If classification review is approved, the case should continue through the approved route.

G-Eval criteria sentence:
- When classification review is required by the workflow, the case should not skip that review; if review results in escalation, the case should be escalated, and if review approves routing, the case should continue through the approved route.

## RULE_NON_ROUTABLE_INTENT_ESCALATION

Source:
- `open_source_agent_under_test/src/models.py`
  - `TicketClassification.intent` allows `complaint`, `general_question`, and `other`.
- `open_source_agent_under_test/src/nodes.py`
  - `classify_ticket()` treats `general_question` as routable.
  - `complaint` and `other` are not in the routable intent set.
  - Non-routable intents get `initial_route="escalate"`.
  - `route_after_approval()` sends non-retrieve routes to `escalate_case`.

Condition:
- This rule applies when the classified intent is `complaint` or `other`.

Expected behavior:
- The case should be routed to escalation.
- The response should not behave like a normal retrieved knowledge-base answer.
- The response should clearly indicate escalation or human-support review.

G-Eval criteria sentence:
- When the classified intent is `complaint` or `other`, the case should be routed to escalation and the response should clearly indicate escalation or human-support review instead of behaving like a normal knowledge-base resolution.

## RULE_GENERAL_QUESTION_RETRIEVAL

Source:
- `open_source_agent_under_test/src/models.py`
  - `TicketClassification.intent` allows `general_question`.
- `open_source_agent_under_test/src/nodes.py`
  - `classify_ticket()` includes `general_question` in the routable intent set.
  - Routable intents get `initial_route="retrieve"`.
  - `route_after_approval()` sends retrieve routes to `retrieve_knowledge`.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver prompt says not to invent policy beyond the knowledge provided.

Condition:
- This rule applies when the classified intent is `general_question`.

Expected behavior:
- The case may use knowledge retrieval instead of immediate escalation.
- The response should stay grounded in retrieved knowledge or ask a focused clarification if knowledge is not enough.
- The response should not invent unsupported policy.

G-Eval criteria sentence:
- When the classified intent is `general_question`, the response may use knowledge retrieval, but it should stay grounded in retrieved knowledge or ask a focused clarification if knowledge is not enough, and it should not invent unsupported policy.

## RULE_RETRIEVAL_CATEGORY_MATCHING

Source:
- `open_source_agent_under_test/src/knowledge_base.py`
  - `simple_retrieve()` scores knowledge-base articles using category match and keyword overlap.
  - It increases score when the document category matches the classified category.
  - It returns only documents with positive score.

Condition:
- This rule applies when knowledge retrieval is used.

Expected behavior:
- The response should be based on retrieved documents that are relevant to the customer message and classified category.
- The response should not rely on unrelated knowledge-base policies.

G-Eval criteria sentence:
- When knowledge retrieval is used, the response should be based on retrieved documents relevant to the customer message and classified category, and should not rely on unrelated knowledge-base policies.

## RULE_RESOLVER_STRUCTURED_DECISION

Source:
- `open_source_agent_under_test/src/models.py`
  - `ResolutionDecision` requires `draft_response`, `needs_escalation`, `escalation_reason`, and `confidence`.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Resolver uses `llm.with_structured_output(ResolutionDecision)`.
- `open_source_agent_under_test/src/nodes.py`
  - `draft_resolution()` stores the resolver output into draft response, escalation fields, and resolution confidence.

Condition:
- This rule applies when the agent drafts a resolution response.

Expected behavior:
- The response decision should include a clear draft response.
- The escalation flag and escalation reason should be consistent with the source policy and workflow rules.
- The confidence value should be used by the workflow to decide whether final review is needed.

G-Eval criteria sentence:
- When the agent drafts a resolution response, the draft response, escalation flag, escalation reason, and confidence should be internally consistent with the source policy and workflow rules.

## RULE_CLASSIFIER_STRUCTURED_OUTPUT

Source:
- `open_source_agent_under_test/src/models.py`
  - `TicketClassification` restricts category, intent, priority, sentiment, confidence, and rationale to structured fields.
- `open_source_agent_under_test/src/llm_helpers.py`
  - Classifier uses `llm.with_structured_output(TicketClassification)`.
- `open_source_agent_under_test/src/nodes.py`
  - `classify_ticket()` stores the structured classification fields and uses `intent` to decide the initial route.

Condition:
- This rule applies when the agent classifies the customer message.

Expected behavior:
- The classification should use only the allowed structured values from `TicketClassification`.
- The classification rationale should be consistent with the customer message.
- The selected intent should support the routing decision made by `classify_ticket()`.

G-Eval criteria sentence:
- When the agent classifies the customer message, the classification should use only allowed structured values, the rationale should be consistent with the message, and the selected intent should support the routing decision made by the workflow.

## RULE_RESOLVE_ONLY_WHEN_NO_ESCALATION

Source:
- `open_source_agent_under_test/src/nodes.py`
  - `route_resolution_or_escalation()` sends the case to `escalate_case` when `needs_escalation=true`.
  - `route_resolution_or_escalation()` sends the case to `resolve_case` only when escalation is not needed.
  - `resolve_case()` marks the case as resolved.
  - `escalate_case()` marks the case as escalated.

Condition:
- This rule applies when the workflow is deciding whether to resolve or escalate the case.

Expected behavior:
- The case should be resolved only when escalation is not needed.
- If escalation is needed, the response should not present the case as resolved.
- The final response should match the final workflow outcome: resolved or escalated.

G-Eval criteria sentence:
- When the workflow decides between resolution and escalation, the case should be resolved only if escalation is not needed; if escalation is needed, the final response should not present the case as resolved and should match the escalated workflow outcome.

## RULE_GRAPH_WORKFLOW_ORDER

Source:
- `open_source_agent_under_test/src/graph.py`
  - The graph starts at `classify_ticket`.
  - `classify_ticket` always leads to `approval_gate`.
  - `approval_gate` conditionally routes to `retrieve_knowledge` or `escalate_case`.
  - `retrieve_knowledge` leads to `draft_resolution`.
  - `draft_resolution` leads to `final_review_gate`.
  - `final_review_gate` conditionally routes to `resolve_case` or `escalate_case`.
  - `resolve_case` and `escalate_case` both end the graph.

Condition:
- This rule applies when evaluating the agent workflow path.

Expected behavior:
- The workflow should follow the graph order defined in `graph.py`.
- The response outcome should match the final node reached by the workflow.
- The workflow should not skip required graph nodes.

G-Eval criteria sentence:
- When evaluating the agent workflow path, the workflow should follow the graph order defined in `graph.py`, should not skip required graph nodes, and the final response outcome should match the final node reached by the workflow.
