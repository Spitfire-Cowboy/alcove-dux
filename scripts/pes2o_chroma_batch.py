"""Index peS2o passages into Chroma in short, resumable batches.

This script is intentionally process-bounded. Each invocation indexes the next
slice of peS2o, writes state/progress JSON, and exits so local machines can run
large Chroma indexing jobs in resumable steps.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_RUN_ID = "pes2o-train-1m-bge-chroma-batched"
DEFAULT_MODEL_ID = "BAAI/bge-small-en-v1.5"
DEFAULT_COLLECTION = "pes2o_train_bge_small"
DEFAULT_TARGET_PASSAGES = 1_000_000
DEFAULT_BATCH_PASSAGES = 25_000
DEFAULT_FLUSH_SIZE = 512
DEFAULT_MAX_SECONDS = 600
DEFAULT_GPU_MAX_TEMP_C = 82.0
DEFAULT_TOTAL_SHARDS = 20
DATASET_ID = "allenai/peS2o:v2-train"

WORD_RE = re.compile(r"\b[\w'-]+\b")


@dataclass(frozen=True)
class ScanPosition:
    """Next dataset row to scan."""

    shard: int
    line: int

    def to_dict(self) -> dict[str, int]:
        return {"next_shard": self.shard, "next_line": self.line}


@dataclass(frozen=True)
class Passage:
    """A passage plus resumable source position."""

    id: str
    text: str
    source: str
    shard: int
    line: int
    next_position: ScanPosition


class Pes2oScanner:
    """Streaming peS2o scanner that remembers the latest line position."""

    def __init__(
        self,
        *,
        start: ScanPosition,
        total_shards: int,
        cache_dir: Path | None,
    ) -> None:
        self.position = start
        self.total_shards = total_shards
        self.cache_dir = cache_dir
        self.lines_scanned = 0
        self.short_passages_skipped = 0
        self.exhausted = False

    def __iter__(self):
        from huggingface_hub import hf_hub_download

        for shard in range(self.position.shard, self.total_shards):
            start_line = self.position.line if shard == self.position.shard else 0
            filename = f"data/v2/train-{shard:05d}-of-{self.total_shards:05d}.json.gz"
            path = hf_hub_download(
                "allenai/peS2o",
                filename=filename,
                repo_type="dataset",
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
            )
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle):
                    if line_number < start_line:
                        continue
                    self.lines_scanned += 1
                    next_position = ScanPosition(shard=shard, line=line_number + 1)
                    self.position = next_position
                    row = json.loads(line)
                    text = first_passage(str(row.get("text", "")))
                    if text is None:
                        self.short_passages_skipped += 1
                        continue
                    source = str(row.get("source", "unknown"))[:80] or "unknown"
                    passage_id = f"pes2o-train-{shard:05d}-{line_number:09d}"
                    yield Passage(
                        id=passage_id,
                        text=text,
                        source=source,
                        shard=shard,
                        line=line_number,
                        next_position=next_position,
                    )
            self.position = ScanPosition(shard=shard + 1, line=0)
        self.exhausted = True
        self.position = ScanPosition(shard=self.total_shards, line=0)


def main() -> int:
    args = parse_args()
    return run(args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch peS2o train passages into Chroma")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--out-root", type=Path, default=Path("reports/live-fire"))
    parser.add_argument("--index-root", type=Path, default=Path("vectorstores"))
    parser.add_argument("--hf-cache", type=Path, help="Hugging Face cache directory")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION)
    parser.add_argument(
        "--collection-shard-size",
        type=int,
        help=(
            "Maximum records per Chroma collection. When set, the base collection "
            "counts as shard 0 and later writes go to suffixed shard collections."
        ),
    )
    parser.add_argument("--target-passages", type=int, default=DEFAULT_TARGET_PASSAGES)
    parser.add_argument("--batch-passages", type=int, default=DEFAULT_BATCH_PASSAGES)
    parser.add_argument("--flush-size", type=int, default=DEFAULT_FLUSH_SIZE)
    parser.add_argument("--max-seconds", type=int, default=DEFAULT_MAX_SECONDS)
    parser.add_argument(
        "--max-upsert-seconds",
        type=float,
        help="Mark the batch as a guardrail stop when Chroma upserts exceed this many seconds",
    )
    parser.add_argument(
        "--min-passages-per-second",
        type=float,
        help="Mark the batch as a guardrail stop when total throughput falls below this value",
    )
    parser.add_argument("--total-shards", type=int, default=DEFAULT_TOTAL_SHARDS)
    parser.add_argument("--gpu-max-temp-c", type=float, default=DEFAULT_GPU_MAX_TEMP_C)
    parser.add_argument("--no-gpu-temp-check", action="store_true")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete this run's report state and vectorstore before starting",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Print the next-batch plan without loading models or touching Chroma",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    validate_positive_args(args)
    out_dir = args.out_root / args.run_id
    index_dir = args.index_root / args.run_id
    state_path = out_dir / "state.json"
    latest_path = out_dir / "latest.json"

    if args.plan_only:
        state = load_state(state_path, args=args, index_dir=index_dir)
        plan = next_batch_plan(state, args=args, index_dir=index_dir)
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if args.fresh:
        reset_run(out_dir=out_dir, index_dir=index_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    state = load_state(state_path, args=args, index_dir=index_dir)

    temp = current_gpu_temp_c() if not args.no_gpu_temp_check else None
    if temp is not None and temp >= args.gpu_max_temp_c:
        report = finish_without_indexing(
            state,
            status="temperature_pause",
            note=f"GPU temperature {temp:.1f}C is at or above limit {args.gpu_max_temp_c:.1f}C.",
            args=args,
            index_dir=index_dir,
            extra={"gpu_temp_c": temp},
        )
        write_report_files(out_dir, state_path, latest_path, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            'peS2o Chroma batching requires: python -m pip install -e ".[semantic,vector-chroma]"'
        ) from exc

    started = time.perf_counter()
    model = SentenceTransformer(args.model_id, device=args.device)
    client = chromadb.PersistentClient(path=str(index_dir))
    shard_counts = collection_shard_counts(client, args.collection_name)
    collection = select_active_collection(client, args, shard_counts)
    active_collection_name = collection.name
    count_before = sum(shard_counts.values())
    if count_before >= args.target_passages:
        report = finish_without_indexing(
            state,
            status="target_reached",
            note="Chroma collection already meets the target passage count.",
            args=args,
            index_dir=index_dir,
            extra={"collection_count_before": count_before},
        )
        write_report_files(out_dir, state_path, latest_path, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    start = ScanPosition(
        shard=int(state.get("next_shard", 0)),
        line=int(state.get("next_line", 0)),
    )
    scanner = Pes2oScanner(start=start, total_shards=args.total_shards, cache_dir=args.hf_cache)
    pending: list[Passage] = []
    source_counts: Counter[str] = Counter()
    indexed_this_run = 0
    embed_seconds = 0.0
    upsert_seconds = 0.0
    status = "batch_complete"
    stop_note = ""
    batch_number = int(state.get("batch_number", 0)) + 1
    last_flush_position = start

    def rotate_active_collection_if_needed() -> None:
        nonlocal collection, active_collection_name
        if args.collection_shard_size is None:
            return
        active_count = shard_counts.get(active_collection_name, 0)
        if active_count < args.collection_shard_size:
            return
        collection = select_active_collection(client, args, shard_counts)
        active_collection_name = collection.name

    def flush_pending() -> bool:
        nonlocal embed_seconds, upsert_seconds, indexed_this_run, last_flush_position, status
        if not pending:
            return True
        while pending:
            rotate_active_collection_if_needed()
            temp_before = current_gpu_temp_c() if not args.no_gpu_temp_check else None
            if temp_before is not None and temp_before >= args.gpu_max_temp_c:
                status = "temperature_pause"
                return False
            chunk_size = len(pending)
            if args.collection_shard_size is not None:
                remaining_in_shard = args.collection_shard_size - shard_counts.get(
                    active_collection_name,
                    0,
                )
                chunk_size = min(chunk_size, max(1, remaining_in_shard))
            chunk = pending[:chunk_size]
            texts = [item.text for item in chunk]
            t0 = time.perf_counter()
            vectors = model.encode(
                prepare_embedding_texts(args.model_id, texts, role="passage"),
                normalize_embeddings=True,
                batch_size=min(128, len(texts)),
                show_progress_bar=False,
            )
            embed_seconds += time.perf_counter() - t0
            embeddings = vectors.tolist() if hasattr(vectors, "tolist") else list(vectors)
            t1 = time.perf_counter()
            collection.upsert(
                ids=[item.id for item in chunk],
                embeddings=embeddings,
                metadatas=[
                    {
                        "document_id": item.id,
                        "chunk_id": f"{item.id}:0",
                        "source": item.source,
                        "start": 0,
                        "end": len(item.text),
                        "shard": item.shard,
                        "line": item.line,
                    }
                    for item in chunk
                ],
            )
            upsert_seconds += time.perf_counter() - t1
            shard_counts[active_collection_name] = int(collection.count())
            indexed_this_run += len(chunk)
            last_flush_position = chunk[-1].next_position
            del pending[:chunk_size]
            interim = make_report(
                state,
                args=args,
                index_dir=index_dir,
                batch_number=batch_number,
                status="running",
                collection_count_before=count_before,
                collection_count_after=sum(shard_counts.values()),
                indexed_this_run=indexed_this_run,
                lines_scanned=scanner.lines_scanned,
                short_passages_skipped=scanner.short_passages_skipped,
                source_counts=source_counts,
                embed_seconds=embed_seconds,
                upsert_seconds=upsert_seconds,
                elapsed_seconds=time.perf_counter() - started,
                next_position=last_flush_position,
                note="Progress checkpoint after a successful Chroma upsert.",
                active_collection_name=active_collection_name,
                shard_counts=shard_counts,
            )
            write_json_atomic(state_path, state_from_report(interim))
            write_json_atomic(latest_path, interim)
        return True

    for passage in scanner:
        if indexed_this_run + len(pending) >= args.batch_passages:
            break
        if count_before + indexed_this_run + len(pending) >= args.target_passages:
            status = "target_reached"
            break
        if pending and time.perf_counter() - started >= args.max_seconds:
            status = "time_budget_reached"
            stop_note = "Time budget reached; flushing pending records before exit."
            break
        pending.append(passage)
        source_counts[passage.source] += 1
        if len(pending) >= args.flush_size and not flush_pending():
            stop_note = "GPU temperature limit reached before the next flush."
            break
        if time.perf_counter() - started >= args.max_seconds:
            status = "time_budget_reached"
            stop_note = "Time budget reached after the latest successful flush."
            break

    if pending and status != "temperature_pause" and not flush_pending():
        stop_note = "GPU temperature limit reached before the next flush."

    if scanner.exhausted and status != "temperature_pause":
        status = "dataset_exhausted"
        last_flush_position = scanner.position
    shard_counts[active_collection_name] = int(collection.count())
    count_after = sum(shard_counts.values())
    final_elapsed = time.perf_counter() - started
    passages_per_second = indexed_this_run / final_elapsed if indexed_this_run else 0.0
    if count_after >= args.target_passages:
        status = "target_reached"
    elif args.max_upsert_seconds is not None and upsert_seconds > args.max_upsert_seconds:
        status = "upsert_guardrail_exceeded"
        stop_note = (
            f"Chroma upsert time {upsert_seconds:.3f}s exceeded guardrail "
            f"{args.max_upsert_seconds:.3f}s."
        )
    elif (
        args.min_passages_per_second is not None
        and indexed_this_run
        and passages_per_second < args.min_passages_per_second
    ):
        status = "throughput_guardrail_exceeded"
        stop_note = (
            f"Total throughput {passages_per_second:.2f}/sec fell below guardrail "
            f"{args.min_passages_per_second:.2f}/sec."
        )
    elif indexed_this_run >= args.batch_passages and status == "batch_complete":
        stop_note = "Batch passage limit reached."
    elif status == "batch_complete" and indexed_this_run == 0:
        status = "no_progress"
        stop_note = "No new passages were indexed in this invocation."

    report = make_report(
        state,
        args=args,
        index_dir=index_dir,
        batch_number=batch_number,
        status=status,
        collection_count_before=count_before,
        collection_count_after=count_after,
        indexed_this_run=indexed_this_run,
        lines_scanned=scanner.lines_scanned,
        short_passages_skipped=scanner.short_passages_skipped,
        source_counts=source_counts,
        embed_seconds=embed_seconds,
        upsert_seconds=upsert_seconds,
        elapsed_seconds=time.perf_counter() - started,
        next_position=last_flush_position,
        note=stop_note or status_note(status),
        active_collection_name=active_collection_name,
        shard_counts=shard_counts,
    )
    write_report_files(out_dir, state_path, latest_path, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def validate_positive_args(args: argparse.Namespace) -> None:
    for name in ("target_passages", "batch_passages", "flush_size", "max_seconds", "total_shards"):
        if int(getattr(args, name)) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")
    if args.collection_shard_size is not None and args.collection_shard_size <= 0:
        raise SystemExit("--collection-shard-size must be positive")


def collection_shard_name(base_name: str, shard_index: int) -> str:
    """Return the Chroma collection name for a logical shard."""

    if shard_index == 0:
        return base_name
    return f"{base_name}_shard_{shard_index:04d}"


def collection_shard_index(base_name: str, collection_name: str) -> int | None:
    """Return the shard index for a collection name, if it belongs to the shard set."""

    if collection_name == base_name:
        return 0
    prefix = f"{base_name}_shard_"
    if not collection_name.startswith(prefix):
        return None
    suffix = collection_name.removeprefix(prefix)
    if not re.fullmatch(r"\d{4}", suffix):
        return None
    return int(suffix)


def collection_names(client: Any) -> list[str]:
    """Return collection names across Chroma versions."""

    names = []
    for item in client.list_collections():
        names.append(str(item if isinstance(item, str) else item.name))
    return names


def collection_shard_counts(client: Any, base_name: str) -> dict[str, int]:
    """Count existing collections that belong to the configured shard set."""

    counts: dict[str, int] = {}
    for name in collection_names(client):
        if collection_shard_index(base_name, name) is None:
            continue
        counts[name] = int(client.get_collection(name).count())
    return dict(
        sorted(
            counts.items(),
            key=lambda item: collection_shard_index(base_name, item[0]) or 0,
        )
    )


def select_active_collection(
    client: Any,
    args: argparse.Namespace,
    shard_counts: dict[str, int],
) -> Any:
    """Return the collection that should receive the next upsert."""

    if args.collection_shard_size is None:
        collection = client.get_or_create_collection(
            name=args.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        shard_counts[args.collection_name] = int(collection.count())
        return collection

    shard_index = 0
    while True:
        name = collection_shard_name(args.collection_name, shard_index)
        if shard_counts.get(name, 0) < args.collection_shard_size:
            collection = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
            shard_counts[name] = int(collection.count())
            return collection
        shard_index += 1


def reset_run(*, out_dir: Path, index_dir: Path) -> None:
    for path in (out_dir, index_dir):
        resolved = path.resolve()
        if resolved.anchor == str(resolved):
            raise SystemExit(f"Refusing to delete root path: {path}")
        if path.exists():
            shutil.rmtree(path)


def load_state(state_path: Path, *, args: argparse.Namespace, index_dir: Path) -> dict[str, Any]:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "run_id": args.run_id,
        "dataset_id": DATASET_ID,
        "model_id": args.model_id,
        "device": args.device,
        "collection_name": args.collection_name,
        "collection_shard_size": args.collection_shard_size,
        "index_dir": str(index_dir),
        "target_passages": args.target_passages,
        "batch_passages": args.batch_passages,
        "flush_size": args.flush_size,
        "total_shards": args.total_shards,
        "next_shard": 0,
        "next_line": 0,
        "batch_number": 0,
        "status": "new",
        "created": utc_now(),
        "updated": utc_now(),
        "notes": [
            "Aggregate metrics only; raw peS2o text is not emitted.",
            "Each invocation is bounded and resumable via next_shard/next_line.",
        ],
    }


def next_batch_plan(
    state: dict[str, Any],
    *,
    args: argparse.Namespace,
    index_dir: Path,
) -> dict[str, Any]:
    return {
        "run_id": args.run_id,
        "dataset_id": DATASET_ID,
        "model_id": args.model_id,
        "device": args.device,
        "index_dir": str(index_dir),
        "collection_name": args.collection_name,
        "collection_shard_size": args.collection_shard_size,
        "target_passages": args.target_passages,
        "batch_passages": args.batch_passages,
        "flush_size": args.flush_size,
        "total_shards": args.total_shards,
        "max_seconds": args.max_seconds,
        "max_upsert_seconds": args.max_upsert_seconds,
        "min_passages_per_second": args.min_passages_per_second,
        "next_shard": int(state.get("next_shard", 0)),
        "next_line": int(state.get("next_line", 0)),
        "next_batch_number": int(state.get("batch_number", 0)) + 1,
    }


def finish_without_indexing(
    state: dict[str, Any],
    *,
    status: str,
    note: str,
    args: argparse.Namespace,
    index_dir: Path,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    position = ScanPosition(
        shard=int(state.get("next_shard", 0)),
        line=int(state.get("next_line", 0)),
    )
    report = make_report(
        state,
        args=args,
        index_dir=index_dir,
        batch_number=int(state.get("batch_number", 0)),
        status=status,
        collection_count_before=int(extra.get("collection_count_before", 0)) if extra else 0,
        collection_count_after=int(extra.get("collection_count_before", 0)) if extra else 0,
        indexed_this_run=0,
        lines_scanned=0,
        short_passages_skipped=0,
        source_counts=Counter(),
        embed_seconds=0.0,
        upsert_seconds=0.0,
        elapsed_seconds=0.0,
        next_position=position,
        note=note,
        active_collection_name=args.collection_name,
        shard_counts={args.collection_name: int(extra.get("collection_count_before", 0))}
        if extra
        else {},
    )
    if extra:
        report.update(extra)
    return report


def make_report(
    state: dict[str, Any],
    *,
    args: argparse.Namespace,
    index_dir: Path,
    batch_number: int,
    status: str,
    collection_count_before: int,
    collection_count_after: int,
    indexed_this_run: int,
    lines_scanned: int,
    short_passages_skipped: int,
    source_counts: Counter[str],
    embed_seconds: float,
    upsert_seconds: float,
    elapsed_seconds: float,
    next_position: ScanPosition,
    note: str,
    active_collection_name: str,
    shard_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "run_id": args.run_id,
        "dataset_id": DATASET_ID,
        "license_note": "ODC-By per the Hugging Face dataset card.",
        "status": status,
        "note": note,
        "batch_number": batch_number,
        "created": state.get("created", utc_now()),
        "updated": utc_now(),
        "model_id": args.model_id,
        "device": args.device,
        "collection_name": args.collection_name,
        "active_collection_name": active_collection_name,
        "collection_shard_size": args.collection_shard_size,
        "collection_shard_counts": dict(
            sorted(
                shard_counts.items(),
                key=lambda item: collection_shard_index(args.collection_name, item[0]) or 0,
            )
        ),
        "index_backend": "ChromaDB PersistentClient hnsw:space=cosine",
        "index_dir": str(index_dir),
        "target_passages": args.target_passages,
        "batch_passages": args.batch_passages,
        "flush_size": args.flush_size,
        "total_shards": args.total_shards,
        "max_seconds": args.max_seconds,
        "max_upsert_seconds": args.max_upsert_seconds,
        "min_passages_per_second": args.min_passages_per_second,
        "collection_count_before": collection_count_before,
        "collection_count_after": collection_count_after,
        "indexed_this_run": indexed_this_run,
        "remaining_to_target": max(0, args.target_passages - collection_count_after),
        "lines_scanned_this_run": lines_scanned,
        "short_passages_skipped_this_run": short_passages_skipped,
        "next_shard": next_position.shard,
        "next_line": next_position.line,
        "embedding_seconds": round(embed_seconds, 3),
        "upsert_seconds": round(upsert_seconds, 3),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "passages_per_second_total": round(indexed_this_run / elapsed_seconds, 2)
        if elapsed_seconds and indexed_this_run
        else 0.0,
        "passages_per_second_embedding_only": round(indexed_this_run / embed_seconds, 2)
        if embed_seconds and indexed_this_run
        else 0.0,
        "source_distribution_top10": source_counts.most_common(10),
        "notes": [
            "Aggregate metrics only; raw peS2o text is not emitted.",
            "Use the same command again to resume from next_shard/next_line.",
            "The script exits after each bounded batch, time budget, target, or temperature stop.",
        ],
    }


def state_from_report(report: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "run_id",
        "dataset_id",
        "model_id",
        "device",
        "collection_name",
        "active_collection_name",
        "collection_shard_size",
        "index_dir",
        "target_passages",
        "batch_passages",
        "flush_size",
        "max_upsert_seconds",
        "min_passages_per_second",
        "total_shards",
        "next_shard",
        "next_line",
        "batch_number",
        "status",
        "created",
        "updated",
        "notes",
    )
    return {key: report[key] for key in keys if key in report}


def write_report_files(
    out_dir: Path,
    state_path: Path,
    latest_path: Path,
    report: dict[str, Any],
) -> None:
    batch_path = out_dir / f"batch-{int(report['batch_number']):04d}.json"
    write_json_atomic(state_path, state_from_report(report))
    write_json_atomic(latest_path, report)
    write_json_atomic(batch_path, report)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def first_passage(text: str, *, max_words: int = 160) -> str | None:
    paragraphs = [
        paragraph.strip().replace("\n", " ")
        for paragraph in text.split("\n\n")
        if len(words(paragraph)) >= 80
    ]
    passage = paragraphs[0] if paragraphs else text.replace("\n", " ")
    tokens = words(passage)
    if len(tokens) < 80:
        return None
    return " ".join(tokens[:max_words])


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def prepare_embedding_texts(model_id: str, texts: list[str], *, role: str) -> list[str]:
    if re.search(r"(^|/)(?:multilingual-)?e5", model_id, flags=re.IGNORECASE) is None:
        return texts
    prefix = "query: " if role == "query" else "passage: "
    return [f"{prefix}{text}" for text in texts]


def current_gpu_temp_c() -> float | None:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    first = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
    try:
        return float(first.strip())
    except ValueError:
        return None


def status_note(status: str) -> str:
    return {
        "batch_complete": "Batch completed; run the same command again to continue.",
        "target_reached": "Target passage count reached.",
        "time_budget_reached": "Time budget reached; run the same command again to continue.",
        "temperature_pause": "GPU temperature limit reached; resume after the system cools down.",
        "throughput_guardrail_exceeded": (
            "Batch completed, but throughput fell below the safety guardrail."
        ),
        "upsert_guardrail_exceeded": (
            "Batch completed, but Chroma upsert time exceeded the safety guardrail."
        ),
        "dataset_exhausted": "All configured peS2o train shards were scanned.",
        "no_progress": "No progress was made in this invocation.",
    }.get(status, status)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


if __name__ == "__main__":
    raise SystemExit(main())
