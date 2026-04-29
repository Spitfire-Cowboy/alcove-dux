"""Alcove Dux command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from alcove_dux.calibration import CalibrationProfile
from alcove_dux.catalog import load_catalog
from alcove_dux.config import RuntimeConfig
from alcove_dux.corpus import load_corpus_documents, scan_text_against_corpus
from alcove_dux.documents import chunk_text, load_document_file
from alcove_dux.html_report import render_local_review_html, render_report_html
from alcove_dux.matching import compare_texts
from alcove_dux.reports import ReportDocument, ScanReport
from alcove_dux.semantic import (
    SentenceTransformerBackend,
    SentenceTransformerRerankerBackend,
    rerank_matches,
    semantic_chunk_matches,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alcove-dux",
        description="Local text-reuse evidence toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("catalog", help="Print the configured model and dataset catalog")

    scan_parser = subparsers.add_parser("scan", help="Compare two text files")
    scan_parser.add_argument("suspicious", type=Path)
    scan_parser.add_argument("source", type=Path)
    scan_parser.add_argument("--min-score", type=float, default=0.50)
    scan_parser.add_argument("--out", type=Path, help="Write JSON report to this path")
    scan_parser.add_argument("--html", type=Path, help="Write static HTML report to this path")
    scan_parser.add_argument(
        "--review-html",
        type=Path,
        help="Write local-only HTML report with matched text snippets",
    )
    _add_runtime_config_arguments(scan_parser)

    scan_corpus_parser = subparsers.add_parser("scan-corpus", help="Scan one file against a corpus")
    scan_corpus_parser.add_argument("suspicious", type=Path)
    scan_corpus_parser.add_argument("corpus", type=Path)
    scan_corpus_parser.add_argument("--min-score", type=float, default=0.50)
    scan_corpus_parser.add_argument("--out", type=Path, required=True)
    scan_corpus_parser.add_argument(
        "--html",
        type=Path,
        help="Write static HTML report to this path",
    )
    scan_corpus_parser.add_argument(
        "--review-html",
        type=Path,
        help="Write local-only HTML report with matched text snippets",
    )
    _add_runtime_config_arguments(scan_corpus_parser)

    args = parser.parse_args(argv)

    if args.command == "catalog":
        catalog = load_catalog()
        print(json.dumps(catalog.raw, indent=2, sort_keys=True))
        return 0

    if args.command == "scan":
        try:
            suspicious = load_document_file(args.suspicious, document_id=args.suspicious.stem)
            source = load_document_file(args.source, document_id=args.source.stem)
        except (RuntimeError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        min_score = _min_score_from_args(args)
        matches = compare_texts(
            suspicious.text,
            source.text,
            suspicious_id=suspicious.id,
            source_id=source.id,
            min_score=min_score,
        )
        catalog = load_catalog()
        runtime_config = _runtime_config_from_args(args, catalog, min_score=min_score)
        if args.semantic:
            try:
                backend = _semantic_backend(catalog, runtime_config)
                matches.extend(
                    semantic_chunk_matches(
                        chunk_text(suspicious.text, document_id=suspicious.id),
                        chunk_text(source.text, document_id=source.id),
                        backend,
                        min_score=args.semantic_threshold,
                        top_k=args.semantic_top_k,
                    )
                )
            except RuntimeError as error:
                print(str(error), file=sys.stderr)
                return 1
        if args.rerank:
            try:
                matches = rerank_matches(
                    matches,
                    suspicious_text=suspicious.text,
                    source_texts={source.id: source.text},
                    backend=_reranker_backend(catalog, runtime_config),
                )
            except RuntimeError as error:
                print(str(error), file=sys.stderr)
                return 1
        report = ScanReport.create(
            scan_id=str(uuid4()),
            suspicious_document_id=suspicious.id,
            source_document_id=source.id,
            matches=matches,
            source_documents=[ReportDocument(id=source.id, sha256=source.sha256)],
            suspicious_document_sha256=suspicious.sha256,
            source_document_sha256=source.sha256,
            catalog_schema_version=catalog.schema_version,
            selected_embedding_model_id=runtime_config.embedding_model_id,
            selected_reranker_model_id=runtime_config.reranker_model_id,
            runtime_config=runtime_config.to_dict(),
        )
        report_json = report.to_json()
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(report_json + "\n", encoding="utf-8")
        else:
            print(report_json)
        if args.html:
            _write_html_report(args.html, report.to_dict())
        if args.review_html:
            _write_review_html_report(
                args.review_html,
                report.to_dict(),
                suspicious_text=suspicious.text,
                source_texts={source.id: source.text},
            )
        return 0

    if args.command == "scan-corpus":
        try:
            suspicious = load_document_file(args.suspicious, document_id=args.suspicious.stem)
            corpus = load_corpus_documents(args.corpus)
        except (RuntimeError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        result = scan_text_against_corpus(
            suspicious.text,
            corpus,
            suspicious_id=suspicious.id,
            min_score=_min_score_from_args(args),
        )
        catalog = load_catalog()
        runtime_config = _runtime_config_from_args(
            args,
            catalog,
            min_score=_min_score_from_args(args),
        )
        matches = list(result.matches)
        if args.semantic:
            try:
                backend = _semantic_backend(catalog, runtime_config)
                for corpus_document in corpus:
                    matches.extend(
                        semantic_chunk_matches(
                            chunk_text(
                                result.suspicious_document.text,
                                document_id=result.suspicious_document.id,
                            ),
                            list(corpus_document.chunks),
                            backend,
                            min_score=args.semantic_threshold,
                            top_k=args.semantic_top_k,
                        )
                    )
            except RuntimeError as error:
                print(str(error), file=sys.stderr)
                return 1
        if args.rerank:
            try:
                matches = rerank_matches(
                    matches,
                    suspicious_text=result.suspicious_document.text,
                    source_texts={
                        corpus_document.document.id: corpus_document.document.text
                        for corpus_document in corpus
                    },
                    backend=_reranker_backend(catalog, runtime_config),
                )
            except RuntimeError as error:
                print(str(error), file=sys.stderr)
                return 1
        report = ScanReport.create(
            scan_id=str(uuid4()),
            suspicious_document_id=result.suspicious_document.id,
            source_document_id=f"corpus:{len(result.source_documents)}",
            source_documents=[
                ReportDocument(id=document.id, sha256=document.sha256)
                for document in result.source_documents
            ],
            matches=matches,
            suspicious_document_sha256=result.suspicious_document.sha256,
            catalog_schema_version=catalog.schema_version,
            selected_embedding_model_id=runtime_config.embedding_model_id,
            selected_reranker_model_id=runtime_config.reranker_model_id,
            runtime_config=runtime_config.to_dict(),
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        report_json = report.to_json()
        args.out.write_text(report_json + "\n", encoding="utf-8")
        if args.html:
            _write_html_report(args.html, report.to_dict())
        if args.review_html:
            _write_review_html_report(
                args.review_html,
                report.to_dict(),
                suspicious_text=result.suspicious_document.text,
                source_texts={
                    corpus_document.document.id: corpus_document.document.text
                    for corpus_document in corpus
                },
            )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _write_html_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report_html(report), encoding="utf-8")


def _write_review_html_report(
    path: Path,
    report: dict,
    *,
    suspicious_text: str,
    source_texts: dict[str, str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_local_review_html(
            report,
            suspicious_text=suspicious_text,
            source_texts=source_texts,
        ),
        encoding="utf-8",
    )


def _add_runtime_config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--embedding-model", help="Catalog ID for the embedding model")
    parser.add_argument(
        "--long-context-embedding-model",
        help="Catalog ID for the long-context embedding model",
    )
    parser.add_argument(
        "--multilingual-embedding-model",
        help="Catalog ID for the multilingual embedding model",
    )
    parser.add_argument("--reranker-model", help="Catalog ID for the reranker model")
    parser.add_argument(
        "--language",
        help="BCP-47 language hint to store with runtime config, such as en, es, or multilingual",
    )
    parser.add_argument(
        "--dataset",
        dest="datasets",
        action="append",
        help="Catalog dataset ID to record as enabled; repeat for multiple datasets",
    )
    parser.add_argument(
        "--calibration-profile",
        type=Path,
        help="Use a saved calibration profile's selected lexical threshold",
    )
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Enable optional embedding similarity matches",
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.72,
        help="Minimum embedding similarity score to report",
    )
    parser.add_argument(
        "--semantic-top-k",
        type=int,
        default=5,
        help="Maximum semantic source candidates per suspicious chunk",
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Apply the configured reranker model to reported evidence",
    )


def _runtime_config_from_args(
    args: argparse.Namespace,
    catalog,
    *,
    min_score: float,
) -> RuntimeConfig:
    return RuntimeConfig.from_catalog(
        catalog,
        embedding_model_id=args.embedding_model,
        long_context_embedding_model_id=args.long_context_embedding_model,
        multilingual_embedding_model_id=args.multilingual_embedding_model,
        reranker_model_id=args.reranker_model,
        baseline_lexical_threshold=min_score,
        semantic_similarity_threshold=args.semantic_threshold,
        semantic_top_k=args.semantic_top_k,
        calibration_profile_id=(
            str(args.calibration_profile) if args.calibration_profile else None
        ),
        language=args.language,
        enabled_dataset_ids=tuple(args.datasets) if args.datasets else None,
    )


def _semantic_backend(catalog, runtime_config: RuntimeConfig) -> SentenceTransformerBackend:
    if not runtime_config.embedding_model_id:
        raise RuntimeError("Semantic scanning requires an embedding model in runtime config")
    model = catalog.model(runtime_config.embedding_model_id)
    return SentenceTransformerBackend(model.model_id)


def _reranker_backend(catalog, runtime_config: RuntimeConfig) -> SentenceTransformerRerankerBackend:
    if not runtime_config.reranker_model_id:
        raise RuntimeError("Reranking requires a reranker model in runtime config")
    model = catalog.model(runtime_config.reranker_model_id)
    return SentenceTransformerRerankerBackend(model.model_id)


def _min_score_from_args(args: argparse.Namespace) -> float:
    if not args.calibration_profile:
        return args.min_score
    return CalibrationProfile.load(args.calibration_profile).selected_threshold


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
