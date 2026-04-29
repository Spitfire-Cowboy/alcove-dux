"""Scan report data structures."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from alcove_dux.documents import is_public_document_id
from alcove_dux.matching import MatchEvidence

REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ReportDocument:
    """Document identity included in a report."""

    id: str
    sha256: str | None = None


@dataclass(frozen=True)
class ScanReport:
    """A privacy-preserving Alcove Dux scan report."""

    schema_version: int
    scan_id: str
    suspicious_document_id: str
    source_document_id: str
    generated_at: str
    matches: tuple[MatchEvidence, ...]
    source_documents: tuple[ReportDocument, ...] = ()
    suspicious_document_sha256: str | None = None
    source_document_sha256: str | None = None
    catalog_schema_version: int | None = None
    selected_embedding_model_id: str | None = None
    selected_reranker_model_id: str | None = None
    runtime_config: dict | None = None

    @classmethod
    def create(
        cls,
        *,
        scan_id: str,
        suspicious_document_id: str,
        source_document_id: str,
        matches: list[MatchEvidence],
        source_documents: list[ReportDocument] | None = None,
        suspicious_document_sha256: str | None = None,
        source_document_sha256: str | None = None,
        catalog_schema_version: int | None = None,
        selected_embedding_model_id: str | None = None,
        selected_reranker_model_id: str | None = None,
        runtime_config: dict | None = None,
    ) -> ScanReport:
        return cls(
            schema_version=REPORT_SCHEMA_VERSION,
            scan_id=scan_id,
            suspicious_document_id=suspicious_document_id,
            source_document_id=source_document_id,
            generated_at=datetime.now(UTC).isoformat(),
            matches=tuple(matches),
            source_documents=tuple(source_documents or []),
            suspicious_document_sha256=suspicious_document_sha256,
            source_document_sha256=source_document_sha256,
            catalog_schema_version=catalog_schema_version,
            selected_embedding_model_id=selected_embedding_model_id,
            selected_reranker_model_id=selected_reranker_model_id,
            runtime_config=runtime_config,
        )

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""

        payload = asdict(self)
        payload["matches"] = list(payload["matches"])
        payload["source_documents"] = list(payload["source_documents"])
        return payload

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to JSON."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def validate_report_dict(report: dict) -> list[str]:
    """Return validation errors for an Alcove Dux report dictionary."""

    errors: list[str] = []
    required = {
        "schema_version",
        "scan_id",
        "suspicious_document_id",
        "source_document_id",
        "generated_at",
        "matches",
    }
    for key in sorted(required - report.keys()):
        errors.append(f"Missing required field: {key}")
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version: {report.get('schema_version')}")
    for key in ("suspicious_document_sha256", "source_document_sha256"):
        value = report.get(key)
        if value is not None and not _is_sha256(value):
            errors.append(f"Invalid SHA-256 field: {key}")
    for key in ("suspicious_document_id", "source_document_id"):
        value = report.get(key)
        if value is not None and not is_public_document_id(value):
            errors.append(f"{key} must be a public-safe document ID")
    runtime_config = report.get("runtime_config")
    if runtime_config is not None and not isinstance(runtime_config, dict):
        errors.append("runtime_config must be an object")
    source_documents = report.get("source_documents", [])
    if not isinstance(source_documents, list):
        errors.append("source_documents must be a list")
    else:
        for index, document in enumerate(source_documents):
            errors.extend(_validate_report_document(index, document))
    matches = report.get("matches", [])
    if not isinstance(matches, list):
        errors.append("matches must be a list")
        return errors
    for index, match in enumerate(matches):
        errors.extend(_validate_match(index, match))
    return errors


def _validate_report_document(index: int, document: object) -> list[str]:
    if not isinstance(document, dict):
        return [f"source_documents[{index}] must be an object"]
    errors = []
    document_id = document.get("id")
    if not isinstance(document_id, str) or not document_id:
        errors.append(f"source_documents[{index}].id must be a non-empty string")
    elif not is_public_document_id(document_id):
        errors.append(f"source_documents[{index}].id must be a public-safe document ID")
    sha256 = document.get("sha256")
    if sha256 is not None and not _is_sha256(sha256):
        errors.append(f"source_documents[{index}].sha256 must be a valid SHA-256 hash")
    return errors


def _validate_match(index: int, match: object) -> list[str]:
    if not isinstance(match, dict):
        return [f"matches[{index}] must be an object"]
    errors: list[str] = []
    required = {
        "kind",
        "suspicious_chunk_id",
        "source_chunk_id",
        "score",
        "suspicious_start",
        "suspicious_end",
        "source_start",
        "source_end",
        "explanation",
    }
    for key in sorted(required - match.keys()):
        errors.append(f"matches[{index}] missing required field: {key}")
    score = match.get("score")
    if not isinstance(score, int | float) or not 0 <= score <= 1:
        errors.append(f"matches[{index}].score must be between 0 and 1")
    for prefix in ("suspicious", "source"):
        start = match.get(f"{prefix}_start")
        end = match.get(f"{prefix}_end")
        chunk_id = match.get(f"{prefix}_chunk_id")
        if chunk_id is not None and not is_public_document_id(chunk_id):
            errors.append(f"matches[{index}].{prefix}_chunk_id must be a public-safe ID")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"matches[{index}].{prefix} offsets must be integers")
        elif start < 0 or end < start:
            errors.append(f"matches[{index}].{prefix} offsets are invalid")
    return errors


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
