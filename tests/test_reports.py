from dataclasses import replace

from alcove_dux.matching import MatchEvidence
from alcove_dux.reports import (
    REPORT_SCHEMA_VERSION,
    ReportDocument,
    ScanReport,
    validate_report_dict,
)


def sample_match():
    return MatchEvidence(
        kind="exact_token_sequence",
        suspicious_chunk_id="suspicious:0",
        source_chunk_id="source:0",
        score=1.0,
        suspicious_start=0,
        suspicious_end=10,
        source_start=0,
        source_end=10,
        explanation="Exact shared token sequence of 10 tokens.",
    )


def test_scan_report_includes_schema_version():
    report = ScanReport.create(
        scan_id="scan",
        suspicious_document_id="suspicious",
        source_document_id="source",
        suspicious_document_sha256="a" * 64,
        source_document_sha256="b" * 64,
        source_documents=[ReportDocument(id="source", sha256="b" * 64)],
        runtime_config={"embedding_model_id": "baai_bge_small_en_v1_5"},
        matches=[sample_match()],
    )

    payload = report.to_dict()
    assert payload["schema_version"] == REPORT_SCHEMA_VERSION
    assert validate_report_dict(payload) == []
    assert payload["source_documents"][0]["id"] == "source"
    assert payload["runtime_config"]["embedding_model_id"] == "baai_bge_small_en_v1_5"


def test_validate_report_rejects_bad_hash_and_offsets():
    report = ScanReport.create(
        scan_id="scan",
        suspicious_document_id="suspicious",
        source_document_id="source",
        suspicious_document_sha256="not-a-hash",
        matches=[replace(sample_match(), suspicious_start=5, suspicious_end=1)],
    )

    errors = validate_report_dict(report.to_dict())

    assert "Invalid SHA-256 field: suspicious_document_sha256" in errors
    assert "matches[0].suspicious offsets are invalid" in errors


def test_validate_report_rejects_private_document_ids():
    report = ScanReport.create(
        scan_id="scan",
        suspicious_document_id="Student-Jane-Doe",
        source_document_id="source",
        source_documents=[ReportDocument(id="source.docx", sha256="b" * 64)],
        matches=[replace(sample_match(), source_chunk_id="source.docx:0")],
    )

    errors = validate_report_dict(report.to_dict())

    assert "suspicious_document_id must be a public-safe document ID" in errors
    assert "source_documents[0].id must be a public-safe document ID" in errors
    assert "matches[0].source_chunk_id must be a public-safe ID" in errors
