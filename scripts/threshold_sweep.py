"""Sweep baseline thresholds over local evaluation datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from live_fire import DEFAULT_DATASETS, run_dataset

DEFAULT_THRESHOLDS = (0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep Alcove Dux baseline thresholds")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=("mrpc", "stsb", "paws", "plagbench"),
        help="Dataset to run",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--threshold",
        action="append",
        type=float,
        help="Threshold to test; may be repeated",
    )
    parser.add_argument("--out", type=Path, default=Path("reports/live-fire/threshold-sweep.json"))
    args = parser.parse_args()

    dataset_ids = tuple(args.dataset or DEFAULT_DATASETS)
    thresholds = tuple(args.threshold or DEFAULT_THRESHOLDS)
    summaries = []
    for dataset_id in dataset_ids:
        dataset_results = []
        for threshold in thresholds:
            result = run_dataset(dataset_id, limit=args.limit, threshold=threshold)
            dataset_results.append(
                {
                    "threshold": threshold,
                    "metrics": result["metrics"],
                    "group_metrics": result.get("group_metrics", {}),
                }
            )
        summaries.append({"dataset_id": dataset_id, "results": dataset_results})

    payload = {"limit": args.limit, "datasets": summaries}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
