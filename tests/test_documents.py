import pytest

from alcove_dux.documents import (
    Document,
    chunk_text,
    is_public_document_id,
    load_document_file,
    normalize_text,
    public_document_id,
    sha256_text,
)


def test_normalize_text_preserves_paragraph_boundary():
    text = " First   line \r\n still first\r\n\r\n\r\n Second\tparagraph "

    assert normalize_text(text) == "First line\nstill first\n\nSecond paragraph"


def test_document_from_text_is_deterministic():
    one = Document.from_text("hello   world")
    two = Document.from_text("hello world")

    assert one.sha256 == two.sha256
    assert one.sha256 == sha256_text("hello world")
    assert one.id == f"doc:{one.sha256[:16]}"
    assert one.segments[0].kind == "paragraph"
    assert one.segments[0].start == 0
    assert one.segments[0].end == len("hello world")


def test_document_from_text_keeps_public_safe_id():
    document = Document.from_text("hello world", document_id="source-a")

    assert document.id == "source-a"


def test_public_document_id_sanitizes_private_identifiers():
    assert public_document_id("student@example.com").startswith("doc:")
    assert public_document_id("/private/source.txt").startswith("doc:")
    assert public_document_id("Essay Draft.docx").startswith("doc:")
    assert public_document_id("Student-Jane-Doe").startswith("doc:")
    assert public_document_id("john-smith-paper").startswith("doc:")
    assert public_document_id("SourceA").startswith("doc:")


def test_public_document_id_keeps_short_opaque_lowercase_ids():
    assert public_document_id("source-a") == "source-a"
    assert public_document_id("corpus:1") == "corpus:1"
    assert public_document_id("sample_02") == "sample_02"


def test_is_public_document_id_rejects_private_labels():
    assert is_public_document_id("source-a")
    assert not is_public_document_id("Student-Jane-Doe")
    assert not is_public_document_id("paper.docx")


def test_chunk_text_splits_long_paragraph_with_overlap():
    chunks = chunk_text("abcdefghij", document_id="doc", max_chars=5, overlap_chars=2)

    assert [chunk.text for chunk in chunks] == ["abcde", "defgh", "ghij"]
    assert [chunk.id for chunk in chunks] == ["doc:0", "doc:1", "doc:2"]


def test_chunk_text_rejects_invalid_window():
    with pytest.raises(ValueError):
        chunk_text("hello", max_chars=10, overlap_chars=10)


def test_load_document_file_reads_text_and_markdown(tmp_path):
    text_path = tmp_path / "paper.txt"
    markdown_path = tmp_path / "notes.md"
    text_path.write_text("Alpha   beta", encoding="utf-8")
    markdown_path.write_text("# Title\n\nGamma delta", encoding="utf-8")

    text_document = load_document_file(text_path, document_id="text")
    markdown_document = load_document_file(markdown_path, document_id="markdown")

    assert text_document.text == "Alpha beta"
    assert markdown_document.text == "# Title\n\nGamma delta"
    assert text_document.metadata["file_type"] == "txt"
    assert [segment.label for segment in markdown_document.segments] == [
        "paragraph 1",
        "paragraph 2",
    ]


def test_load_document_file_rejects_unsupported_type(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b", encoding="utf-8")

    with pytest.raises(ValueError):
        load_document_file(path)
