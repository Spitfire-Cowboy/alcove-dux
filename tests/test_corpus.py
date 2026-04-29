from alcove_dux.corpus import discover_text_files, load_corpus_documents, scan_text_against_corpus


def test_discover_text_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.md").write_text("b")
    (tmp_path / "c.docx").write_text("c")
    (tmp_path / "d.csv").write_text("d")

    paths = discover_text_files(tmp_path)

    assert [path.name for path in paths] == ["a.txt", "b.md", "c.docx"]


def test_scan_text_against_corpus(tmp_path):
    (tmp_path / "source.txt").write_text(
        "Alpha beta gamma delta epsilon zeta eta theta iota.",
        encoding="utf-8",
    )
    corpus = load_corpus_documents(tmp_path)

    result = scan_text_against_corpus(
        "Intro. Alpha beta gamma delta epsilon zeta eta theta iota. Outro.",
        corpus,
    )

    assert len(result.source_documents) == 1
    assert result.matches
    assert result.matches[0].kind == "exact_token_sequence"
