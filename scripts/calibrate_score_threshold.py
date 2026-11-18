"""Create a policy-cap calibration profile from detector scores."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from alcove_dux.calibration import calibrate_score_threshold


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select a detector-score threshold under a false-positive-rate cap"
    )
    parser.add_argument("--input", type=Path, required=True, help="JSON with labels and scores")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--detector-id", required=True)
    parser.add_argument("--fpr-cap", type=float, required=True)
    parser.add_argument("--threshold", action="append", type=float)
    parser.add_argument("--language")
    parser.add_argument("--task-type")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    labels = payload.get("labels")
    scores = payload.get("scores")
    if not isinstance(labels, list) or not all(isinstance(label, bool) for label in labels):
        raise ValueError("input labels must be a JSON array of booleans")
    if not isinstance(scores, list) or not all(
        isinstance(score, int | float) and not isinstance(score, bool) for score in scores
    ):
        raise ValueError("input scores must be a JSON array of numbers")
    numeric_scores = [float(score) for score in scores]
    if args.threshold:
        thresholds = tuple(args.threshold)
    elif numeric_scores:
        threshold_values = set(numeric_scores)
        upper_bound = min(math.nextafter(max(numeric_scores), math.inf), 1.0)
        threshold_values.add(upper_bound)
        thresholds = tuple(sorted(threshold_values))
    else:
        thresholds = ()

    profile = calibrate_score_threshold(
        labels,
        numeric_scores,
        dataset_id=args.dataset_id,
        detector_id=args.detector_id,
        thresholds=thresholds,
        false_positive_rate_cap=args.fpr_cap,
        language=args.language,
        task_type=args.task_type,
    )
    profile.save(args.out)
    print(profile.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
