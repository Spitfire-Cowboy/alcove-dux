"""Local corpus discovery and scanning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from alcove_dux.candidates import simhash_candidates
from alcove_dux.documents import Document, TextChunk, chunk_text, load_document_file
from alcove_dux.matching import MatchEvidence, compare_chunks, exact_token_sequence_matches

DEFAULT_TEXT_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".pdf", ".docx"})


@dataclass(frozen=True)
class CorpusDocument:
    """A document loaded from a local corpus."""

    document: Document
    path: Path
    chunks: tuple[TextChunk, ...]


@dataclass(frozen=True)
class CorpusScanResult:
    """Matches from scanning one suspicious document against a corpus."""

    suspicious_document: Document
    source_documents: tuple[Document, ...]
    matches: tuple[MatchEvidence, ...]


def discover_text_files(
    root: str | Path,
    *,
    extensions: Iterable[str] = DEFAULT_TEXT_EXTENSIONS,
) -> list[Path]:
    """Return text-like files under ``root`` in stable order."""

    root_path = Path(root)
    normalized_extensions = {extension.casefold() for extension in extensions}
    return sorted(
        path
        for path in root_path.rglob("*")
        if path.is_file() and path.suffix.casefold() in normalized_extensions
    )


def load_corpus_documents(root: str | Path) -> list[CorpusDocument]:
    """Load supported corpus files without storing paths in report payloads."""

    corpus: list[CorpusDocument] = []
    for path in discover_text_files(root):
        document = load_document_file(path)
        corpus.append(
            CorpusDocument(
                document=document,
                path=path,
                chunks=tuple(chunk_text(document.text, document_id=document.id)),
            )
        )
    return corpus


def scan_text_against_corpus(
    suspicious_text: str,
    corpus: list[CorpusDocument],
    *,
    suspicious_id: str = "suspicious",
    min_score: float = 0.50,
) -> CorpusScanResult:
    """Scan suspicious text against loaded corpus documents."""

    suspicious = Document.from_text(suspicious_text, document_id=suspicious_id)
    suspicious_chunks = chunk_text(suspicious.text, document_id=suspicious.id)
    matches: list[MatchEvidence] = []
    source_documents: list[Document] = []

    for corpus_document in corpus:
        source_documents.append(corpus_document.document)
        matches.extend(
            exact_token_sequence_matches(
                suspicious.text,
                corpus_document.document.text,
                suspicious_id=suspicious.id,
                source_id=corpus_document.document.id,
            )
        )
        candidate_pairs = simhash_candidates(suspicious_chunks, list(corpus_document.chunks))
        for suspicious_chunk in suspicious_chunks:
            candidate_sources = [
                candidate.source
                for candidate in candidate_pairs
                if candidate.suspicious.id == suspicious_chunk.id
            ]
            if not candidate_sources:
                continue
            matches.extend(
                compare_chunks(
                    [suspicious_chunk],
                    candidate_sources,
                    min_score=min_score,
                )
            )

    return CorpusScanResult(
        suspicious_document=suspicious,
        source_documents=tuple(source_documents),
        matches=tuple(_dedupe_and_sort(matches)),
    )


def _dedupe_and_sort(matches: list[MatchEvidence]) -> list[MatchEvidence]:
    seen = set()
    unique: list[MatchEvidence] = []
    for match in sorted(matches, key=lambda item: item.score, reverse=True):
        key = (
            match.kind,
            match.suspicious_start,
            match.suspicious_end,
            match.source_chunk_id,
            match.source_start,
            match.source_end,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(match)
    return unique
