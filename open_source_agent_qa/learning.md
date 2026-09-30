# Learning Plan

Yes. The project should focus on testing an existing open-source agent, not building a new agent.

Plan:

1. Keep your current DeepEval project as the baseline.
2. Select a small open-source agent with real tools and an acceptable license.
3. Add the open-source agent to a separate folder without changing its original code.
4. Run the agent with a few normal user requests to confirm it works.
5. Create QA test cases covering:
   - correct tool selection
   - wrong tool selection
   - missing information
   - incorrect arguments
   - unnecessary tool calls
   - incomplete final answers
6. Connect DeepEval to the agent’s real tracing/callback system.
7. Evaluate the agent using:
   - `TaskCompletionMetric`
   - `ToolCorrectnessMetric`
   - `ArgumentCorrectnessMetric`
   - `StepEfficiencyMetric`
   - `PlanAdherenceMetric`
   - `PlanQualityMetric`
8. Record the score, reason, actual tool calls, and failed test cases.
9. Analyse each failure and identify the root cause.
10. Document the defects and recommended fixes in the README.
11. If appropriate, apply a small agent fix and run the same tests again.
12. Add before-and-after results to GitHub.

Your role will be clearly shown as GenAI QA:

```text
existing open-source agent
→ QA test dataset
→ real trace capture
→ agentic metric evaluation
→ defect analysis
→ fix verification
```

This is stronger and more relevant to a GenAI QA portfolio than creating only a dummy agent.

## Action Steps

Examine source code files (`agent.py`, `tools.py`, `main.py`) to trace execution flow, prompt structures, and tool integration logic.

Review configuration and dependency files (`requirements.txt`, `.env`) to identify model providers, API versions, and installed libraries.

Check test suites or evaluation scripts (`tests/`, dataset CSVs) to see how inputs, expected outcomes, and metrics are currently defined.

## Purpose

Identify failure points: Spot code bugs, incorrect tool bindings, schema mismatches, or missing parameters before running tests.

Determine testability: Assess how the agent is structured so you know where to hook evaluation metrics, trace handlers, or assertions.

## Professional QA Workflow

Professionals usually do it in this order:

1. **Find the entry point**  
   Identify how the application starts. Here, it is `build_graph()`.
2. **Run a smoke test**  
   Send one normal request through the real entry point and confirm the agent completes.
3. **Record the result**  
   Note the input, final output, errors, and returned state.
4. **Understand only the required flow**  
   Inspect the files involved in that request: knowledge retrieval, model calls, nodes, and graph routing.
5. **Build the test adapter**  
   Connect DeepEval outside the original agent code.
6. **Run structured QA tests**  
   Evaluate the agent’s output, state, paths, and failures with metrics.

So your next professional step is to run one normal request through `build_graph()`.
