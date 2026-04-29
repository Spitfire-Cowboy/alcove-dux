from alcove_dux.html_report import render_local_review_html, render_report_html


def test_render_report_html_omits_private_text_and_escapes_values():
    html = render_report_html(
        {
            "schema_version": 1,
            "scan_id": "<scan>",
            "suspicious_document_id": "suspicious",
            "source_document_id": "corpus:1",
            "generated_at": "2026-04-28T00:00:00+00:00",
            "suspicious_document_sha256": "a" * 64,
            "source_documents": [{"id": "source", "sha256": "b" * 64}],
            "matches": [
                {
                    "kind": "exact_token_sequence",
                    "suspicious_chunk_id": "suspicious:exact:0",
                    "source_chunk_id": "source:exact:0",
                    "score": 1.0,
                    "suspicious_start": 3,
                    "suspicious_end": 12,
                    "source_start": 0,
                    "source_end": 9,
                    "explanation": "Exact shared token sequence.",
                }
            ],
        }
    )

    assert "&lt;scan&gt;" in html
    assert "Exact shared token sequence." in html
    assert "private" in html
    assert "document text" in html
    assert "Alpha beta gamma" not in html


def test_render_report_html_has_screen_reader_structure():
    html = render_report_html(
        {
            "schema_version": 1,
            "scan_id": "scan",
            "suspicious_document_id": "suspicious",
            "source_document_id": "source",
            "source_documents": [{"id": "source", "sha256": "b" * 64}],
            "matches": [],
        }
    )

    assert 'href="#main-content"' in html
    assert '<main id="main-content" tabindex="-1">' in html
    assert '<dl class="summary" aria-label="Scan summary">' in html
    assert '<caption>Run metadata</caption>' in html
    assert '<caption>Source document inventory</caption>' in html
    assert '<caption>Matched evidence spans</caption>' in html
    assert '<th scope="row">Schema version</th>' in html
    assert '<th scope="col">Document ID</th>' in html
    assert '<th scope="row"><code>source</code></th>' in html


def test_render_local_review_html_highlights_snippets():
    html = render_local_review_html(
        {
            "scan_id": "scan",
            "matches": [
                {
                    "kind": "exact_token_sequence",
                    "suspicious_chunk_id": "suspicious:exact:0",
                    "source_chunk_id": "source:exact:0",
                    "score": 1.0,
                    "suspicious_start": 6,
                    "suspicious_end": 22,
                    "source_start": 0,
                    "source_end": 16,
                    "explanation": "Exact shared token sequence.",
                }
            ],
        },
        suspicious_text="Intro Alpha beta gamma outro",
        source_texts={"source": "Alpha beta gamma source"},
    )

    assert "local-only report includes source text snippets" in html
    assert '<mark><span class="sr-only">Matched text: </span>Alpha beta gamma</mark>' in html
    assert "Exact shared token sequence." in html


def test_render_local_review_html_names_review_regions():
    html = render_local_review_html(
        {
            "scan_id": "scan",
            "matches": [
                {
                    "kind": "exact_token_sequence",
                    "suspicious_chunk_id": "suspicious:exact:0",
                    "source_chunk_id": "source:exact:0",
                    "score": 1.0,
                    "suspicious_start": 0,
                    "suspicious_end": 5,
                    "source_start": 0,
                    "source_end": 5,
                    "explanation": "Exact shared token sequence.",
                }
            ],
        },
        suspicious_text="Alpha beta",
        source_texts={"source": "Alpha source"},
    )

    assert 'href="#main-content"' in html
    assert '<section aria-labelledby="evidence-1-heading">' in html
    assert 'role="region"' in html
    assert 'aria-labelledby="evidence-1-heading evidence-1-submitted"' in html
    assert 'aria-labelledby="evidence-1-heading evidence-1-source"' in html
