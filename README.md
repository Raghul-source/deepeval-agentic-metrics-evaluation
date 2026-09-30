# DeepEval Agentic Metrics Evaluation

This project evaluates an AI customer-support agent using DeepEval agentic metrics.

The agent receives a user request, decides whether a tool is needed, calls the selected tool when required, uses the tool result, and returns a final answer.

## Project Structure

This repository contains two parts:

- `baseline/` — original DeepEval learning project.
- `open_source_agent_qa/` — QA evaluation of the [LangGraph Customer Support Agent](https://github.com/niti007/langgraph-customer-support-agent).

## Project Objective

- The `baseline/` project demonstrates DeepEval metric evaluation techniques.
- The `open_source_agent_qa/` project tests the real LangGraph Customer Support Agent using an adapter, QA test cases, source-based expected behavior, and DeepEval evaluation.

## Baseline Implementation

The notebook currently contains tracing-based implementations for:

- `TaskCompletionMetric`
- `ToolCorrectnessMetric`

Both metrics run against the real agent execution rather than comparing manually entered agent results from the CSV.

### Trace levels used

- Task Completion uses the complete agent trace captured by `traced_support_agent()`.
- Tool Correctness uses a component-level trace span created by `evaluate_tool_correctness()`.

### Task Completion

`TaskCompletionMetric` evaluates whether the agent completed the user's request successfully.

The agent's final answer is captured from the real execution. DeepEval prepares the metric-specific evaluation prompt and sends it to the Groq evaluator model through the custom `DeepEvalBaseLLM` adapter. The evaluator returns the score and reason.

### Tool Correctness

`ToolCorrectnessMetric` evaluates whether the agent selected the correct tool for each test case.

Expected tools are created from the CSV as DeepEval `ToolCall` objects. Blank expected-tool values become an empty list, meaning that no tool is expected for that case.

The actual tool calls are captured automatically from the agent's traced execution through the DeepEval/LangChain callback integration. They are not manually supplied through an `actual_tools` CSV value.

Both positive and clarification cases are evaluated:

- Expected tool and tool called: the tool selection can pass.
- Expected tool and no tool called: the tool selection fails.
- No expected tool and no tool called: the tool selection can pass.
- No expected tool and a tool called: the tool selection fails.

## Baseline Evaluation Flow

```text
CSV test case
    -> DeepEval Golden
    -> real agent execution
    -> traced tool calls and final answer
    -> Task Completion and Tool Correctness evaluation
    -> score, success status, and reason
```

## Baseline Technology

- Python
- DeepEval
- LangChain
- Groq
- `openai/gpt-oss-20b` as the Groq model

## Baseline Files

- `baseline/agent.py` - the LangChain customer-support agent and its tools
- `baseline/agentic_metrics_dataset.csv` - evaluation test data
- `baseline/deepeval_agentic_metrics_evaluation.ipynb` - the evaluation notebook

## Open-Source Agent QA Implementation

This section evaluates the [LangGraph Customer Support Agent](https://github.com/niti007/langgraph-customer-support-agent) as an existing system under test. The original agent source is kept unchanged, while the QA adapter and evaluation scripts are maintained separately.

### Open-Source QA Files

- `open_source_agent_under_test/` — cloned open-source agent being tested.
- `open_source_agent_adapter.py` — calls the agent and handles review interruptions.
- `open_source_agent_evaluation.py` — runs the DeepEval evaluation.
- `open_source_agent_test_cases.csv` — contains the QA test cases and expected behavior.
- `agent_behavior_matrix.md` — extracts the allowed categories and intents, intent-to-route rules, knowledge-base policies, human-review conditions, escalation rules, reusable QA scenarios, and expected-value validation checklist.
- `evaluation_output.txt` — records the latest evaluation scores, reasons, and mismatches.
- `smoke_test_log.txt` — records the initial smoke-test execution.

### Open-Source QA Workflow

```text
QA test case
→ evaluation adapter
→ real agent graph
→ automatic human-review responses
→ captured state and workflow path
→ DeepEval TaskCompletionMetric
→ direct category, intent, route, and escalation checks
→ failure analysis
```

### Current Evaluation Result

The latest run completed all 10 test cases.

- Task Completion average score: `0.69`
- Threshold: `0.50`
- DeepEval metric result: `8 passed, 2 failed`
- Direct comparison mismatches: `3`

The direct mismatches were found in:

- `OS_AGENT_TC_003` — escalation value
- `OS_AGENT_TC_007` — intent, route, and escalation values
- `OS_AGENT_TC_009` — intent value

Detailed outputs and metric reasons are available in `evaluation_output.txt`.

### Run the Open-Source Evaluation

1. Copy `open_source_agent_qa/.env.example` to `open_source_agent_qa/.env`.
2. Replace the placeholder with your own Groq API key.
3. From the `open_source_agent_qa/` folder, run:

```powershell
python .\open_source_agent_evaluation.py
```

The real `.env` file is ignored and must not be committed. `.env.example` contains only a dummy placeholder.
