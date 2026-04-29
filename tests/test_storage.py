from alcove_dux.documents import Document
from alcove_dux.matching import MatchEvidence
from alcove_dux.reports import ReportDocument, ScanReport
from alcove_dux.storage import AlcoveDuxStore


def test_store_persists_document_and_summary_without_raw_text(tmp_path):
    store = AlcoveDuxStore(tmp_path / "alcove_dux.sqlite")
    document = Document.from_text("Alpha beta", document_id="source")

    stored = store.put_document(document)
    summaries = store.list_documents()
    restored = store.get_document("source")
    chunks = store.list_chunks("source")

    assert stored.sha256 == document.sha256
    assert summaries[0]["id"] == "source"
    assert "text" not in summaries[0]
    assert summaries[0]["text_length"] == len("Alpha beta")
    assert restored is not None
    assert restored.text == "Alpha beta"
    assert chunks[0].summary == {
        "id": "source:0",
        "document_id": "source",
        "start": 0,
        "end": 10,
        "text_length": 10,
    }


def test_store_persists_scan_report_and_results(tmp_path):
    store = AlcoveDuxStore(tmp_path / "alcove_dux.sqlite")
    report = ScanReport.create(
        scan_id="scan",
        suspicious_document_id="suspicious",
        source_document_id="source",
        suspicious_document_sha256="a" * 64,
        source_document_sha256="b" * 64,
        source_documents=[ReportDocument(id="source", sha256="b" * 64)],
        matches=[
            MatchEvidence(
                kind="exact_token_sequence",
                suspicious_chunk_id="suspicious:0",
                source_chunk_id="source:0",
                score=1.0,
                suspicious_start=0,
                suspicious_end=10,
                source_start=0,
                source_end=10,
                explanation="Exact shared token sequence.",
            )
        ],
    )

    stored = store.put_scan(report)
    summary = store.list_scans()[0]
    restored = store.get_scan("scan")

    assert stored.status == "complete"
    assert summary["match_count"] == 1
    assert summary["top_score"] == 1.0
    assert restored is not None
    assert restored.report["matches"][0]["kind"] == "exact_token_sequence"
