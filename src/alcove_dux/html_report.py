"""Static HTML rendering for Alcove Dux reports."""

from __future__ import annotations

from html import escape
from typing import Any


def render_report_html(report: dict[str, Any]) -> str:
    """Render a privacy-preserving static HTML report."""

    matches = list(report.get("matches", []))
    source_documents = list(report.get("source_documents", []))
    top_score = max((float(match.get("score", 0)) for match in matches), default=0.0)
    match_rows = "\n".join(
        _render_match_row(index, match) for index, match in enumerate(matches, 1)
    )
    source_rows = "\n".join(_render_source_row(document) for document in source_documents)

    if not match_rows:
        match_rows = '<tr><td colspan="7">No matches crossed the configured threshold.</td></tr>'
    if not source_rows:
        source_rows = '<tr><td colspan="2">No source document inventory was included.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alcove Dux Scan Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202124;
      --muted: #5f6368;
      --line: #dadce0;
      --panel: #f8fafd;
      --accent: #0b57d0;
      --soft: #e8f0fe;
      --exact: #137333;
      --near: #b06000;
      --review: #a50e0e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.5;
    }}
    .skip-link {{
      position: absolute;
      left: 12px;
      top: -48px;
      z-index: 10;
      background: #fff;
      color: var(--accent);
      border: 2px solid var(--accent);
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
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    a:focus-visible {{
      outline: 3px solid #174ea6;
      outline-offset: 2px;
    }}
    h1, h2 {{
      margin: 0;
      letter-spacing: 0;
    }}
    h1 {{
      font-size: 2rem;
      line-height: 1.15;
    }}
    h2 {{
      font-size: 1rem;
      margin-bottom: 12px;
    }}
    .eyebrow {{
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 24px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--panel);
    }}
    .metric dt {{
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      margin-bottom: 4px;
    }}
    .metric dd {{
      display: block;
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0;
      overflow-wrap: anywhere;
    }}
    section {{
      margin-top: 28px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      font-size: 0.92rem;
    }}
    caption {{
      text-align: left;
      font-weight: 700;
      margin-bottom: 8px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--soft);
      font-size: 0.78rem;
      text-transform: uppercase;
      color: #174ea6;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.86em;
      overflow-wrap: anywhere;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--soft);
      color: #174ea6;
      font-weight: 650;
      white-space: nowrap;
    }}
    .badge.exact_token_sequence, .badge.exact_overlap {{
      background: #e6f4ea;
      color: var(--exact);
    }}
    .badge.near_duplicate, .badge.lexical_similarity {{
      background: #fef7e0;
      color: var(--near);
    }}
    .badge.needs_review {{
      background: #fce8e6;
      color: var(--review);
    }}
    .note {{
      color: var(--muted);
      max-width: 760px;
      margin-top: 8px;
    }}
    @media (max-width: 780px) {{
      main {{ width: min(100vw - 20px, 1180px); padding-top: 20px; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <main id="main-content" tabindex="-1">
    <p class="eyebrow">Alcove Dux evidence report</p>
    <h1>Scan {escape(str(report.get("scan_id", "unknown")))}</h1>
    <p class="note">
      This report shows similarity evidence and offsets. It does not include private
      document text or local file paths.
    </p>

    <dl class="summary" aria-label="Scan summary">
      <div class="metric"><dt>Matches</dt><dd>{len(matches)}</dd></div>
      <div class="metric"><dt>Top score</dt><dd>{top_score:.2f}</dd></div>
      <div class="metric">
        <dt>Submitted document</dt>
        <dd><code>{escape(str(report.get("suspicious_document_id", "")))}</code></dd>
      </div>
      <div class="metric">
        <dt>Source scope</dt>
        <dd><code>{escape(str(report.get("source_document_id", "")))}</code></dd>
      </div>
    </dl>

    <section aria-labelledby="run-metadata-heading">
      <h2 id="run-metadata-heading">Run Metadata</h2>
      <table>
        <caption>Run metadata</caption>
        <tbody>
          {_metadata_row("Generated", report.get("generated_at"))}
          {_metadata_row("Schema version", report.get("schema_version"))}
          {_metadata_row("Catalog schema", report.get("catalog_schema_version"))}
          {_metadata_row("Embedding model", report.get("selected_embedding_model_id"))}
          {_metadata_row("Reranker model", report.get("selected_reranker_model_id"))}
          {_metadata_row("Submitted SHA-256", report.get("suspicious_document_sha256"))}
          {_metadata_row("Source SHA-256", report.get("source_document_sha256"))}
        </tbody>
      </table>
    </section>

    <section aria-labelledby="source-documents-heading">
      <h2 id="source-documents-heading">Source Documents</h2>
      <table>
        <caption>Source document inventory</caption>
        <thead><tr><th scope="col">Document ID</th><th scope="col">SHA-256</th></tr></thead>
        <tbody>
          {source_rows}
        </tbody>
      </table>
    </section>

    <section aria-labelledby="evidence-heading">
      <h2 id="evidence-heading">Evidence</h2>
      <table>
        <caption>Matched evidence spans</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Kind</th>
            <th scope="col">Score</th>
            <th scope="col">Suspicious Offset</th>
            <th scope="col">Source Offset</th>
            <th scope="col">Chunk IDs</th>
            <th scope="col">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {match_rows}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def render_local_review_html(
    report: dict[str, Any],
    *,
    suspicious_text: str,
    source_texts: dict[str, str],
) -> str:
    """Render a local-only review report with matched text snippets."""

    matches = list(report.get("matches", []))
    evidence_rows = "\n".join(
        _render_review_match(
            index,
            match,
            suspicious_text=suspicious_text,
            source_texts=source_texts,
        )
        for index, match in enumerate(matches, 1)
    )
    if not evidence_rows:
        evidence_rows = "<section><p>No matches crossed the configured threshold.</p></section>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alcove Dux Local Review</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #202124;
      background: #fff;
      line-height: 1.55;
    }}
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    h1 {{ margin: 0; font-size: 2rem; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 1rem; letter-spacing: 0; }}
    .note {{ max-width: 780px; color: #5f6368; }}
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
    section {{
      border-top: 1px solid #dadce0;
      padding-top: 18px;
      margin-top: 24px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}
    .pane {{
      border: 1px solid #dadce0;
      border-radius: 8px;
      padding: 14px;
      min-height: 160px;
      background: #f8fafd;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }}
    .meta {{
      color: #5f6368;
      font-size: 0.86rem;
      margin: 0 0 10px;
    }}
    mark {{
      background: #fff2cc;
      color: inherit;
      padding: 0 2px;
    }}
    a:focus-visible {{
      outline: 3px solid #174ea6;
      outline-offset: 2px;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.86em;
    }}
    @media (max-width: 780px) {{
      main {{ width: min(100vw - 20px, 1180px); padding-top: 20px; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <main id="main-content" tabindex="-1">
    <h1>Local Review</h1>
    <p class="note">
      This local-only report includes source text snippets for human review. Use the
      standard HTML export when sharing evidence outside this machine.
    </p>
    {evidence_rows}
  </main>
</body>
</html>
"""


def _metadata_row(label: str, value: object) -> str:
    shown = "" if value is None else str(value)
    return f'<tr><th scope="row">{escape(label)}</th><td><code>{escape(shown)}</code></td></tr>'


def _render_source_row(document: object) -> str:
    if not isinstance(document, dict):
        return '<tr><th scope="row">Invalid source document</th><td></td></tr>'
    document_id = escape(str(document.get("id", "")))
    sha256 = escape(str(document.get("sha256") or ""))
    return f'<tr><th scope="row"><code>{document_id}</code></th><td><code>{sha256}</code></td></tr>'


def _render_match_row(index: int, match: object) -> str:
    if not isinstance(match, dict):
        return f'<tr><th scope="row">{index}</th><td colspan="6">Invalid match entry</td></tr>'
    kind = str(match.get("kind", "needs_review"))
    score = _format_score(match.get("score"))
    suspicious_offset = _offset(match.get("suspicious_start"), match.get("suspicious_end"))
    source_offset = _offset(match.get("source_start"), match.get("source_end"))
    chunk_ids = (
        f"<code>{escape(str(match.get('suspicious_chunk_id', '')))}</code><br>"
        f"<code>{escape(str(match.get('source_chunk_id', '')))}</code>"
    )
    return (
        f'<tr><th scope="row">{index}</th>'
        f'<td><span class="badge {escape(kind)}">{escape(kind)}</span></td>'
        f"<td>{score}</td>"
        f"<td><code>{suspicious_offset}</code></td>"
        f"<td><code>{source_offset}</code></td>"
        f"<td>{chunk_ids}</td>"
        f"<td>{escape(str(match.get('explanation', '')))}</td></tr>"
    )


def _offset(start: object, end: object) -> str:
    return f"{start}-{end}" if start is not None and end is not None else ""


def _format_score(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return ""


def _render_review_match(
    index: int,
    match: object,
    *,
    suspicious_text: str,
    source_texts: dict[str, str],
) -> str:
    if not isinstance(match, dict):
        return f"<section><h2>Evidence {index}</h2><p>Invalid match entry.</p></section>"
    source_id = _source_id_for_match(match, source_texts)
    source_text = source_texts.get(source_id, "")
    kind = escape(str(match.get("kind", "needs_review")))
    score = _format_score(match.get("score"))
    suspicious_snippet = _highlighted_snippet(
        suspicious_text,
        match.get("suspicious_start"),
        match.get("suspicious_end"),
    )
    source_snippet = _highlighted_snippet(
        source_text,
        match.get("source_start"),
        match.get("source_end"),
    )
    suspicious_offset = _offset(match.get("suspicious_start"), match.get("suspicious_end"))
    source_offset = _offset(match.get("source_start"), match.get("source_end"))
    heading_id = f"evidence-{index}-heading"
    suspicious_id = f"evidence-{index}-submitted"
    source_id_attr = f"evidence-{index}-source"
    return f"""<section aria-labelledby="{heading_id}">
  <h2 id="{heading_id}">Evidence {index}: {kind} ({score})</h2>
  <p class="meta">{escape(str(match.get("explanation", "")))}</p>
  <div class="grid">
    <div>
      <p class="meta" id="{suspicious_id}">Submitted offset <code>{suspicious_offset}</code></p>
      <div
        class="pane"
        role="region"
        aria-labelledby="{heading_id} {suspicious_id}"
      >
        {suspicious_snippet}
      </div>
    </div>
    <div>
      <p class="meta" id="{source_id_attr}">
        Source <code>{escape(source_id)}</code> offset <code>{source_offset}</code>
      </p>
      <div
        class="pane"
        role="region"
        aria-labelledby="{heading_id} {source_id_attr}"
      >
        {source_snippet}
      </div>
    </div>
  </div>
</section>"""


def _source_id_for_match(match: dict[str, Any], source_texts: dict[str, str]) -> str:
    source_chunk_id = str(match.get("source_chunk_id", ""))
    for source_id in sorted(source_texts, key=len, reverse=True):
        if source_chunk_id == source_id or source_chunk_id.startswith(f"{source_id}:"):
            return source_id
    return next(iter(source_texts), "")


def _highlighted_snippet(text: str, start: object, end: object, *, context: int = 160) -> str:
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
        return ""
    start = min(start, len(text))
    end = min(end, len(text))
    snippet_start = max(start - context, 0)
    snippet_end = min(end + context, len(text))
    prefix = "..." if snippet_start > 0 else ""
    suffix = "..." if snippet_end < len(text) else ""
    before = escape(text[snippet_start:start])
    marked = escape(text[start:end])
    after = escape(text[end:snippet_end])
    return (
        f'{prefix}{before}<mark><span class="sr-only">Matched text: </span>'
        f"{marked}</mark>{after}{suffix}"
    )
