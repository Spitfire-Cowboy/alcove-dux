"""Optional semantic matching for Alcove Dux."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace
from typing import Protocol

from alcove_dux.documents import TextChunk
from alcove_dux.matching import MatchEvidence


class EmbeddingBackend(Protocol):
    """Minimal embedding backend contract."""

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""


class SentenceTransformerBackend:
    """Sentence Transformers embedding backend loaded only when requested."""

    def __init__(self, model_id: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Semantic scanning requires the semantic extra: "
                'python -m pip install -e ".[semantic]"'
            ) from exc
        self.model = SentenceTransformer(model_id)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed texts with Sentence Transformers."""

        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return [list(vector) for vector in vectors]


class RerankerBackend(Protocol):
    """Minimal reranker backend contract."""

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
        """Return one score per text pair."""


class SentenceTransformerRerankerBackend:
    """Sentence Transformers cross-encoder backend loaded only when requested."""

    def __init__(self, model_id: str) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError(
                "Reranking requires the semantic extra: "
                'python -m pip install -e ".[semantic]"'
            ) from exc
        self.model = CrossEncoder(model_id)

    def score_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
        """Score text pairs with a cross-encoder."""

        return [float(score) for score in self.model.predict(list(pairs))]


def semantic_chunk_matches(
    suspicious_chunks: list[TextChunk],
    source_chunks: list[TextChunk],
    backend: EmbeddingBackend,
    *,
    min_score: float = 0.72,
    top_k: int = 5,
) -> list[MatchEvidence]:
    """Return semantic candidate matches for suspicious/source chunk pairs."""

    if not suspicious_chunks or not source_chunks:
        return []
    suspicious_vectors = backend.embed_texts([chunk.text for chunk in suspicious_chunks])
    source_vectors = backend.embed_texts([chunk.text for chunk in source_chunks])

    evidence: list[MatchEvidence] = []
    for suspicious, suspicious_vector in zip(
        suspicious_chunks,
        suspicious_vectors,
        strict=True,
    ):
        scored_sources = sorted(
            (
                (cosine_similarity(suspicious_vector, source_vector), source)
                for source, source_vector in zip(source_chunks, source_vectors, strict=True)
            ),
            key=lambda item: item[0],
            reverse=True,
        )[:top_k]
        for score, source in scored_sources:
            if score < min_score:
                continue
            evidence.append(
                MatchEvidence(
                    kind="possible_paraphrase",
                    suspicious_chunk_id=suspicious.id,
                    source_chunk_id=source.id,
                    score=round(score, 4),
                    suspicious_start=suspicious.start,
                    suspicious_end=suspicious.end,
                    source_start=source.start,
                    source_end=source.end,
                    explanation="Embedding similarity crossed the configured review threshold.",
                )
            )
    return evidence


def rerank_matches(
    matches: list[MatchEvidence],
    *,
    suspicious_text: str,
    source_texts: dict[str, str],
    backend: RerankerBackend,
) -> list[MatchEvidence]:
    """Rerank evidence with a pairwise text scorer."""

    pairs: list[tuple[str, str]] = []
    rerankable: list[tuple[int, MatchEvidence]] = []
    for index, match in enumerate(matches):
        source_id = _source_id_for_match(match, source_texts)
        if source_id is None:
            continue
        suspicious_span = suspicious_text[match.suspicious_start : match.suspicious_end]
        source_text = source_texts[source_id]
        source_span = source_text[match.source_start : match.source_end]
        pairs.append((suspicious_span, source_span))
        rerankable.append((index, match))

    if not pairs:
        return matches

    scores = backend.score_pairs(pairs)
    updated = list(matches)
    for score, (index, match) in zip(scores, rerankable, strict=True):
        normalized_score = max(0.0, min(float(score), 1.0))
        updated[index] = replace(
            match,
            score=round(normalized_score, 4),
            explanation=f"{match.explanation} Reranker score applied.",
        )
    return sorted(updated, key=lambda item: item.score, reverse=True)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two vectors."""

    if len(left) != len(right):
        raise ValueError("Vectors must have the same dimension")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _source_id_for_match(match: MatchEvidence, source_texts: dict[str, str]) -> str | None:
    for source_id in sorted(source_texts, key=len, reverse=True):
        if match.source_chunk_id == source_id or match.source_chunk_id.startswith(f"{source_id}:"):
            return source_id
    return None
