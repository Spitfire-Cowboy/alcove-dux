"""Sentence-pair and document-pair benchmark loaders."""

from __future__ import annotations

import csv
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass

PLAGBENCH_CSV_URL = (
    "https://raw.githubusercontent.com/Brit7777/plagbench/main/plagbench_evaluation_set.csv"
)


@dataclass(frozen=True)
class PairExample:
    """A pairwise benchmark example."""

    id: str
    left_text: str
    right_text: str
    label: bool | float
    metadata: dict[str, str]


def load_plagbench_public(*, limit: int | None = None) -> list[PairExample]:
    """Load PlagBench's public CSV artifact."""

    with urllib.request.urlopen(PLAGBENCH_CSV_URL, timeout=30) as response:
        text = response.read().decode("utf-8")
    return parse_plagbench_csv(text, limit=limit)


def parse_plagbench_csv(text: str, *, limit: int | None = None) -> list[PairExample]:
    """Parse PlagBench public CSV text into pair examples."""

    rows = csv.DictReader(text.splitlines())
    examples = []
    for index, row in enumerate(rows):
        examples.append(
            PairExample(
                id=f"plagbench:{index}",
                left_text=row["source_doc"],
                right_text=row["susp_doc"],
                label=row["label"] == "yes",
                metadata={
                    key: row[key]
                    for key in ("label", "plagiarism_type", "generation", "genre")
                    if key in row
                },
            )
        )
        if limit is not None and len(examples) >= limit:
            break
    return examples


def load_huggingface_pair_examples(dataset_id: str, *, limit: int) -> list[PairExample]:
    """Load configured small pair benchmarks through Hugging Face Datasets."""

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "Benchmark loaders require the eval extra: python -m pip install -e \".[eval]\""
        ) from exc

    if dataset_id == "mrpc":
        rows = load_dataset("glue", "mrpc", split=f"validation[:{limit}]")
        return _examples_from_rows(
            rows,
            dataset_id=dataset_id,
            left_key="sentence1",
            right_key="sentence2",
            label_key="label",
            positive_label=1,
        )
    if dataset_id == "paws":
        rows = load_dataset(
            "google-research-datasets/paws",
            "labeled_final",
            split=f"validation[:{limit}]",
        )
        return _examples_from_rows(
            rows,
            dataset_id=dataset_id,
            left_key="sentence1",
            right_key="sentence2",
            label_key="label",
            positive_label=1,
        )
    if dataset_id == "stsb":
        rows = load_dataset("glue", "stsb", split=f"validation[:{limit}]")
        return [
            PairExample(
                id=f"{dataset_id}:{index}",
                left_text=row["sentence1"],
                right_text=row["sentence2"],
                label=float(row["label"]) / 5.0,
                metadata={"raw_label": str(row["label"])},
            )
            for index, row in enumerate(rows)
        ]
    raise ValueError(f"Unsupported Hugging Face pair dataset: {dataset_id}")


def _examples_from_rows(
    rows: Iterable,
    *,
    dataset_id: str,
    left_key: str,
    right_key: str,
    label_key: str,
    positive_label: int | str,
) -> list[PairExample]:
    return [
        PairExample(
            id=f"{dataset_id}:{index}",
            left_text=row[left_key],
            right_text=row[right_key],
            label=row[label_key] == positive_label,
            metadata={"label": str(row[label_key])},
        )
        for index, row in enumerate(rows)
    ]
