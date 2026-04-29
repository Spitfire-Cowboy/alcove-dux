"""Run a small PAN14 detection smoke test.

This is not a full PlagDet scorer yet. It checks whether Alcove Dux's current
baseline emits any evidence for pairs that have PAN truth annotations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from alcove_dux.datasets.pan import iter_pan_pairs
from alcove_dux.evaluation import Span, binary_classification_metrics, span_overlap_metrics
from alcove_dux.matching import compare_texts


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a PAN14 baseline smoke test")
    parser.add_argument("root", type=Path, help="PAN14 corpus root")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--out", type=Path, default=Path("reports/live-fire/pan14-smoke.json"))
    args = parser.parse_args()

    result = run_pan14_smoke(args.root, limit=args.limit, threshold=args.threshold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_pan14_smoke(root: Path, *, limit: int, threshold: float) -> dict:
    expected_values = []
    predicted_values = []
    examples = []
    suspicious_truth_spans = []
    suspicious_predicted_spans = []
    source_truth_spans = []
    source_predicted_spans = []
    suspicious_exact_spans = []
    source_exact_spans = []
    match_kinds: dict[str, int] = {}

    for index, pair in enumerate(iter_pan_pairs(root, limit=limit)):
        suspicious_text = pair.suspicious_path.read_text(encoding="utf-8", errors="ignore")
        source_text = pair.source_path.read_text(encoding="utf-8", errors="ignore")
        matches = compare_texts(
            suspicious_text,
            source_text,
            suspicious_id=Path(pair.suspicious_reference).stem,
            source_id=Path(pair.source_reference).stem,
            min_score=threshold,
        )
        expected = bool(pair.annotations)
        predicted = bool(matches)
        expected_values.append(expected)
        predicted_values.append(predicted)
        suspicious_truth_spans.extend(
            Span.from_offset_length(
                annotation.suspicious_offset,
                annotation.suspicious_length,
            )
            for annotation in pair.annotations
        )
        source_truth_spans.extend(
            Span.from_offset_length(
                annotation.source_offset,
                annotation.source_length,
            )
            for annotation in pair.annotations
        )
        suspicious_predicted_spans.extend(
            Span(match.suspicious_start, match.suspicious_end)
            for match in matches
        )
        source_predicted_spans.extend(
            Span(match.source_start, match.source_end)
            for match in matches
        )
        suspicious_exact_spans.extend(
            Span(match.suspicious_start, match.suspicious_end)
            for match in matches
            if match.kind == "exact_token_sequence"
        )
        source_exact_spans.extend(
            Span(match.source_start, match.source_end)
            for match in matches
            if match.kind == "exact_token_sequence"
        )
        for match in matches:
            match_kinds[match.kind] = match_kinds.get(match.kind, 0) + 1
        examples.append(
            {
                "index": index,
                "suspicious_reference": pair.suspicious_reference,
                "source_reference": pair.source_reference,
                "expected": expected,
                "predicted": predicted,
                "annotations": len(pair.annotations),
                "matches": len(matches),
                "best_score": matches[0].score if matches else 0.0,
            }
        )

    metrics = binary_classification_metrics(expected_values, predicted_values)
    suspicious_span_metrics = span_overlap_metrics(
        suspicious_truth_spans,
        suspicious_predicted_spans,
    )
    source_span_metrics = span_overlap_metrics(
        source_truth_spans,
        source_predicted_spans,
    )
    suspicious_exact_metrics = span_overlap_metrics(
        suspicious_truth_spans,
        suspicious_exact_spans,
    )
    source_exact_metrics = span_overlap_metrics(
        source_truth_spans,
        source_exact_spans,
    )
    return {
        "dataset_id": "pan_2014_text_alignment",
        "kind": "span_dataset_detection_smoke",
        "limit": len(examples),
        "threshold": threshold,
        "metrics": metrics.to_dict(),
        "span_metrics": {
            "all_matches": {
                "submitted": suspicious_span_metrics.to_dict(),
                "source": source_span_metrics.to_dict(),
            },
            "exact_token_sequence": {
                "submitted": suspicious_exact_metrics.to_dict(),
                "source": source_exact_metrics.to_dict(),
            },
        },
        "match_kinds": dict(sorted(match_kinds.items())),
        "examples": examples,
        "notes": (
            "Smoke test only. Character-overlap metrics are implemented, but official "
            "PAN PlagDet granularity scoring is not implemented yet."
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
