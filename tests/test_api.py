import pytest

from alcove_dux.api import _dashboard_html, create_app


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
