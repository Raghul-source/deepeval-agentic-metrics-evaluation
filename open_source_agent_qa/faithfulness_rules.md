# Custom Faithfulness Trial: Rules and Validation

This guide describes the custom implementation developed in [whole_answer_faithfulness_trial.py](whole_answer_faithfulness_trial.py) and now copied into the main evaluator, [open_source_agent_evaluation.py](open_source_agent_evaluation.py). It does not describe the unchanged built-in DeepEval metric. Moving the implementation into the main evaluator does not remove the validation limits documented below.

QA/evaluation engineers define evaluation rules with product or domain experts. The model applies the judging instructions; engineers implement and test the calculation. These custom rules were developed during this project's investigation. They still need validation; documenting a rule does not establish that it is correct for every use case or that the model follows it reliably.

## What this trial measures

The trial checks factual support while giving the judge the complete answer for meaning. It uses extracted document facts and recorded workflow outcomes as evidence. It does not measure answer helpfulness, relevance, or task completion by itself. Adding action evidence extends the scope beyond document-only faithfulness.

The support agent being tested is the downloaded LangGraph agent, called through [the adapter](open_source_agent_adapter.py). The shipment tools in [the separate baseline agent](../baseline/agent.py) are not connected to this agent.

## Current judging and scoring rules

| Area | Current rule | Effect and implementation limit |
| --- | --- | --- |
| Understanding | Read the complete answer before judging each point. | Prompt instruction; code cannot verify that the judge understood it. |
| Meaning | Preserve conditions, uncertainty, timing, negation and references. | Prompt instruction; incorrect interpretations remain possible. |
| Paraphrasing | Accept different wording when evidence supports the same meaning. | Exact word matching is not the judging criterion. |
| Evidence | Use facts extracted from retrieved documents for policies, procedures, timelines and documented capabilities. | The judge receives extracted facts; this adds a possible information-loss step. |
| Action evidence | Use recorded action results for executed steps and outcomes. | A policy instruction is not confirmation of execution. |
| Internal actions | Internal escalation does not prove external notification or human receipt. | The supplied records contain status and executed steps, not proof of external delivery. |
| Answer as evidence | The answer cannot prove its own factual claims. | Supplied text is data, not instructions or independent proof. |
| Customer question | The complete answer is supplied to the judge, but the customer question is not included in these custom judging prompts. | Although the runner sets `LLMTestCase.input`, this trial does not use it as evidence. Handling repeated customer-reported details remains unresolved. |
| Future actions | A future capability needs evidence it exists, but not proof it has already executed. | A promise of a specific operation remains checkable even if conditional. |
| Coverage | Review every distinct factual point, including promises and capabilities. | Requested in the prompt; there is no automated completeness check for omitted points. |
| Original wording | Copy each excerpt exactly from the answer. | Code rejects excerpts that are not substrings of the answer. This does not prove a fragment preserves the complete meaning. |
| Duplication | Do not repeat or artificially split points to change their weight. | Code rejects exact duplicate excerpts, but cannot detect all overlapping or semantically repeated points. |
| Supported | Supplied evidence establishes the point's complete meaning. | Counts in both the supported count and total factual count. |
| Unsupported | Necessary evidence is missing. | Counts only in the total factual count, unless the second review excludes it. |
| Contradicted | Evidence conflicts with the point. | Counts only in the total factual count. This trial does not give contradictions a larger penalty. |
| Ignored | The point is non-factual conversational wording. | Excluded from both counts; it neither adds nor removes a passing factual point. |
| Explanations | Return evidence and a reason for decisions. | Schema requires these fields; code rejects empty evidence for supported points. It does not independently verify that cited evidence actually supports the point, and reasons are not required to be non-empty. |
| Second review | Reconsider only points initially marked `unsupported`. | Incorrect `supported`, `contradicted` or `ignored` labels are not reconsidered. |
| Second-review changes | Keep `unsupported`, or change to `ignored`. | The second review cannot change a point to `supported` or fix a wrongly accepted fact. |
| Second-review coverage | Return one purpose decision for every supplied point ID. | Code rejects missing, repeated or unexpected point IDs. |
| Mixed wording | Do not hide factual content inside polite wording, an acknowledgment or a recommendation. | First review is instructed to separate parts. Second review keeps the existing point intact and retains `unsupported` if any factual purpose remains. |
| Score calculation | Supported factual points divided by total factual points. | Code calculates the score after the second review. The model does not directly choose the score. |
| Weighting | Every scored point has equal weight. | Point grouping still depends on the judge; different grouping can produce different scores. No severity weighting exists. |
| No factual points | Return `1.0` when all points are ignored. | An explicit custom-code convention, not a result of calculating `0 / 0`. It means no unsupported factual assertions were identified, not that the answer is useful or complete. Whether to instead report this as not assessed requires a separate project decision. |
| Passing threshold | Score at least `0.7` passes this check. | A configuration choice; it is not validated as the correct threshold for this application's risks. |
| Ambiguous claims setting | The runner passes `penalize_ambiguous_claims=True`. | The custom schema has no `borderline` verdict and the custom formula does not read this setting. Do not attribute this trial's deductions to that flag. |
| Task completion | Evaluate task completion separately from factual support. | A clarification or abstention can contain no unsupported facts while leaving the customer's request unanswered. |

## Second-review phrase categories

The model returns purpose labels and an explanation. Code then maps those labels to `ignored` or `unsupported`.

| Phrase category | Current treatment |
| --- | --- |
| `missing_information_acknowledgment` | Ignore an acknowledgment that available information is insufficient, unless a separate factual purpose also occurs in the same point. |
| `clarification_request` | Ignore a request for more details unless factual content or a specific promise is also present. |
| `suggested_next_step` | A recommendation is not itself a claim that an action already happened. Check any factual policy, timeline, capability or guarantee within it. |
| `polite_wording` | Ignore greetings, apologies, thanks and general conversational invitations unless factual content also occurs. |
| `factual_assertion` | Keep the initially unsupported point penalized. |
| `specific_capability_or_promise` | Keep the initially unsupported point penalized, including specific future or conditional operational promises. |
| `completed_action_claim` | Keep the initially unsupported point penalized when execution support is missing. |
| Statement about missing knowledge-base information | Classify a statement of the answer's information limits as an acknowledgment. Do not add a factual label solely because it mentions the assistant or its knowledge base. This does not excuse separate claims about the outside world or completed searches. |
| Multiple categories together | If any of the three factual categories occurs, retain `unsupported`; otherwise assign `ignored`. An acknowledgment label alone does not override another factual label. |

## Calculation examples

| Reviewed points | Calculation | Meaning |
| --- | --- | --- |
| Two supported, one unsupported, two ignored | `2 / 3 = 0.667` | Ignored points do not increase the score. |
| Zero supported, one unsupported, two ignored | `0 / 1 = 0` | One remaining unsupported point gives zero, regardless of ignored wording. |
| All points ignored | Explicit fallback: `1.0` | No factual points assessed; this is not evidence of task success. |

## Validation audit: 26 October 2026

The latest controlled experiment reused the same 10 saved answers, extracted document facts, action records and first-stage judgments. Only the second review ran again, using `openai/gpt-oss-20b` through Groq. This isolates that stage; it is not a fresh end-to-end validation or proof of repeatability on future cases.

The following summary comes from the saved local artifact `whole_answer_trial_knowledge_review_results.json`. Experiment output files are not required for the reader to understand the findings below.

| Check | Audit finding | Validation status |
| --- | --- | --- |
| Score arithmetic | Stored scores match the supported-count / factual-count formula. | Verified for the 10 saved cases and offline execution checks. |
| Preservation | Saved answers, documents, action records and initially non-unsupported decisions stayed unchanged during the second-review experiment. | Verified. |
| Case 005 | Missing verification details became an ignored information-limit acknowledgment. | Targeted check passed in this run. |
| Case 007 | Insufficient information plus a requested next step became ignored. | Targeted check passed in this run. |
| Case 010, acknowledgment | The missing-knowledge-base-details sentence became ignored. | Targeted check passed in this run. |
| Unsupported refund timeline and fraud-team statement | These remained unsupported. | Negative controls passed in this run. |
| Case 001, seven-day eligibility | The first judge accepted the statement that this charge is within seven days, citing a general seven-day policy. The policy does not establish this customer's charge date. | Incorrect supporting inference; untouched by the second review because the label was already supported. |
| Case 003, escalation reason | The first judge used a policy about login crashes to support requirements for an upload crash, and described a rule about logs being available as if it covered missing logs. | The cited evidence does not establish that complete reason. Internal escalation itself is supported separately. |
| Case 004, shipment lookup | Tracking-window evidence was treated as proof of a shipment lookup and delivery-estimate capability. The active agent has no connected lookup tool. | Incorrect supporting inference; second review does not revisit supported points. |
| Customer-reported facts | Case 001 penalizes repetition of the customer's report, while case 002 accepts a customer-specific purchase age without that age appearing in the supplied policy evidence. | Source-handling inconsistency remains; do not treat every saved verdict as a reference answer. |
| General offer versus specific promise | Case 010's final sentence is still classified as a capability promise. | Unresolved judging boundary; its deduction is not established as correct merely because the model returned it. |
| No-factual-points fallback | Code explicitly returns `1.0`. | Implementation verified; appropriateness as a reported outcome is a project decision, not settled by these tests. |
| Completeness, grouping and severity | Code does not prove all relevant points were covered, grouped consistently or weighted appropriately for harm. | Not fully validated. |
| Generalization and repeatability | The same saved cases have been used to develop and inspect the rules. | New held-out cases and repeated runs have not established reliability. |

The rule set and judge are therefore **not fully validated**. Correct arithmetic and several corrected exclusions do not establish that the complete evaluation is reliable.

## Why case 010 still has a deduction

The saved answer says it lacks specific service details, asks which aspects interest the customer, and ends with:

> That way I can provide the most accurate information or direct you to the right resources.

| Part of the answer | Latest label | Explanation |
| --- | --- | --- |
| Acknowledgment of missing knowledge-base details | Ignored | The new information-limit rule covers it. |
| Request to clarify the customer's interest | Ignored | A question, not a factual assertion. |
| Final offer quoted above | Unsupported | The reviewer assigns `specific_capability_or_promise`. |

The acknowledgment rule does not automatically exclude a different sentence that the judge classifies as a specific promise. The remaining calculation is `0 supported / 1 factual point = 0`.

The full-answer context may instead make this a general offer to help after clarification. The saved judgment does not settle that interpretation. Earlier claims that this answer definitely deserves `1.0` were too certain: it would receive `1.0` under the current fallback **if** the final offer were also judged non-factual. That is a conditional outcome, not a verified reference score.

## How to validate these rules further

| Validation question | Required check |
| --- | --- |
| Are the intended exclusions clear? | Establish expected labels for general assistance, information limits, clarification, recommendations and mixed factual promises. Preserve the complete answer when deciding them. |
| Are genuine errors retained? | Include unsupported timelines, invented capabilities, false completed-action claims and contradictions as negative controls. |
| Does the evidence actually support the verdict? | Check the exact source and its conditions, not only the presence of an evidence explanation. |
| Is the action evidence sufficient? | Match records to the exact case/run; distinguish internal status changes from external outcomes. |
| Are cases with no factual points reported appropriately? | Decide and document whether to retain `1.0` or report a separate not-assessed outcome. Do not change the convention silently. |
| Are scores stable and useful? | Compare point coverage and grouping across repeated runs; assess the threshold and consequences of serious unsupported statements. |
| Do rules generalize? | Evaluate on independently established reference decisions and held-out answers that were not used to tune the prompt. Automate those regression checks once the reference decisions are settled. |

## References

- [DeepEval Faithfulness documentation](https://deepeval.com/docs/metrics-faithfulness): the LLM-judge approach checks claims against retrieved facts and calculates their faithful proportion. This trial customizes the judging flow, exclusions, action evidence and score calculation.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents): distinguish what an agent says from the actual outcome in its environment, and validate graders against reliable reference judgments.
