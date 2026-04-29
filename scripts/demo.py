"""Run the public Alcove Dux demo."""

from __future__ import annotations

import json
from pathlib import Path

from alcove_dux.cli import main

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "examples" / "demo"
OUT_DIR = ROOT / "reports" / "demo"


def run_demo() -> int:
    """Generate demo reports from the bundled example documents."""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUT_DIR / "demo.alcove-dux"
    public_html = OUT_DIR / "demo.html"
    review_html = OUT_DIR / "demo-review.html"

    result = main(
        [
            "scan",
            str(DEMO_DIR / "submitted.txt"),
            str(DEMO_DIR / "source.txt"),
            "--min-score",
            "0.35",
            "--out",
            str(report),
            "--html",
            str(public_html),
            "--review-html",
            str(review_html),
        ]
    )
    if result != 0:
        return result

    payload = json.loads(report.read_text(encoding="utf-8"))
    print("Alcove Dux demo complete")
    print(f"JSON report: {report}")
    print(f"Public HTML: {public_html}")
    print(f"Local review HTML: {review_html}")
    print(f"Matches: {len(payload.get('matches', []))}")
    if payload.get("matches"):
        top = payload["matches"][0]
        print(f"Top match: {top.get('kind')} score={top.get('score')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
