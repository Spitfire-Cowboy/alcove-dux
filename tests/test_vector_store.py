import pytest

from alcove_dux.vector_store import ChromaVectorIndex, LocalVectorIndex, VectorRecord


def test_local_vector_index_queries_and_persists(tmp_path):
    index = LocalVectorIndex()
    index.upsert(
        VectorRecord(
            id="a",
            document_id="source",
            chunk_id="source:0",
            start=0,
            end=4,
            vector=(1.0, 0.0),
        )
    )
    index.upsert(
        VectorRecord(
            id="b",
            document_id="source",
            chunk_id="source:1",
            start=5,
            end=9,
            vector=(0.0, 1.0),
        )
    )

    hits = index.query([0.9, 0.1], top_k=1)

    assert hits[0].record.id == "a"

    path = tmp_path / "index.jsonl"
    index.save_jsonl(path)
    restored = LocalVectorIndex.load_jsonl(path)

    assert [record.id for record in restored.records] == ["a", "b"]


def test_local_vector_index_upsert_replaces_existing_record():
    index = LocalVectorIndex(
        [
            VectorRecord(
                id="a",
                document_id="source",
                chunk_id="source:0",
                start=0,
                end=4,
                vector=(1.0, 0.0),
            )
        ]
    )

    index.upsert(
        VectorRecord(
            id="a",
            document_id="source",
            chunk_id="source:0",
            start=0,
            end=4,
            vector=(0.0, 1.0),
        )
    )

    assert len(index.records) == 1
    assert index.query([0.0, 1.0], top_k=1)[0].record.id == "a"


def test_chroma_vector_index_reports_missing_optional_dependency(monkeypatch, tmp_path):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "chromadb":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="vector-chroma"):
        ChromaVectorIndex(tmp_path)
