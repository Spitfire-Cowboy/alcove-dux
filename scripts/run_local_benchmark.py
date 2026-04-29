"""Run repeatable local Alcove Dux benchmark tasks.

The runner writes aggregate JSON reports under ``reports/live-fire`` and keeps
large corpus locations configurable. It intentionally does not store raw source
or submitted text in the generated reports.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import re
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from live_fire import DEFAULT_DATASETS, run_dataset
from threshold_sweep import DEFAULT_THRESHOLDS

from alcove_dux.datasets.pairs import load_plagbench_public
from alcove_dux.datasets.pan import iter_pan_pc11_pairs
from alcove_dux.evaluation import binary_classification_metrics
from alcove_dux.matching import compare_texts

SEMANTIC_MODELS = (
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "intfloat/multilingual-e5-small",
)
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Alcove Dux benchmark suite")
    parser.add_argument("--out-dir", type=Path, default=Path("reports/live-fire"))
    parser.add_argument("--limit", type=int, default=4000, help="Pair examples per small dataset")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DEFAULT_DATASETS,
        help="Small dataset to include; defaults to all supported small datasets",
    )
    parser.add_argument("--skip-checks", action="store_true", help="Skip pytest/ruff/build checks")
    parser.add_argument("--semantic", action="store_true", help="Run semantic pair sweeps")
    parser.add_argument("--reranker", action="store_true", help="Run calibrated reranker sweeps")
    parser.add_argument("--pan-pc-11-root", type=Path, help="PAN-PC-11 external corpus root")
    parser.add_argument("--pan-limit", type=int, default=500, help="PAN positive windows to sample")
    parser.add_argument(
        "--pan-semantic",
        action="store_true",
        help="Run semantic PAN window sweeps",
    )
    parser.add_argument("--pes2o-v2", action="store_true", help="Run peS2o v2 controlled reuse")
    parser.add_argument("--pes2o-limit", type=int, default=1000, help="peS2o passages to sample")
    parser.add_argument("--hf-cache", type=Path, help="Hugging Face cache directory for peS2o")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commands": [],
        "outputs": [],
        "notes": [
            "Reports contain aggregate metrics only; raw benchmark text is not emitted.",
            "PAN-PC-11 and other large corpora run only when explicit local roots are provided.",
        ],
    }

    if not args.skip_checks:
        manifest["checks"] = _run_checks()

    threshold_out = args.out_dir / "threshold-sweep.json"
    _run_threshold_sweep(tuple(args.dataset or DEFAULT_DATASETS), args.limit, threshold_out)
    manifest["outputs"].append(str(threshold_out))

    if args.semantic:
        semantic_out = args.out_dir / "semantic-pair-sweep.json"
        _run_semantic_pair_sweep(
            tuple(args.dataset or DEFAULT_DATASETS),
            args.limit,
            semantic_out,
            include_reranker=args.reranker,
        )
        manifest["outputs"].append(str(semantic_out))

    if args.pan_pc_11_root:
        pan_out = args.out_dir / "pan-pc-11-window-summary.json"
        _run_pan_window_eval(
            args.pan_pc_11_root,
            args.pan_limit,
            pan_out,
            semantic=args.pan_semantic,
            include_reranker=args.reranker,
        )
        manifest["outputs"].append(str(pan_out))

    if args.pes2o_v2:
        pes2o_out = args.out_dir / "pes2o-v2-controlled-reuse.json"
        _run_pes2o_v2_controlled_reuse(
            limit=args.pes2o_limit,
            out=pes2o_out,
            cache_dir=args.hf_cache,
            semantic=args.semantic,
            include_reranker=args.reranker,
        )
        manifest["outputs"].append(str(pes2o_out))

    manifest_out = args.out_dir / "local-benchmark-manifest.json"
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _run_checks() -> dict[str, dict[str, object]]:
    checks = {}
    for name, command in {
        "pytest": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [sys.executable, "-m", "ruff", "check", "."],
        "build": [sys.executable, "-m", "build"],
    }.items():
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        checks[name] = {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        }
    return checks


def _run_threshold_sweep(dataset_ids: Sequence[str], limit: int, out: Path) -> None:
    summaries = []
    for dataset_id in dataset_ids:
        dataset_results = []
        for threshold in DEFAULT_THRESHOLDS:
            result = run_dataset(dataset_id, limit=limit, threshold=threshold)
            dataset_results.append(
                {
                    "threshold": threshold,
                    "metrics": result["metrics"],
                    "group_metrics": result.get("group_metrics", {}),
                }
            )
        summaries.append({"dataset_id": dataset_id, "results": dataset_results})
    out.write_text(
        json.dumps({"limit": limit, "datasets": summaries}, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _run_semantic_pair_sweep(
    dataset_ids: Sequence[str],
    limit: int,
    out: Path,
    *,
    include_reranker: bool = False,
) -> None:
    try:
        from datasets import load_dataset
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            'Semantic benchmark requires: python -m pip install -e ".[semantic,eval]"'
        ) from exc

    datasets = {
        dataset_id: _load_pair_rows(load_dataset, dataset_id, limit)
        for dataset_id in dataset_ids
        if dataset_id != "stsb"
    }
    payload: dict[str, object] = {
        "limit": limit,
        "models": list(SEMANTIC_MODELS),
        "datasets": {},
    }
    for model_id in SEMANTIC_MODELS:
        model = SentenceTransformer(model_id)
        for dataset_id, rows in datasets.items():
            left = [row["left"] for row in rows]
            right = [row["right"] for row in rows]
            labels = [bool(row["label"]) for row in rows]
            left_vectors = model.encode(
                _prepare_embedding_texts(model_id, left, role="query"),
                normalize_embeddings=True,
                batch_size=64,
                show_progress_bar=False,
            )
            right_vectors = model.encode(
                _prepare_embedding_texts(model_id, right, role="passage"),
                normalize_embeddings=True,
                batch_size=64,
                show_progress_bar=False,
            )
            scores = np.sum(
                np.asarray(left_vectors) * np.asarray(right_vectors),
                axis=1,
            ).astype(float)
            payload["datasets"].setdefault(dataset_id, {"methods": {}})
            payload["datasets"][dataset_id]["methods"][model_id] = _classification_sweep(
                labels,
                scores.tolist(),
            )
    if include_reranker:
        for dataset_id, rows in datasets.items():
            payload["datasets"].setdefault(dataset_id, {"methods": {}})
            payload["datasets"][dataset_id]["methods"][RERANKER_MODEL] = _reranker_sweep(rows)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _load_pair_rows(load_dataset, dataset_id: str, limit: int) -> list[dict[str, object]]:
    if dataset_id == "mrpc":
        rows = load_dataset("glue", "mrpc", split=f"validation[:{limit}]")
        return [
            {"left": row["sentence1"], "right": row["sentence2"], "label": row["label"] == 1}
            for row in rows
        ]
    if dataset_id == "paws":
        rows = load_dataset(
            "google-research-datasets/paws",
            "labeled_final",
            split=f"validation[:{limit}]",
        )
        return [
            {"left": row["sentence1"], "right": row["sentence2"], "label": row["label"] == 1}
            for row in rows
        ]
    if dataset_id == "plagbench":
        examples = load_plagbench_public(limit=limit)
        return [
            {
                "left": example.left_text,
                "right": example.right_text,
                "label": bool(example.label),
            }
            for example in examples
        ]
    raise ValueError(f"Unsupported semantic pair dataset: {dataset_id}")


def _run_pan_window_eval(
    root: Path,
    limit: int,
    out: Path,
    *,
    semantic: bool = False,
    include_reranker: bool = False,
) -> None:
    cases = _collect_pan_window_cases(root, limit)
    labels = [case["label"] for case in cases]
    scores = []
    kinds: dict[str, int] = {}
    for case in cases:
        matches = compare_texts(str(case["left"]), str(case["right"]), min_score=0.0)
        score = matches[0].score if matches else 0.0
        kind = matches[0].kind if matches else "none"
        scores.append(score)
        kinds[kind] = kinds.get(kind, 0) + 1
    payload: dict[str, object] = {
        "dataset_id": "pan_pc_11_external_annotation_windows",
        "positive_windows": sum(labels),
        "negative_windows": len(labels) - sum(labels),
        "methods": {
            "exact_fuzzy_baseline": {
                "threshold_sweep": _classification_sweep(labels, scores),
                "match_kinds": kinds,
            }
        },
        "match_kinds": kinds,
        "notes": (
            "Window-level aggregate evaluation. Negative windows are deterministic unrelated "
            "source snippets, not official PAN retrieval scoring."
        ),
    }
    if semantic:
        for model_id in SEMANTIC_MODELS:
            payload["methods"][model_id] = _semantic_sweep(cases, model_id)
    if include_reranker:
        payload["methods"][RERANKER_MODEL] = _reranker_sweep(cases)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _collect_pan_window_cases(root: Path, limit: int) -> list[dict[str, object]]:
    rng = random.Random(20260428)
    source_paths = list(root.rglob("source-document*.txt"))
    positives = []
    for pair in iter_pan_pc11_pairs(root):
        if len(positives) >= limit:
            break
        suspicious_text = pair.suspicious_path.read_text(encoding="utf-8", errors="ignore")
        source_text = pair.source_path.read_text(encoding="utf-8", errors="ignore")
        for annotation in pair.annotations:
            left = _window(
                suspicious_text,
                annotation.suspicious_offset,
                annotation.suspicious_length,
            )
            right = _window(source_text, annotation.source_offset, annotation.source_length)
            if len(left.strip()) < 40 or len(right.strip()) < 40:
                continue
            positives.append({"left": left, "right": right, "label": True})
            if len(positives) >= limit:
                break
    negatives = []
    for item in positives:
        source_path = rng.choice(source_paths)
        text = source_path.read_text(encoding="utf-8", errors="ignore")
        if len(text) > 500:
            start = rng.randrange(0, max(1, len(text) - 400))
            right = text[start : start + 400]
        else:
            right = text
        negatives.append({"left": item["left"], "right": right, "label": False})
    return positives + negatives


def _window(text: str, start: int, length: int, *, pad: int = 80) -> str:
    return text[max(0, start - pad) : min(len(text), start + length + pad)]


def _run_pes2o_v2_controlled_reuse(
    *,
    limit: int,
    out: Path,
    cache_dir: Path | None,
    semantic: bool,
    include_reranker: bool,
) -> None:
    documents = _load_pes2o_v2_passages(limit=limit, cache_dir=cache_dir)
    cases = _controlled_reuse_cases(documents)
    labels = [case["label"] for case in cases]
    baseline_scores = []
    for case in cases:
        matches = compare_texts(str(case["left"]), str(case["right"]), min_score=0.0)
        baseline_scores.append(matches[0].score if matches else 0.0)
    payload: dict[str, object] = {
        "dataset_id": "allenai/peS2o:v2-validation-controlled-reuse",
        "documents_loaded": len(documents),
        "cases": len(cases),
        "license_note": "ODC-By per the Hugging Face dataset card.",
        "methods": {
            "exact_fuzzy_baseline": _classification_sweep(labels, baseline_scores),
        },
        "notes": (
            "Controlled reuse benchmark over validation passages. No raw paper text is emitted."
        ),
    }
    if semantic:
        for model_id in SEMANTIC_MODELS:
            payload["methods"][model_id] = _semantic_sweep(cases, model_id)
    if include_reranker:
        payload["methods"][RERANKER_MODEL] = _reranker_sweep(cases)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _load_pes2o_v2_passages(*, limit: int, cache_dir: Path | None) -> list[dict[str, str]]:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise SystemExit("peS2o support requires huggingface_hub") from exc

    filenames = (
        "data/v2/validation-00000-of-00002.json.gz",
        "data/v2/validation-00001-of-00002.json.gz",
    )
    documents = []
    source_counts: dict[str, int] = {}
    for filename in filenames:
        path = hf_hub_download(
            "allenai/peS2o",
            filename=filename,
            repo_type="dataset",
            cache_dir=str(cache_dir) if cache_dir else None,
        )
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                text = _first_passage(str(row.get("text", "")))
                if text is None:
                    continue
                source = str(row.get("source", "unknown"))
                source_counts[source] = source_counts.get(source, 0) + 1
                documents.append(
                    {
                        "id": f"pes2o:{len(documents)}",
                        "source": source,
                        "text": text,
                    }
                )
                if len(documents) >= limit:
                    return documents
    return documents


def _first_passage(text: str, *, max_words: int = 160) -> str | None:
    paragraphs = [
        paragraph.strip().replace("\n", " ")
        for paragraph in text.split("\n\n")
        if len(_words(paragraph)) >= 80
    ]
    passage = paragraphs[0] if paragraphs else text.replace("\n", " ")
    words = _words(passage)
    if len(words) < 80:
        return None
    return " ".join(words[:max_words])


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _controlled_reuse_cases(documents: list[dict[str, str]]) -> list[dict[str, object]]:
    rng = random.Random(20260428)
    if len(documents) < 4:
        return []
    half = len(documents) // 2
    count = min(700, half, len(documents) - half)
    source_indexes = rng.sample(range(half), count)
    negative_indexes = rng.sample(range(half, len(documents)), count)
    cases = []
    for source_index, negative_index in zip(source_indexes, negative_indexes, strict=True):
        source_text = documents[source_index]["text"]
        cases.append(
            {
                "left": source_text,
                "right": source_text,
                "label": True,
                "case_type": "exact",
            }
        )
        cases.append(
            {
                "left": _mechanical_obfuscation(source_text),
                "right": source_text,
                "label": True,
                "case_type": "obfuscated",
            }
        )
        cases.append(
            {
                "left": source_text,
                "right": documents[negative_index]["text"],
                "label": False,
                "case_type": "unrelated",
            }
        )
    rng.shuffle(cases)
    return cases


def _mechanical_obfuscation(text: str) -> str:
    words = _words(text)
    kept = [word for index, word in enumerate(words) if (index + 1) % 9 != 0]
    for index in range(10, min(len(kept) - 1, 80), 17):
        kept[index], kept[index + 1] = kept[index + 1], kept[index]
    return " ".join(kept)


def _semantic_sweep(cases: Sequence[dict[str, object]], model_id: str) -> dict[str, object]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            'Semantic benchmark requires: python -m pip install -e ".[semantic]"'
        ) from exc

    model = SentenceTransformer(model_id)
    left = [str(case["left"]) for case in cases]
    right = [str(case["right"]) for case in cases]
    left_vectors = model.encode(
        _prepare_embedding_texts(model_id, left, role="query"),
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )
    right_vectors = model.encode(
        _prepare_embedding_texts(model_id, right, role="passage"),
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )
    scores = np.sum(np.asarray(left_vectors) * np.asarray(right_vectors), axis=1).astype(float)
    payload = _classification_sweep([bool(case["label"]) for case in cases], scores.tolist())
    payload["preprocessing"] = _embedding_preprocessing_note(model_id)
    return payload


def _reranker_sweep(cases: Sequence[dict[str, object]]) -> dict[str, object]:
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise SystemExit(
            'Reranker benchmark requires: python -m pip install -e ".[semantic]"'
        ) from exc

    reranker = CrossEncoder(RERANKER_MODEL)
    raw_scores = [
        float(score)
        for score in reranker.predict(
            [(str(case["left"]), str(case["right"])) for case in cases],
            batch_size=32,
            show_progress_bar=False,
        )
    ]
    labels = [bool(case["label"]) for case in cases]
    minmax_scores = _minmax(raw_scores)
    sigmoid_scores = [_sigmoid(score) for score in raw_scores]
    return {
        "model_id": RERANKER_MODEL,
        "raw_score_min": round(min(raw_scores), 4) if raw_scores else 0.0,
        "raw_score_max": round(max(raw_scores), 4) if raw_scores else 0.0,
        "raw_threshold_sweep": _raw_score_sweep(labels, raw_scores),
        "minmax_calibrated_sweep": _classification_sweep(labels, minmax_scores),
        "sigmoid_calibrated_sweep": _classification_sweep(labels, sigmoid_scores),
        "notes": (
            "Reranker scores are evaluated as raw thresholds plus observed min-max and "
            "sigmoid transforms. Use held-out calibration before adopting a production threshold."
        ),
    }


def _prepare_embedding_texts(model_id: str, texts: Sequence[str], *, role: str) -> list[str]:
    if "e5" not in model_id.lower():
        return list(texts)
    prefix = "query: " if role == "query" else "passage: "
    return [f"{prefix}{text}" for text in texts]


def _embedding_preprocessing_note(model_id: str) -> str:
    if "e5" in model_id.lower():
        return "Applied E5 query/passage prefixes."
    return "No model-specific text prefixing applied."


def _classification_sweep(labels: Sequence[bool], scores: Sequence[float]) -> dict[str, object]:
    rows = []
    for threshold in sorted({*DEFAULT_THRESHOLDS, 0.72, 0.75, 0.85}):
        predicted = [score >= threshold for score in scores]
        metrics = binary_classification_metrics(list(labels), predicted).to_dict()
        fp = int(metrics["fp"])
        tn = int(metrics["tn"])
        metrics["false_positive_rate"] = round(fp / (fp + tn), 4) if fp + tn else 0.0
        rows.append({"threshold": threshold, "metrics": metrics})
    rows = sorted(rows, key=lambda item: item["threshold"])
    return {
        "best_by_f1": max(
            rows,
            key=lambda item: (
                item["metrics"]["f1"],
                item["metrics"]["recall"],
                -item["metrics"]["false_positive_rate"],
            ),
        ),
        "thresholds": rows,
    }


def _raw_score_sweep(labels: Sequence[bool], scores: Sequence[float]) -> dict[str, object]:
    if not scores:
        return {"best_by_f1": None, "thresholds": []}
    thresholds = sorted({min(scores), max(scores), *np.quantile(scores, np.linspace(0, 1, 11))})
    rows = []
    for threshold in thresholds:
        predicted = [score >= threshold for score in scores]
        metrics = binary_classification_metrics(list(labels), predicted).to_dict()
        fp = int(metrics["fp"])
        tn = int(metrics["tn"])
        metrics["false_positive_rate"] = round(fp / (fp + tn), 4) if fp + tn else 0.0
        rows.append({"threshold": round(float(threshold), 4), "metrics": metrics})
    return {
        "best_by_f1": max(
            rows,
            key=lambda item: (
                item["metrics"]["f1"],
                item["metrics"]["recall"],
                -item["metrics"]["false_positive_rate"],
            ),
        ),
        "thresholds": rows,
    }


def _minmax(scores: Sequence[float]) -> list[float]:
    if not scores:
        return []
    low = min(scores)
    high = max(scores)
    if math.isclose(low, high):
        return [0.0 for _ in scores]
    return [(score - low) / (high - low) for score in scores]


def _sigmoid(score: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-score))
    except OverflowError:
        return 0.0 if score < 0 else 1.0


if __name__ == "__main__":
    raise SystemExit(main())
