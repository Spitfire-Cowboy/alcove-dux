from pathlib import Path

from alcove_dux.datasets.pan import iter_pan_pairs, iter_pan_pc11_documents, iter_pan_pc11_pairs


def test_iter_pan_pairs_loads_annotations(tmp_path):
    root = tmp_path
    (root / "susp").mkdir()
    (root / "src").mkdir()
    (root / "02-no-obfuscation").mkdir()
    (root / "pairs").write_text("suspicious-document00001.txt source-document00002.txt\n")
    (root / "susp" / "suspicious-document00001.txt").write_text("suspicious")
    (root / "src" / "source-document00002.txt").write_text("source")
    (root / "02-no-obfuscation" / "suspicious-document00001-source-document00002.xml").write_text(
        '<document reference="suspicious-document00001.txt">'
        '<feature name="plagiarism" obfuscation="none" source_length="5" '
        'source_offset="10" source_reference="source-document00002.txt" '
        'this_length="5" this_offset="20" type="artificial" />'
        "</document>"
    )

    pairs = iter_pan_pairs(root)

    assert len(pairs) == 1
    assert pairs[0].suspicious_path == Path(root / "susp" / "suspicious-document00001.txt")
    assert len(pairs[0].annotations) == 1
    assert pairs[0].annotations[0].source_offset == 10


def test_iter_pan_pc11_documents_loads_sibling_annotations(tmp_path):
    root = tmp_path
    susp_dir = root / "external-detection-corpus" / "suspicious-documents"
    source_dir = root / "external-detection-corpus" / "source-documents"
    susp_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    suspicious = susp_dir / "suspicious-document00001.txt"
    source = source_dir / "source-document00002.txt"
    suspicious.write_text("suspicious", encoding="utf-8")
    source.write_text("source", encoding="utf-8")
    suspicious.with_suffix(".xml").write_text(
        '<document reference="suspicious-document00001.txt">'
        '<feature name="plagiarism" obfuscation="translation" source_length="7" '
        'source_offset="11" source_reference="source-document00002.txt" '
        'this_length="5" this_offset="3" type="artificial" />'
        "</document>",
        encoding="utf-8",
    )

    documents = iter_pan_pc11_documents(root)
    pairs = iter_pan_pc11_pairs(root)

    assert len(documents) == 1
    assert documents[0].reference == "suspicious-document00001.txt"
    assert documents[0].annotations[0].obfuscation == "translation"
    assert len(pairs) == 1
    assert pairs[0].source_path == source
    assert pairs[0].annotations[0].suspicious_offset == 3


def test_iter_pan_pc11_pairs_honors_limit(tmp_path):
    for index in range(2):
        suspicious = tmp_path / f"suspicious-document0000{index}.txt"
        source = tmp_path / f"source-document0000{index}.txt"
        suspicious.write_text("suspicious", encoding="utf-8")
        source.write_text("source", encoding="utf-8")
        suspicious.with_suffix(".xml").write_text(
            f'<document reference="{suspicious.name}">'
            '<feature name="plagiarism" source_length="1" '
            f'source_offset="0" source_reference="{source.name}" '
            'this_length="1" this_offset="0" />'
            "</document>",
            encoding="utf-8",
        )

    pairs = iter_pan_pc11_pairs(tmp_path, limit=1)

    assert len(pairs) == 1
