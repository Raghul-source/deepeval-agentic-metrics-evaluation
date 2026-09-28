"""Stage 8: evaluate the open-source agent with DeepEval trajectory metrics."""

import csv
import json
import os
from pathlib import Path

import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from deepeval.evaluate import AsyncConfig, ErrorConfig
from deepeval.metrics import TaskCompletionMetric
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

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Return one compact valid JSON object only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=512,
            include_reasoning=False,
        )

        print("Finish reason:", response.choices[0].finish_reason)
        print("Usage:", response.usage)

        raw_response = response.choices[0].message.content or ""
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Groq returned non-JSON content: {raw_response!r}")

        return json.dumps(json.loads(raw_response[start : end + 1]))

    async def a_generate(self, prompt: str, **kwargs) -> str:
        return self.generate(prompt, **kwargs)

    def get_model_name(self) -> str:
        return self.model_name


def load_dataset(path: str = "open_source_agent_test_cases.csv"):
    """Convert the Stage 7 CSV into DeepEval Goldens."""
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig", newline="")))
    goldens = [
        Golden(
            input=row["customer_message"],
            expected_output=row["expected_final_result"],
        )
        for row in rows
    ]
    return rows, EvaluationDataset(goldens=goldens)


def run_evaluation():
    """Run every Stage 7 case once through the real traced agent."""
    groq_model = GroqDeepEvalModel()
    task_completion_metric = TaskCompletionMetric(
        threshold=0.6,
        model=groq_model,
        include_reason=True,
    )

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
                "actual_path": state.get("_execution_path", []),
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

    print("Agent execution results:")
    print(pd.DataFrame(results).to_string(index=False))
    failed_cases = [result for result in results if result["failed_checks"]]
    print(f"QA cases with deterministic mismatches: {len(failed_cases)}")
    for result in failed_cases:
        print(result["test_id"], "->", ", ".join(result["failed_checks"]))
    return results


if __name__ == "__main__":
    run_evaluation()
