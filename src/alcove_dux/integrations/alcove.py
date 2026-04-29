"""Alcove integration helpers.

This module is intentionally small until Alcove Dux's scan report format and
Alcove's plugin target are both stable. It provides a privacy-preserving
conversion from an Alcove Dux report into text that Alcove can index.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from alcove_dux.reports import validate_report_dict


def extract_alcove_dux_report(path: str | Path) -> str:
    """Alcove extractor contract: read a ``.alcove-dux`` report as searchable text."""

    report_path = Path(path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Alcove Dux report must be a JSON object")
    errors = validate_report_dict(report)
    if errors:
        raise ValueError(f"Invalid Alcove Dux report: {'; '.join(errors)}")
    return report_to_alcove_text(report)


def report_to_alcove_text(report: Mapping[str, Any]) -> str:
    """Convert an Alcove Dux JSON report into searchable Alcove text."""

    lines = [
        "Alcove Dux similarity evidence report",
        f"Scan ID: {report.get('scan_id', 'unknown')}",
        f"Generated at: {report.get('generated_at', 'unknown')}",
        "",
        "Matches:",
    ]
    for match in report.get("matches", []):
        kind = match.get("kind", "needs_review")
        score = match.get("score", "unknown")
        explanation = match.get("explanation", "")
        lines.append(f"- {kind} score={score}: {explanation}")
    return "\n".join(lines).strip()


def report_to_alcove_document(report: Mapping[str, Any]) -> dict[str, str]:
    """Convert a report into a simple document dictionary for future adapters."""

    return {
        "source": str(report.get("scan_id", "unknown")),
        "text": report_to_alcove_text(report),
        "kind": "alcove_dux_report",
    }
