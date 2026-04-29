"""Create a baseline lexical calibration profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from alcove_dux.calibration import (
    calibrate_lexical_threshold,
    calibrate_lexical_threshold_by_language,
)
from alcove_dux.datasets.pairs import load_huggingface_pair_examples, load_plagbench_public

DEFAULT_THRESHOLDS = (0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate Alcove Dux baseline thresholds")
    parser.add_argument(
        "--dataset",
        choices=("mrpc", "paws", "plagbench"),
        default="plagbench",
    )
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--language", help="Language code to store in the calibration profile")
    parser.add_argument("--task-type", help="Task type, such as exact_reuse or paraphrase")
    parser.add_argument(
        "--group-by-language",
        action="store_true",
        help="Write one calibration profile per language metadata value",
    )
    parser.add_argument("--out", type=Path, default=Path("reports/calibration/profile.json"))
    args = parser.parse_args()

    if args.dataset == "plagbench":
        examples = load_plagbench_public(limit=args.limit)
    else:
        examples = load_huggingface_pair_examples(args.dataset, limit=args.limit)
    if args.group_by_language:
        profiles = calibrate_lexical_threshold_by_language(
            examples,
            dataset_id=args.dataset,
            thresholds=DEFAULT_THRESHOLDS,
            task_type=args.task_type,
        )
        payload = {language: profile.to_dict() for language, profile in profiles.items()}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        profile = calibrate_lexical_threshold(
            examples,
            dataset_id=args.dataset,
            thresholds=DEFAULT_THRESHOLDS,
            language=args.language,
            task_type=args.task_type,
        )
        profile.save(args.out)
        print(json.dumps(profile.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
