"""Run small local checks against public benchmark samples.

This script intentionally avoids large corpora by default. It uses Hugging Face
Datasets for small sentence-pair benchmarks and writes summary JSON under
``reports/live-fire``.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path
from typing import Any

from alcove_dux.evaluation import binary_classification_metrics, mean_absolute_error
from alcove_dux.matching import compare_texts

DEFAULT_DATASETS = ("mrpc", "stsb", "paws", "plagbench")
PLAGBENCH_CSV_URL = (
    "https://raw.githubusercontent.com/Brit7777/plagbench/main/plagbench_evaluation_set.csv"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Alcove Dux baseline live-fire checks")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=("mrpc", "stsb", "paws", "plagbench"),
        help="Dataset to run",
    )
    parser.add_argument("--limit", type=int, default=50, help="Examples per dataset")
    parser.add_argument("--threshold", type=float, default=0.50, help="Baseline score threshold")
    parser.add_argument("--out-dir", type=Path, default=Path("reports/live-fire"))
    args = parser.parse_args()

    datasets = tuple(args.dataset or DEFAULT_DATASETS)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for dataset_id in datasets:
        summary = run_dataset(dataset_id, limit=args.limit, threshold=args.threshold)
        summaries.append(summary)
        (args.out_dir / f"{dataset_id}.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    print(json.dumps({"datasets": summaries}, indent=2, sort_keys=True))
    return 0


def run_dataset(dataset_id: str, *, limit: int, threshold: float) -> dict[str, Any]:
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - exercised by users without extra
        raise SystemExit("Install evaluation dependencies with: pip install -e '.[eval]'") from exc

    if dataset_id == "mrpc":
        rows = load_dataset("glue", "mrpc", split=f"validation[:{limit}]")
        return _run_pair_classification(
            dataset_id=dataset_id,
            rows=rows,
            left_key="sentence1",
            right_key="sentence2",
            label_key="label",
            positive_label=1,
            min_score=threshold,
        )
    if dataset_id == "stsb":
        rows = load_dataset("glue", "stsb", split=f"validation[:{limit}]")
        return _run_regression(
            dataset_id=dataset_id,
            rows=rows,
            left_key="sentence1",
            right_key="sentence2",
            label_key="label",
            min_score=threshold,
        )
    if dataset_id == "paws":
        rows = load_dataset(
            "google-research-datasets/paws",
            "labeled_final",
            split=f"validation[:{limit}]",
        )
        return _run_pair_classification(
            dataset_id=dataset_id,
            rows=rows,
            left_key="sentence1",
            right_key="sentence2",
            label_key="label",
            positive_label=1,
            min_score=threshold,
        )
    if dataset_id == "plagbench":
        rows = _load_plagbench(limit=limit)
        return _run_pair_classification(
            dataset_id=dataset_id,
            rows=rows,
            left_key="source_doc",
            right_key="susp_doc",
            label_key="label",
            positive_label="yes",
            min_score=threshold,
        )
    raise ValueError(f"Unsupported evaluation dataset: {dataset_id}")


def _load_plagbench(*, limit: int) -> list[dict[str, str]]:
    with urllib.request.urlopen(PLAGBENCH_CSV_URL, timeout=30) as response:
        text = response.read().decode("utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    return rows[:limit]


def _run_pair_classification(
    *,
    dataset_id: str,
    rows: Any,
    left_key: str,
    right_key: str,
    label_key: str,
    positive_label: int | str,
    min_score: float,
) -> dict[str, Any]:
    examples = []
    expected_values = []
    predicted_values = []
    group_values: dict[str, dict[str, tuple[list[bool], list[bool]]]] = {}
    for index, row in enumerate(rows):
        matches = compare_texts(row[left_key], row[right_key], min_score=min_score)
        predicted = bool(matches)
        expected = row[label_key] == positive_label
        score = matches[0].score if matches else 0.0
        expected_values.append(expected)
        predicted_values.append(predicted)
        example = {
            "index": index,
            "expected": expected,
            "predicted": predicted,
            "score": score,
            "label": row[label_key],
        }
        for key in ("plagiarism_type", "generation", "genre"):
            if key in row:
                value = row[key] or "none"
                example[key] = value
                group_values.setdefault(key, {}).setdefault(value, ([], []))
                group_values[key][value][0].append(expected)
                group_values[key][value][1].append(predicted)
        examples.append(example)

    metrics = binary_classification_metrics(expected_values, predicted_values)
    return {
        "dataset_id": dataset_id,
        "kind": "pair_classification",
        "limit": len(examples),
        "threshold": min_score,
        "metrics": metrics.to_dict(),
        "group_metrics": _group_metrics(group_values),
        "examples": examples,
    }


def _run_regression(
    *,
    dataset_id: str,
    rows: Any,
    left_key: str,
    right_key: str,
    label_key: str,
    min_score: float,
) -> dict[str, Any]:
    examples = []
    expected_values = []
    predicted_values = []
    for index, row in enumerate(rows):
        matches = compare_texts(row[left_key], row[right_key], min_score=min_score)
        predicted = matches[0].score if matches else 0.0
        expected = float(row[label_key]) / 5.0
        expected_values.append(expected)
        predicted_values.append(predicted)
        examples.append(
            {
                "index": index,
                "expected_similarity": round(expected, 4),
                "predicted_similarity": round(predicted, 4),
                "raw_label": row[label_key],
            }
        )

    return {
        "dataset_id": dataset_id,
        "kind": "similarity_regression",
        "limit": len(examples),
        "threshold": min_score,
        "metrics": {
            "mean_absolute_error": round(mean_absolute_error(expected_values, predicted_values), 4),
        },
        "examples": examples,
    }


def _group_metrics(
    groups: dict[str, dict[str, tuple[list[bool], list[bool]]]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        key: {
            value: binary_classification_metrics(expected, predicted).to_dict()
            for value, (expected, predicted) in values.items()
        }
        for key, values in groups.items()
    }


if __name__ == "__main__":
    raise SystemExit(main())
