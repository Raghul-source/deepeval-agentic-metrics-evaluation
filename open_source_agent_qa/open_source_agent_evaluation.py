"""Stage 8: evaluate the open-source agent with DeepEval trajectory metrics."""

import csv
import json
import os
from pathlib import Path

import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from deepeval.evaluate import AsyncConfig, ErrorConfig
from deepeval.metrics import StepEfficiencyMetric, TaskCompletionMetric
from deepeval.models import DeepEvalBaseLLM
from deepeval.dataset import EvaluationDataset, Golden

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / "open_source_agent_under_test" / ".env")

from open_source_agent_adapter import run_open_source_agent  # noqa: E402


class GroqDeepEvalModel(DeepEvalBaseLLM):
    """Use the configured Groq model as DeepEval's judge model."""

    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        self.model_name = model_name
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

    def load_model(self):
        return self.client

    def generate(self, prompt: str, **kwargs) -> str:
        print("Prompt characters:", len(prompt))
        print("Approximate prompt tokens:", len(prompt) // 4)

        system_message = "Return one compact valid JSON object only."
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        requested_schema = kwargs.get("schema")

        print("Request model:", self.model_name)
        print("Request max_tokens:", 1024)
        print("Request schema:", repr(requested_schema))
        print("Request system message:", repr(system_message))
        print("Request user prompt:", repr(prompt))

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
            max_tokens=1024,
            include_reasoning=False,
        )

        print("Finish reason:", response.choices[0].finish_reason)
        print("Usage:", response.usage)
        print("Raw Groq response:", repr(response))
        print("Raw Groq message:", repr(response.choices[0].message))

        raw_response = response.choices[0].message.content or ""
        print("Raw Groq content:", repr(raw_response))
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Groq returned non-JSON content: {raw_response!r}")

        return json.dumps(json.loads(raw_response[start : end + 1]))

    async def a_generate(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)

    def get_model_name(self) -> str:
        return self.model_name


def load_dataset(path: str | None = None):
    """Convert the Stage 7 CSV into DeepEval Goldens."""
    if path is None:
        path = str(PROJECT_ROOT / "open_source_agent_test_cases.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    goldens = [
        Golden(
            input=row["customer_message"],
            expected_output=row["expected_final_result"],
        )
        for row in rows
    ]
    return rows, EvaluationDataset(goldens=goldens)


def build_expected_trajectory(row: dict) -> list[str]:
    """Build the expected workflow path from existing QA expectation columns."""
    expected_category = row["expected_category"].strip().lower()
    expected_route = row["expected_route"].strip().lower()
    expected_escalation = row["expected_escalation"].strip().lower() == "true"

    expected_steps = ["classify_ticket"]

    if expected_category in {"billing", "account"}:
        expected_steps.append("approval_gate")

    if expected_route == "retrieve":
        expected_steps.extend(["retrieve_knowledge", "draft_resolution"])
        expected_steps.append("final_review_gate")
        expected_steps.append(
            "escalate_case" if expected_escalation else "resolve_case"
        )
    elif expected_route == "escalate":
        expected_steps.append("escalate_case")

    return expected_steps


def compare_trajectory(
    expected_steps: list[str],
    actual_steps: list[str],
) -> dict:
    """Compare expected workflow steps with the agent's actual workflow path."""
    missing_steps = [step for step in expected_steps if step not in actual_steps]
    unexpected_steps = [step for step in actual_steps if step not in expected_steps]

    expected_positions = [
        actual_steps.index(step)
        for step in expected_steps
        if step in actual_steps
    ]
    order_match = expected_positions == sorted(expected_positions)

    return {
        "trajectory_match": (
            not missing_steps
            and not unexpected_steps
            and order_match
        ),
        "missing_steps": missing_steps,
        "unexpected_steps": unexpected_steps,
        "order_match": order_match,
    }


def run_evaluation():
    """Run every Stage 7 case once through the real traced agent."""
    groq_model = GroqDeepEvalModel()
    task_completion_metric = TaskCompletionMetric(
        threshold=0.5,
        model=groq_model,
        include_reason=True,
    )
    # Disabled for the active run: the built-in StepEfficiencyMetric is
    # referenceless and can fail on Groq before our trajectory table prints.
    # Keep it here only for later experimental/secondary analysis.
    # step_efficiency_metric = StepEfficiencyMetric(
    #     threshold=0.5,
    #     model=groq_model,
    #     include_reason=True,
    #     async_mode=False,
    #     eval_mode="llm",
    # )

    rows, dataset = load_dataset()
    results = []

    for index, golden in enumerate(
        dataset.evals_iterator(
            metrics=[task_completion_metric],
            error_config=ErrorConfig(ignore_errors=False),
            async_config=AsyncConfig(run_async=False),
        ),
        start=1,
    ):
        row = rows[index - 1]
        # state = run_open_source_agent(
        #    customer_id=f"QA_{row['test_id']}",
        #    customer_message=golden.input,
        #)

        try:
            state = run_open_source_agent(
                customer_id=f"QA_{row['test_id']}",
                customer_message=golden.input,
            )
        except Exception as exc:
            print("\n--- RAW GROQ ERROR ---")
            print("Error type:", type(exc).__name__)
            print("Error body:", repr(getattr(exc, "body", None)))
            print("Full error:", repr(str(exc)))
            raise


        expected_escalation = row["expected_escalation"].strip().lower() == "true"
        actual_category = state.get("category", "")
        actual_intent = state.get("intent", "")
        actual_route = state.get("initial_route", "")
        actual_escalation = bool(state.get("needs_escalation", False))
        actual_trajectory = state.get("_execution_path", [])
        expected_trajectory = build_expected_trajectory(row)
        trajectory_checks = compare_trajectory(
            expected_trajectory,
            actual_trajectory,
        )

        checks = {
            "category_match": actual_category == row["expected_category"],
            "intent_match": actual_intent == row["expected_intent"],
            "route_match": actual_route == row["expected_route"],
            "escalation_match": actual_escalation == expected_escalation,
        }
        failed_checks = [name for name, passed in checks.items() if not passed]

        results.append(
            {
                "test_id": row["test_id"],
                "actual_output": state.get("final_response", ""),
                "expected_trajectory": expected_trajectory,
                "actual_trajectory": actual_trajectory,
                **trajectory_checks,
                "expected_category": row["expected_category"],
                "actual_category": actual_category,
                "expected_intent": row["expected_intent"],
                "actual_intent": actual_intent,
                "expected_route": row["expected_route"],
                "actual_route": actual_route,
                "expected_escalation": expected_escalation,
                "actual_escalation": actual_escalation,
                **checks,
                "failed_checks": failed_checks,
            }
        )

        print(f"Completed {index}/{len(rows)}: {row['test_id']}")

    results_df = pd.DataFrame(results)
    agent_result_columns = [
        "test_id",
        "actual_output",
        "expected_category",
        "actual_category",
        "expected_intent",
        "actual_intent",
        "expected_route",
        "actual_route",
        "expected_escalation",
        "actual_escalation",
        "category_match",
        "intent_match",
        "route_match",
        "escalation_match",
        "failed_checks",
    ]
    trajectory_columns = [
        "test_id",
        "expected_trajectory",
        "actual_trajectory",
        "trajectory_match",
        "missing_steps",
        "unexpected_steps",
        "order_match",
    ]

    print("Agent execution results:")
    print(results_df[agent_result_columns].to_string(index=False))
    print("Trajectory evaluation results:")
    print(results_df[trajectory_columns].to_string(index=False))
    print(
        "Note: trajectory_match is the project-specific workflow check. "
        "Built-in StepEfficiencyMetric output is secondary observation only."
    )

    failed_cases = [result for result in results if result["failed_checks"]]
    print(f"QA cases with deterministic mismatches: {len(failed_cases)}")
    for result in failed_cases:
        print(result["test_id"], "->", ", ".join(result["failed_checks"]))
    failed_trajectories = [
        result for result in results if not result["trajectory_match"]
    ]
    print(f"QA cases with trajectory mismatches: {len(failed_trajectories)}")
    for result in failed_trajectories:
        print(result["test_id"], "->", "trajectory_match")
    return results


if __name__ == "__main__":
    run_evaluation()
