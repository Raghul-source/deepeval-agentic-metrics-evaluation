# Open-Source Agent Behavior Matrix

This matrix is the source of truth for creating and reviewing test cases for the
open-source customer-support agent.

Expected results must be derived from the agent's schemas, workflow rules, and
knowledge-base policies. They must not be copied from the agent's actual output.

## 1. Classification values

### Allowed categories

| Category | Meaning |
| --- | --- |
| `billing` | Refunds, charges, payments, and invoices |
| `technical` | Application or technical problems |
| `order` | Order and delivery status |
| `account` | Login, password, access, and account security |
| `general` | General questions or unsupported/general requests |

### Allowed intents and initial route

| Intent | Meaning | Initial route |
| --- | --- | --- |
| `refund_request` | Customer asks for a refund | `retrieve` |
| `payment_issue` | Payment, charge, or invoice problem | `retrieve` |
| `bug_report` | Customer reports a software problem | `retrieve` |
| `password_reset` | Customer cannot reset or recover a password | `retrieve` |
| `order_status` | Customer asks about an order | `retrieve` |
| `account_access` | Customer cannot access an account or reports account risk | `retrieve` |
| `general_question` | Customer asks a general question | `retrieve` |
| `complaint` | Customer complaint not covered by a routable intent | `escalate` |
| `other` | Unsupported or unclassified request | `escalate` |

The initial route is defined by `nodes.py`. Any intent not in the routable set
is sent to `escalate_case` after the approval gate.

## 2. Knowledge-base policy matrix

These are the documented behaviors from `src/knowledge_base.py`.

| Policy ID | Scenario | Required response behavior | Escalation condition |
| --- | --- | --- | --- |
| `kb_001` | Duplicate or accidental purchase within 7 days | Explain that a refund can be requested within 7 days | Follow verification rules for subscription renewals |
| `kb_001` | Duplicate or accidental purchase after 7 days | Explain that it is outside the documented 7-day refund period | Do not claim that a refund is guaranteed |
| `kb_001` | Subscription renewal refund | Request account verification before processing | Escalate if verification or required information is missing |
| `kb_002` | Payment failure | Ask the customer to verify card details, billing address, and available balance | Escalate repeated failures after two attempts |
| `kb_003` | Application crashes during login | Ask the customer to clear cache, update the app, restart the device, and retry | Escalate if crash logs are available or the issue persists |
| `kb_004` | Password-reset email not received | Ask the customer to check spam, confirm the email address, and retry after five minutes | Escalate if the account is locked |
| `kb_005` | Order is marked shipped | Provide a tracking window of 24 hours | Escalate to logistics if tracking is unavailable after 24 hours |
| `kb_006` | Account is locked | Verify registered email, last successful login, and customer ID | Do not unlock manually; route high-risk access issues for review |

If a new input is not covered by a specific policy above, first apply the
general workflow rules: request missing information and escalate when the
resolver identifies insufficient information or a safety risk. If neither a
specific policy nor a general workflow rule applies, mark the case as
`requires_policy_review` instead of guessing.

## 3. Human-review rules

### Classification review (`approval_gate`)

The workflow requires classification review when any condition is true:

| Condition | Expected behavior |
| --- | --- |
| Priority is `high` or `urgent` | Pause for human classification review |
| Classification confidence is below `0.70` | Pause for human classification review |
| Category is `billing` or `account` | Pause for human classification review |

Otherwise, the classification is auto-approved.

### Final response review (`final_review_gate`)

The workflow requires final review when any condition is true:

| Condition | Expected behavior |
| --- | --- |
| `needs_escalation` is `true` | Pause for final review |
| Resolution confidence is below `0.80` | Pause for final review |
| Priority is `high` or `urgent` | Pause for final review |
| Category is `billing` or `account` | Pause for final review |

The final review can approve, edit, or escalate the response.

## 4. Reusable scenario matrix

Use these scenario families when adding more test cases. Each new test case
should reference one policy or explicitly state that it is a routing or review
scenario.

| Scenario family | Example input condition | Expected category/intent | Expected route | Expected behavior |
| --- | --- | --- | --- | --- |
| Eligible duplicate refund | Duplicate charge within 7 days | `billing` / `refund_request` | `retrieve` | Explain refund eligibility and required verification |
| Ineligible refund | Purchase older than 7 days | `billing` / `refund_request` | `retrieve` | Explain that the documented refund period has passed |
| Subscription renewal refund | Renewal charge and refund request | `billing` / `refund_request` | `retrieve` | Request account verification before processing |
| Failed payment | Payment declined or failed | `billing` / `payment_issue` | `retrieve` | Request card, address, and balance checks |
| Repeated failed payment | More than two payment failures | `billing` / `payment_issue` | `retrieve` | Escalate according to payment policy |
| Login crash | App crashes during login | `technical` / `bug_report` | `retrieve` | Provide the documented troubleshooting steps |
| Persistent login crash | Login crash continues after retry | `technical` / `bug_report` | `retrieve` | Escalate after troubleshooting |
| Technical issue with insufficient details | Crash reported without logs, reproduction steps, or enough diagnostic information | `technical` / `bug_report` | `retrieve` | Request diagnostic details; the resolver rule allows or requires escalation when information is insufficient |
| Missing password-reset email | Reset email is not received | `technical` or `account` / `password_reset` | `retrieve` | Check spam, confirm email, retry after five minutes |
| Locked account | Account is locked | `account` / `account_access` | `retrieve` | Verify identity; do not unlock manually; review high-risk cases |
| Unauthorized access | Possible account compromise | `account` / `account_access` | `retrieve` | Treat as high risk and require human review/escalation |
| Missing account details | Vague account request | `account` / `account_access` | `retrieve` | Request verification details and avoid unsafe action |
| Shipped order with tracking | Order marked shipped | `order` / `order_status` | `retrieve` | Explain the 24-hour tracking window |
| Missing tracking after 24 hours | Tracking still unavailable | `order` / `order_status` | `retrieve` | Escalate to logistics |
| Unsupported request | Request outside all policies | `general` / `other` | `escalate` | Route for human-support review |
| General service question | General how-does-it-work question | `general` / `general_question` | `retrieve` | Provide supported information or ask a focused clarification |
| Complaint | Complaint without a routable intent | `general` / `complaint` | `escalate` | Route for human review |

## 5. Test-case review checklist

Before adding a case to the scoring dataset, confirm:

1. The input matches one scenario family or has an approved product requirement.
2. The expected category and intent are allowed by `models.py`.
3. The expected route follows the intent routing in `nodes.py`.
4. The expected final behavior is supported by a knowledge-base policy or requirement.
5. The expected escalation value follows the documented risk and review rules.
6. Any missing-information behavior is explicitly stated.
7. Unsupported scenarios are marked for policy review instead of guessed.

The matrix is reusable: future test cases only need a new input and a reference
to the applicable scenario or policy row.
