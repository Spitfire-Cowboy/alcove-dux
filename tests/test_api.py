import pytest

import alcove_dux.api as api_module
from alcove_dux.api import _dashboard_html, create_app
from alcove_dux.matching import MatchEvidence


def test_create_app_requires_api_extra_when_fastapi_missing():
    pytest.importorskip("fastapi")
    app = create_app()

    assert app.title == "Alcove Dux"


def test_api_document_and_scan_lifecycle(tmp_path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "api.sqlite"))

    suspicious = client.post(
        "/documents",
        json={
            "document_id": "suspicious",
            "text": "Intro. Alpha beta gamma delta epsilon zeta eta theta iota. Outro.",
        },
    )
    source = client.post(
        "/documents",
        json={
            "document_id": "source",
            "text": "Alpha beta gamma delta epsilon zeta eta theta iota.",
        },
    )

    assert suspicious.status_code == 200
    assert source.status_code == 200
    assert "text" not in suspicious.json()
    chunks = client.get("/documents/suspicious/chunks")
    assert chunks.status_code == 200
    assert chunks.json()[0]["document_id"] == "suspicious"
    assert "text" not in chunks.json()[0]

    scan = client.post(
        "/scans",
        json={
            "suspicious_document_id": "suspicious",
            "source_document_id": "source",
        },
    )
    scan_payload = scan.json()

    assert scan.status_code == 200
    assert scan_payload["matches"]

    summary = client.get(f"/scans/{scan_payload['scan_id']}").json()
    results = client.get(f"/scans/{scan_payload['scan_id']}/results").json()

    assert summary["match_count"] == len(scan_payload["matches"])
    assert "matches" not in summary
    assert results["scan_id"] == scan_payload["scan_id"]


def test_api_file_upload_lifecycle(tmp_path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "upload.sqlite"))

    uploaded = client.post(
        "/documents/file",
        data={"document_id": "upload", "title": "Uploaded"},
        files={"file": ("upload.txt", b"Alpha beta gamma delta epsilon zeta eta.", "text/plain")},
    )

    assert uploaded.status_code == 200
    assert uploaded.json()["id"] == "upload"
    assert uploaded.json()["metadata"]["title"] == "Uploaded"
    assert "text" not in uploaded.json()

    document = client.get("/documents/upload")

    assert document.status_code == 200
    assert document.json()["text"] == "Alpha beta gamma delta epsilon zeta eta."


def test_api_file_upload_rejects_unsupported_type(tmp_path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "reject.sqlite"))

    uploaded = client.post(
        "/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.csv", b"not,a,supported,document", "text/csv")},
    )

    assert uploaded.status_code == 400
    assert uploaded.json()["detail"] == "Unsupported document type: .csv"


def test_api_file_upload_hides_parser_errors(tmp_path, monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "reject-runtime.sqlite"))

    async def fail_upload(*_args, **_kwargs):
        raise RuntimeError("private parser path: /tmp/secret.txt")

    monkeypatch.setattr(api_module, "_document_from_upload", fail_upload)

    uploaded = client.post(
        "/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.txt", b"alpha", "text/plain")},
    )

    assert uploaded.status_code == 400
    assert uploaded.json()["detail"] == api_module.GENERIC_UPLOAD_ERROR_MESSAGE
    assert "secret.txt" not in uploaded.text


def test_api_file_upload_surfaces_missing_documents_extra(tmp_path, monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "missing-docs.sqlite"))

    async def fail_upload(*_args, **_kwargs):
        raise RuntimeError(
            'PDF ingestion requires the documents extra: python -m pip install -e ".[documents]"'
        )

    monkeypatch.setattr(api_module, "_document_from_upload", fail_upload)

    uploaded = client.post(
        "/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert uploaded.status_code == 400
    assert "requires the documents extra" in uploaded.json()["detail"]


def test_dashboard_routes_do_not_expose_raw_text(tmp_path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "dashboard.sqlite"))
    secret_text = "Alpha beta gamma delta epsilon zeta eta theta."

    home = client.get("/")
    assert home.status_code == 200
    assert "No documents yet." in home.text

    suspicious = client.post(
        "/ui/documents",
        data={"document_id": "suspicious", "title": "Suspicious", "text": secret_text},
    )
    source = client.post(
        "/ui/documents",
        data={"document_id": "source", "title": "Source", "text": secret_text},
    )

    assert suspicious.status_code == 200
    assert source.status_code == 200
    assert "suspicious" in source.text
    assert "source" in source.text
    assert secret_text not in source.text

    scan = client.post(
        "/ui/scans",
        data={
            "suspicious_document_id": "suspicious",
            "source_document_id": "source",
            "min_score": "0.5",
        },
    )

    assert scan.status_code == 200
    assert "<mark>" in scan.text


def test_dashboard_file_upload_error_stays_on_dashboard(tmp_path):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "dashboard-upload.sqlite"))

    uploaded = client.post(
        "/ui/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.csv", b"not,a,supported,document", "text/csv")},
    )

    assert uploaded.status_code == 200
    assert "Unsupported document type: .csv" in uploaded.text
    assert "not,a,supported,document" not in uploaded.text


def test_dashboard_file_upload_hides_parser_errors(tmp_path, monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "dashboard-runtime.sqlite"))

    async def fail_upload(*_args, **_kwargs):
        raise RuntimeError("private parser path: /tmp/secret.txt")

    monkeypatch.setattr(api_module, "_document_from_upload", fail_upload)

    uploaded = client.post(
        "/ui/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.txt", b"alpha", "text/plain")},
    )

    assert uploaded.status_code == 200
    assert api_module.GENERIC_UPLOAD_ERROR_MESSAGE in uploaded.text
    assert "secret.txt" not in uploaded.text


def test_dashboard_file_upload_surfaces_missing_documents_extra(tmp_path, monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "dashboard-missing-docs.sqlite"))

    async def fail_upload(*_args, **_kwargs):
        raise RuntimeError(
            'PDF ingestion requires the documents extra: python -m pip install -e ".[documents]"'
        )

    monkeypatch.setattr(api_module, "_document_from_upload", fail_upload)

    uploaded = client.post(
        "/ui/documents/file",
        data={"document_id": "upload"},
        files={"file": ("upload.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert uploaded.status_code == 200
    assert "requires the documents extra" in uploaded.text


def test_dashboard_html_has_screen_reader_landmarks_and_labels():
    html = _dashboard_html([], [], message="Document not found.")

    assert 'href="#main-content"' in html
    assert '<main id="main-content" tabindex="-1">' in html
    assert 'role="alert" aria-live="assertive"' in html
    assert 'aria-labelledby="documents-heading"' in html
    assert 'for="document-id"' in html
    assert 'id="document-id"' in html
    assert 'for="upload-file"' in html
    assert 'id="upload-file"' in html
    assert '<caption>Stored documents</caption>' in html
    assert '<caption>Completed scans</caption>' in html
    assert '<th scope="col">ID</th>' in html
    assert 'aria-describedby="threshold-help"' in html
    assert 'No documents available' in html


def test_dashboard_html_omits_raw_document_text():
    html = _dashboard_html(
        [
            {
                "id": "source",
                "sha256": "a" * 64,
                "text_length": 12,
                "created_at": "2026-04-28T00:00:00+00:00",
                "metadata": {},
            }
        ],
        [
            {
                "id": "scan",
                "status": "complete",
                "match_count": 1,
                "top_score": 1.0,
                "created_at": "2026-04-28T00:00:00+00:00",
            }
        ],
    )

    assert "source" in html
    assert "scan" in html
    assert '<th scope="row"><code>source</code></th>' in html
    assert '<th scope="row"><a href="/ui/scans/scan"><code>scan</code></a></th>' in html
    assert "raw private text" not in html


def test_api_pair_scan_uses_requested_semantic_and_rerank_models(tmp_path, monkeypatch):
    fastapi_testclient = pytest.importorskip("fastapi.testclient")
    client = fastapi_testclient.TestClient(create_app(tmp_path / "semantic.sqlite"))
    seen = {"embedding_model_id": None, "reranker_model_id": None}

    class FakeEmbeddingBackend:
        def __init__(self, model_id: str) -> None:
            seen["embedding_model_id"] = model_id

        def embed_texts(self, texts):
            return [[1.0, 0.0] for _ in texts]

    class FakeRerankerBackend:
        def __init__(self, model_id: str) -> None:
            seen["reranker_model_id"] = model_id

        def score_pairs(self, pairs):
            return [0.91 for _ in pairs]

    def fake_semantic_chunk_matches(*_args, **_kwargs):
        return [
            MatchEvidence(
                kind="possible_paraphrase",
                suspicious_chunk_id="suspicious:0",
                source_chunk_id="source:0",
                score=0.73,
                suspicious_start=0,
                suspicious_end=5,
                source_start=0,
                source_end=5,
                explanation="Semantic match.",
            )
        ]

    monkeypatch.setattr(api_module, "SentenceTransformerBackend", FakeEmbeddingBackend)
    monkeypatch.setattr(api_module, "SentenceTransformerRerankerBackend", FakeRerankerBackend)
    monkeypatch.setattr(api_module, "semantic_chunk_matches", fake_semantic_chunk_matches)

    scan = client.post(
        "/scans/pair",
        json={
            "suspicious_text": "hola mundo",
            "source_text": "hola mundo",
            "suspicious_document_id": "suspicious",
            "source_document_id": "source",
            "multilingual_embedding_model_id": "intfloat_multilingual_e5_small",
            "reranker_model_id": "cross_encoder_ms_marco_minilm_l6_v2",
        },
    )

    assert scan.status_code == 200
    payload = scan.json()
    assert payload["selected_embedding_model_id"] == "intfloat_multilingual_e5_small"
    assert payload["selected_reranker_model_id"] == "cross_encoder_ms_marco_minilm_l6_v2"
    assert seen["embedding_model_id"] == "intfloat/multilingual-e5-small"
    assert seen["reranker_model_id"] == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert payload["matches"][0]["score"] == 0.91
