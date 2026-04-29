"""Optional FastAPI app for local Alcove Dux scans."""

import os
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from alcove_dux.catalog import load_catalog
from alcove_dux.config import RuntimeConfig
from alcove_dux.documents import Document, load_document_file
from alcove_dux.matching import compare_texts
from alcove_dux.reports import ReportDocument, ScanReport
from alcove_dux.storage import AlcoveDuxStore


def create_app(database_path: str | Path | None = None):
    """Create the optional local API app."""

    try:
        from fastapi import FastAPI, File, Form, HTTPException, UploadFile
        from fastapi.responses import HTMLResponse
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError(
            "The API requires the api extra: python -m pip install -e \".[api]\""
        ) from exc

    store = AlcoveDuxStore(
        database_path or os.environ.get("ALCOVE_DUX_DB_PATH", "data/alcove_dux.sqlite")
    )

    class DocumentCreateRequest(BaseModel):
        text: str = Field(min_length=1)
        document_id: str | None = None
        title: str | None = None

    class PairScanRequest(BaseModel):
        suspicious_text: str = Field(min_length=1)
        source_text: str = Field(min_length=1)
        suspicious_document_id: str = "suspicious"
        source_document_id: str = "source"
        min_score: float = Field(default=0.50, ge=0, le=1)
        embedding_model_id: str | None = None
        long_context_embedding_model_id: str | None = None
        reranker_model_id: str | None = None
        language: str | None = None
        enabled_dataset_ids: list[str] | None = None

    class StoredScanRequest(BaseModel):
        suspicious_document_id: str
        source_document_id: str
        min_score: float = Field(default=0.50, ge=0, le=1)
        embedding_model_id: str | None = None
        long_context_embedding_model_id: str | None = None
        reranker_model_id: str | None = None
        language: str | None = None
        enabled_dataset_ids: list[str] | None = None

    app = FastAPI(title="Alcove Dux", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html(store.list_documents(), store.list_scans())

    @app.post("/ui/documents", response_class=HTMLResponse)
    def create_document_form(
        text: str = Form(min_length=1),
        document_id: str = Form(default=""),
        title: str = Form(default=""),
    ) -> str:
        document = Document.from_text(
            text,
            document_id=document_id or None,
            **({"title": title} if title else {}),
        )
        store.put_document(document)
        return _dashboard_html(store.list_documents(), store.list_scans())

    @app.post("/ui/documents/file", response_class=HTMLResponse)
    async def create_document_file_form(
        file: UploadFile = File(),  # noqa: B008 - FastAPI dependency marker
        document_id: str = Form(default=""),
        title: str = Form(default=""),
    ) -> str:
        try:
            document = await _document_from_upload(file, document_id=document_id or None)
        except (RuntimeError, ValueError) as error:
            return _dashboard_html(
                store.list_documents(),
                store.list_scans(),
                message=str(error),
            )
        metadata = dict(document.metadata)
        if title:
            metadata["title"] = title
            document = Document(
                id=document.id,
                text=document.text,
                sha256=document.sha256,
                metadata=metadata,
                segments=document.segments,
            )
        store.put_document(document)
        return _dashboard_html(store.list_documents(), store.list_scans())

    @app.post("/ui/scans", response_class=HTMLResponse)
    def create_scan_form(
        suspicious_document_id: str = Form(),
        source_document_id: str = Form(),
        min_score: float = Form(default=0.50),
    ) -> str:
        suspicious = store.get_document(suspicious_document_id)
        source = store.get_document(source_document_id)
        if suspicious is None or source is None:
            return _dashboard_html(
                store.list_documents(),
                store.list_scans(),
                message="Document not found.",
            )
        report = _build_pair_report(
            suspicious=Document.from_text(suspicious.text, document_id=suspicious.id),
            source=Document.from_text(source.text, document_id=source.id),
            min_score=min_score,
            embedding_model_id=None,
            long_context_embedding_model_id=None,
            reranker_model_id=None,
            language=None,
            enabled_dataset_ids=None,
        )
        stored = store.put_scan(report)
        return _scan_review_html(store, stored.id)

    @app.get("/ui/scans/{scan_id}", response_class=HTMLResponse)
    def review_scan(scan_id: str) -> str:
        return _scan_review_html(store, scan_id)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/documents")
    def create_document(request: DocumentCreateRequest) -> dict:
        metadata = {"title": request.title} if request.title else {}
        document = Document.from_text(
            request.text,
            document_id=request.document_id,
            **metadata,
        )
        stored = store.put_document(document)
        return stored.summary

    @app.post("/documents/file")
    async def create_document_file(
        file: UploadFile = File(),  # noqa: B008 - FastAPI dependency marker
        document_id: str = Form(default=""),
        title: str = Form(default=""),
    ) -> dict:
        try:
            document = await _document_from_upload(file, document_id=document_id or None)
        except (RuntimeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if title:
            document = Document(
                id=document.id,
                text=document.text,
                sha256=document.sha256,
                metadata={**document.metadata, "title": title},
                segments=document.segments,
            )
        return store.put_document(document).summary

    @app.get("/documents")
    def list_documents() -> list[dict]:
        return store.list_documents()

    @app.get("/documents/{document_id}")
    def get_document(document_id: str) -> dict:
        stored = store.get_document(document_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return {**stored.summary, "text": stored.text}

    @app.get("/documents/{document_id}/chunks")
    def get_document_chunks(document_id: str) -> list[dict]:
        stored = store.get_document(document_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return [chunk.summary for chunk in store.list_chunks(document_id)]

    @app.post("/scans/pair")
    def scan_pair(request: PairScanRequest) -> dict:
        suspicious = Document.from_text(
            request.suspicious_text,
            document_id=request.suspicious_document_id,
        )
        source = Document.from_text(request.source_text, document_id=request.source_document_id)
        report = _build_pair_report(
            suspicious=suspicious,
            source=source,
            min_score=request.min_score,
            embedding_model_id=request.embedding_model_id,
            long_context_embedding_model_id=request.long_context_embedding_model_id,
            reranker_model_id=request.reranker_model_id,
            language=request.language,
            enabled_dataset_ids=request.enabled_dataset_ids,
        )
        store.put_scan(report)
        return report.to_dict()

    @app.post("/scans")
    def scan_stored_documents(request: StoredScanRequest) -> dict:
        suspicious = store.get_document(request.suspicious_document_id)
        source = store.get_document(request.source_document_id)
        if suspicious is None:
            raise HTTPException(status_code=404, detail="Submitted document not found")
        if source is None:
            raise HTTPException(status_code=404, detail="Source document not found")
        report = _build_pair_report(
            suspicious=Document.from_text(suspicious.text, document_id=suspicious.id),
            source=Document.from_text(source.text, document_id=source.id),
            min_score=request.min_score,
            embedding_model_id=request.embedding_model_id,
            long_context_embedding_model_id=request.long_context_embedding_model_id,
            reranker_model_id=request.reranker_model_id,
            language=request.language,
            enabled_dataset_ids=request.enabled_dataset_ids,
        )
        store.put_scan(report)
        return report.to_dict()

    @app.get("/scans")
    def list_scans() -> list[dict]:
        return store.list_scans()

    @app.get("/scans/{scan_id}")
    def get_scan(scan_id: str) -> dict:
        scan = store.get_scan(scan_id)
        if scan is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scan.summary

    @app.get("/scans/{scan_id}/results")
    def get_scan_results(scan_id: str) -> dict:
        scan = store.get_scan(scan_id)
        if scan is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scan.report

    return app


def _build_pair_report(
    *,
    suspicious: Document,
    source: Document,
    min_score: float,
    embedding_model_id: str | None,
    long_context_embedding_model_id: str | None,
    reranker_model_id: str | None,
    language: str | None,
    enabled_dataset_ids: list[str] | None,
) -> ScanReport:
    catalog = load_catalog()
    runtime_config = RuntimeConfig.from_catalog(
        catalog,
        embedding_model_id=embedding_model_id,
        long_context_embedding_model_id=long_context_embedding_model_id,
        reranker_model_id=reranker_model_id,
        language=language,
        baseline_lexical_threshold=min_score,
        enabled_dataset_ids=(tuple(enabled_dataset_ids) if enabled_dataset_ids else None),
    )
    matches = compare_texts(
        suspicious.text,
        source.text,
        suspicious_id=suspicious.id,
        source_id=source.id,
        min_score=min_score,
    )
    return ScanReport.create(
        scan_id=str(uuid4()),
        suspicious_document_id=suspicious.id,
        source_document_id=source.id,
        source_documents=[ReportDocument(id=source.id, sha256=source.sha256)],
        matches=matches,
        suspicious_document_sha256=suspicious.sha256,
        source_document_sha256=source.sha256,
        catalog_schema_version=catalog.schema_version,
        selected_embedding_model_id=runtime_config.embedding_model_id,
        selected_reranker_model_id=runtime_config.reranker_model_id,
        runtime_config=runtime_config.to_dict(),
    )


def _dashboard_html(
    documents: list[dict],
    scans: list[dict],
    *,
    message: str = "",
) -> str:
    document_rows = "\n".join(_document_row(document) for document in documents)
    scan_rows = "\n".join(_scan_row(scan) for scan in scans)
    if not document_rows:
        document_rows = "<tr><td colspan=\"4\">No documents yet.</td></tr>"
    if not scan_rows:
        scan_rows = "<tr><td colspan=\"5\">No scans yet.</td></tr>"
    options = "\n".join(
        f'<option value="{_escape(document["id"])}">{_escape(document["id"])}</option>'
        for document in documents
    )
    if not options:
        options = '<option value="" disabled selected>No documents available</option>'
    notice = (
        f'<p class="notice" role="alert" aria-live="assertive">{_escape(message)}</p>'
        if message
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alcove Dux</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #202124;
      background: #fff;
      line-height: 1.5;
    }}
    .skip-link {{
      position: absolute;
      left: 12px;
      top: -48px;
      z-index: 10;
      background: #fff;
      color: #0b57d0;
      border: 2px solid #0b57d0;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .skip-link:focus {{ top: 12px; }}
    .sr-only {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 28px 0; }}
    h1 {{ margin: 0 0 20px; font-size: 2rem; letter-spacing: 0; }}
    h2 {{ margin: 28px 0 10px; font-size: 1.05rem; letter-spacing: 0; }}
    form {{ display: grid; gap: 10px; max-width: 760px; }}
    .scan-form {{ display: block; max-width: none; }}
    label {{ display: grid; gap: 4px; font-size: 0.88rem; color: #5f6368; }}
    input, select, textarea {{
      width: 100%;
      border: 1px solid #dadce0;
      border-radius: 6px;
      padding: 9px 10px;
      font: inherit;
      color: #202124;
      background: #fff;
    }}
    textarea {{ min-height: 130px; resize: vertical; }}
    button {{
      border: 0;
      border-radius: 6px;
      padding: 10px 14px;
      background: #0b57d0;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }}
    button:focus-visible,
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    a:focus-visible {{
      outline: 3px solid #174ea6;
      outline-offset: 2px;
    }}
    fieldset {{ border: 0; padding: 0; margin: 0; display: grid; gap: 10px; }}
    legend {{ font-weight: 700; margin-bottom: 4px; }}
    .scan-form fieldset {{
      grid-template-columns: repeat(3, minmax(0, 1fr)) auto;
      align-items: end;
    }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid #dadce0; }}
    caption {{ text-align: left; font-weight: 700; margin-bottom: 8px; }}
    th, td {{ border-bottom: 1px solid #dadce0; padding: 9px 10px; text-align: left; }}
    th {{ background: #e8f0fe; color: #174ea6; font-size: 0.78rem; text-transform: uppercase; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    a {{ color: #0b57d0; font-weight: 650; }}
    .notice {{ color: #a50e0e; font-weight: 650; }}
    @media (max-width: 780px) {{
      main {{ width: min(100vw - 20px, 1180px); }}
      .scan-form fieldset {{ grid-template-columns: 1fr; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <main id="main-content" tabindex="-1">
    <h1>Alcove Dux</h1>
    {notice}

    <section aria-labelledby="documents-heading">
    <h2 id="documents-heading">Documents</h2>
    <form method="post" action="/ui/documents" aria-labelledby="paste-document-heading">
      <fieldset>
      <legend id="paste-document-heading">Add pasted text</legend>
      <label for="document-id">
        Document ID
        <input id="document-id" name="document_id" autocomplete="off">
      </label>
      <label for="document-title">
        Title
        <input id="document-title" name="title" autocomplete="off">
      </label>
      <label for="document-text">
        Text
        <textarea id="document-text" name="text" required></textarea>
      </label>
      <button type="submit">Add Document</button>
      </fieldset>
    </form>
    <form
      method="post"
      action="/ui/documents/file"
      enctype="multipart/form-data"
      aria-labelledby="upload-document-heading"
    >
      <fieldset>
      <legend id="upload-document-heading">Upload a document file</legend>
      <label for="upload-document-id">
        Document ID
        <input id="upload-document-id" name="document_id" autocomplete="off">
      </label>
      <label for="upload-document-title">
        Title
        <input id="upload-document-title" name="title" autocomplete="off">
      </label>
      <label for="upload-file">File<input id="upload-file" name="file" type="file" required></label>
      <button type="submit">Upload File</button>
      </fieldset>
    </form>
    <table>
      <caption>Stored documents</caption>
      <thead>
        <tr>
          <th scope="col">ID</th>
          <th scope="col">SHA-256</th>
          <th scope="col">Length</th>
          <th scope="col">Created</th>
        </tr>
      </thead>
      <tbody>{document_rows}</tbody>
    </table>
    </section>

    <section aria-labelledby="new-scan-heading">
    <h2 id="new-scan-heading">New Scan</h2>
    <form class="scan-form" method="post" action="/ui/scans" aria-describedby="threshold-help">
      <fieldset>
      <legend class="sr-only">Run a scan between two stored documents</legend>
      <label for="suspicious-document-id">
        Suspicious
        <select id="suspicious-document-id" name="suspicious_document_id">{options}</select>
      </label>
      <label for="source-document-id">
        Source
        <select id="source-document-id" name="source_document_id">{options}</select>
      </label>
      <label for="min-score">
        Threshold
        <input
          id="min-score"
          name="min_score"
          type="number"
          min="0"
          max="1"
          step="0.01"
          value="0.50"
        >
      </label>
      <p id="threshold-help" class="sr-only">Threshold accepts values from 0 to 1.</p>
      <button type="submit">Run Scan</button>
      </fieldset>
    </form>
    </section>

    <section aria-labelledby="scans-heading">
    <h2 id="scans-heading">Scans</h2>
    <table>
      <caption>Completed scans</caption>
      <thead>
        <tr>
          <th scope="col">ID</th>
          <th scope="col">Status</th>
          <th scope="col">Matches</th>
          <th scope="col">Top Score</th>
          <th scope="col">Created</th>
        </tr>
      </thead>
      <tbody>{scan_rows}</tbody>
    </table>
    </section>
  </main>
</body>
</html>
"""


def _scan_review_html(store: AlcoveDuxStore, scan_id: str) -> str:
    from alcove_dux.html_report import render_local_review_html, render_report_html

    scan = store.get_scan(scan_id)
    if scan is None:
        return _dashboard_html(
            store.list_documents(),
            store.list_scans(),
            message="Scan not found.",
        )
    suspicious_id = str(scan.report.get("suspicious_document_id", ""))
    source_documents = scan.report.get("source_documents", [])
    suspicious = store.get_document(suspicious_id)
    source_texts = {}
    for source_document in source_documents:
        if not isinstance(source_document, dict):
            continue
        source = store.get_document(str(source_document.get("id", "")))
        if source is not None:
            source_texts[source.id] = source.text
    if suspicious is None or not source_texts:
        return render_report_html(scan.report)
    return render_local_review_html(
        scan.report,
        suspicious_text=suspicious.text,
        source_texts=source_texts,
    )


async def _document_from_upload(file: Any, *, document_id: str | None) -> Document:
    filename = file.filename or "upload.txt"
    suffix = Path(filename).suffix
    if suffix.casefold() not in {".txt", ".md", ".markdown", ".pdf", ".docx"}:
        raise ValueError(f"Unsupported document type: {suffix or 'none'}")
    content = await file.read()
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
        return load_document_file(temporary_path, document_id=document_id)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _document_row(document: dict) -> str:
    return (
        "<tr>"
        f"<th scope=\"row\"><code>{_escape(document['id'])}</code></th>"
        f"<td><code>{_escape(document['sha256'])}</code></td>"
        f"<td>{document['text_length']}</td>"
        f"<td>{_escape(document['created_at'])}</td>"
        "</tr>"
    )


def _scan_row(scan: dict) -> str:
    scan_id = _escape(scan["id"])
    return (
        "<tr>"
        f'<th scope="row"><a href="/ui/scans/{scan_id}"><code>{scan_id}</code></a></th>'
        f"<td>{_escape(scan['status'])}</td>"
        f"<td>{scan['match_count']}</td>"
        f"<td>{float(scan['top_score']):.2f}</td>"
        f"<td>{_escape(scan['created_at'])}</td>"
        "</tr>"
    )


def _escape(value: object) -> str:
    import html

    return html.escape(str(value), quote=True)
