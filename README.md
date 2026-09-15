# DeepEval Agentic Metrics Evaluation

This project evaluates an AI customer-support agent using DeepEval agentic metrics.

The agent receives a user request, decides whether a tool is needed, calls the selected tool when required, uses the tool result, and returns a final answer.

## Project objective

The objective is to evaluate the agent's behavior using realistic positive and clarification test cases. The test cases are stored in `agentic_metrics_dataset.csv`, and the agent is implemented in `agent.py`.

## Completed implementation

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

## Evaluation flow

```text
CSV test case
    -> DeepEval Golden
    -> real agent execution
    -> traced tool calls and final answer
    -> Task Completion and Tool Correctness evaluation
    -> score, success status, and reason
```

## Technology

- Python
- DeepEval
- LangChain
- Groq
- `openai/gpt-oss-20b` as the Groq model

## Main files

- `agent.py` - the LangChain customer-support agent and its tools
- `agentic_metrics_dataset.csv` - evaluation test data
- `deepeval_agentic_metrics_evaluation.ipynb` - the evaluation notebook
