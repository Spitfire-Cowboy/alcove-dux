from __future__ import annotations

import importlib.util
import json
import sys
import types
from argparse import Namespace
from collections import Counter
from pathlib import Path


def load_batch_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "pes2o_chroma_batch.py"
    spec = importlib.util.spec_from_file_location("pes2o_chroma_batch", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def batch_args(**overrides):
    defaults = {
        "run_id": "unit-run",
        "model_id": "BAAI/bge-small-en-v1.5",
        "device": "cpu",
        "collection_name": "pes2o_train_bge_small",
        "collection_shard_size": None,
        "target_passages": 1_000_000,
        "batch_passages": 25_000,
        "flush_size": 512,
        "max_seconds": 600,
        "max_upsert_seconds": None,
        "min_passages_per_second": None,
        "total_shards": 20,
        "gpu_max_temp_c": 82.0,
        "no_gpu_temp_check": False,
        "out_root": Path("reports/live-fire"),
        "index_root": Path("vectorstores"),
        "hf_cache": None,
        "fresh": False,
        "plan_only": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_first_passage_requires_and_truncates_words():
    module = load_batch_module()
    assert module.first_passage("too short") is None

    text = " ".join(f"word{i}" for i in range(100))
    assert module.first_passage(text, max_words=80) == " ".join(f"word{i}" for i in range(80))


def test_next_batch_plan_uses_resume_state(tmp_path):
    module = load_batch_module()
    args = batch_args(batch_passages=10_000, flush_size=256)
    state = module.load_state(tmp_path / "missing.json", args=args, index_dir=tmp_path / "index")
    state["next_shard"] = 3
    state["next_line"] = 42
    state["batch_number"] = 7

    plan = module.next_batch_plan(state, args=args, index_dir=tmp_path / "index")

    assert plan["next_shard"] == 3
    assert plan["next_line"] == 42
    assert plan["next_batch_number"] == 8
    assert plan["batch_passages"] == 10_000
    assert plan["flush_size"] == 256
    assert plan["max_upsert_seconds"] is None
    assert plan["min_passages_per_second"] is None
    assert plan["collection_shard_size"] is None
    assert plan["total_shards"] == 20


def test_state_from_report_preserves_resume_cursor(tmp_path):
    module = load_batch_module()
    args = batch_args()
    report = module.make_report(
        {"created": "1970-01-01T00:00:00Z"},
        args=args,
        index_dir=tmp_path / "index",
        batch_number=2,
        status="batch_complete",
        collection_count_before=25_000,
        collection_count_after=50_000,
        indexed_this_run=25_000,
        lines_scanned=30_000,
        short_passages_skipped=5_000,
        source_counts=Counter({"pubmed": 10}),
        embed_seconds=20.0,
        upsert_seconds=40.0,
        elapsed_seconds=80.0,
        next_position=module.ScanPosition(shard=1, line=123),
        note="done",
        active_collection_name="pes2o_train_bge_small",
        shard_counts={"pes2o_train_bge_small": 50_000},
    )

    state = module.state_from_report(report)

    assert state["next_shard"] == 1
    assert state["next_line"] == 123
    assert state["batch_number"] == 2
    assert state["status"] == "batch_complete"
    assert state["total_shards"] == 20
    assert state["max_upsert_seconds"] is None
    assert state["min_passages_per_second"] is None
    assert state["collection_shard_size"] is None


def test_collection_shard_names_and_selection():
    module = load_batch_module()

    assert module.collection_shard_name("base", 0) == "base"
    assert module.collection_shard_name("base", 2) == "base_shard_0002"
    assert module.collection_shard_index("base", "base") == 0
    assert module.collection_shard_index("base", "base_shard_0002") == 2
    assert module.collection_shard_index("base", "other") is None


def test_current_gpu_temp_ignores_missing_nvidia_smi(monkeypatch):
    module = load_batch_module()

    def raise_missing(*args, **kwargs):
        raise FileNotFoundError("nvidia-smi")

    monkeypatch.setattr(module.subprocess, "run", raise_missing)

    assert module.current_gpu_temp_c() is None


def test_prepare_embedding_texts_adds_e5_prefixes_only_for_e5_models():
    module = load_batch_module()

    assert module.prepare_embedding_texts("BAAI/bge-small", ["hello"], role="passage") == [
        "hello"
    ]
    assert module.prepare_embedding_texts(
        "intfloat/multilingual-e5-small",
        ["hello"],
        role="query",
    ) == ["query: hello"]
    assert module.prepare_embedding_texts(
        "intfloat/e5-base-v2",
        ["hello"],
        role="passage",
    ) == ["passage: hello"]


def test_temperature_pause_after_exhaustion_preserves_resume_cursor(
    monkeypatch,
    tmp_path,
):
    module = load_batch_module()

    class FakeModel:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, **kwargs):
            return [[0.1] for _ in texts]

    class FakeCollection:
        name = "pes2o_train_bge_small"

        def count(self):
            return 0

        def upsert(self, **kwargs):
            raise AssertionError("temperature pause should happen before upsert")

    class FakeClient:
        def list_collections(self):
            return []

        def get_or_create_collection(self, **kwargs):
            return FakeCollection()

    class ExhaustedScanner:
        def __init__(self, *, start, total_shards, cache_dir):
            self.position = start
            self.lines_scanned = 0
            self.short_passages_skipped = 0
            self.exhausted = False

        def __iter__(self):
            self.lines_scanned = 1
            yield module.Passage(
                id="pes2o-train-00000-000000000",
                text=" ".join(f"word{i}" for i in range(100)),
                source="unit",
                shard=0,
                line=0,
                next_position=module.ScanPosition(shard=0, line=1),
            )
            self.exhausted = True
            self.position = module.ScanPosition(shard=1, line=0)

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=FakeModel),
    )
    monkeypatch.setitem(
        sys.modules,
        "chromadb",
        types.SimpleNamespace(PersistentClient=lambda **kwargs: FakeClient()),
    )
    monkeypatch.setattr(module, "Pes2oScanner", ExhaustedScanner)
    temps = iter([40.0, 90.0])
    monkeypatch.setattr(module, "current_gpu_temp_c", lambda: next(temps))

    args = batch_args(
        out_root=tmp_path / "reports",
        index_root=tmp_path / "index",
        batch_passages=10,
        flush_size=10,
        total_shards=1,
    )

    assert module.run(args) == 0

    latest = json.loads((tmp_path / "reports" / "unit-run" / "latest.json").read_text())
    assert latest["status"] == "temperature_pause"
    assert latest["next_shard"] == 0
    assert latest["next_line"] == 0
    assert latest["indexed_this_run"] == 0
