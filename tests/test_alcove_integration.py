import json
from importlib.metadata import entry_points

from alcove_dux.integrations.alcove import (
    extract_alcove_dux_report,
    report_to_alcove_document,
    report_to_alcove_text,
)


def sample_report():
    return {
        "schema_version": 1,
        "scan_id": "scan-123",
        "generated_at": "2026-04-28T12:00:00+00:00",
        "suspicious_document_id": "suspicious",
        "source_document_id": "source",
        "suspicious_document_sha256": "a" * 64,
        "source_document_sha256": "b" * 64,
        "private_path": "/Users/example/private/source.pdf",
        "matches": [
            {
                "kind": "exact_overlap",
                "suspicious_chunk_id": "suspicious:0",
                "source_chunk_id": "source:0",
                "score": 1.0,
                "suspicious_start": 0,
                "suspicious_end": 10,
                "source_start": 0,
                "source_end": 10,
                "explanation": "Normalized text spans are exact or near-exact matches.",
                "suspicious_text": "raw suspicious passage",
                "source_text": "raw source passage",
            }
        ],
    }


def test_report_to_alcove_text_includes_evidence_summary():
    text = report_to_alcove_text(sample_report())

    assert "Alcove Dux similarity evidence report" in text
    assert "scan-123" in text
    assert "exact_overlap score=1.0" in text
    assert "Normalized text spans" in text


def test_report_to_alcove_text_omits_raw_text_and_private_paths():
    text = report_to_alcove_text(sample_report())

    assert "/Users/example" not in text
    assert "raw suspicious passage" not in text
    assert "raw source passage" not in text


def test_extract_alcove_dux_report_reads_json(tmp_path):
    path = tmp_path / "scan.alcove-dux"
    path.write_text(json.dumps(sample_report()), encoding="utf-8")

    text = extract_alcove_dux_report(path)

    assert "scan-123" in text
    assert "exact_overlap" in text


def test_report_to_alcove_document_shape():
    document = report_to_alcove_document(sample_report())

    assert document["source"] == "scan-123"
    assert document["kind"] == "alcove_dux_report"
    assert "exact_overlap" in document["text"]


def test_alcove_entry_point_metadata_exists():
    group = entry_points().select(group="alcove.extractors")

    assert any(
        item.name == "alcove_dux"
        and item.value == "alcove_dux.integrations.alcove:extract_alcove_dux_report"
        for item in group
    )
