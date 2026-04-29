"""Candidate retrieval for scalable lexical matching."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass

from alcove_dux.documents import TextChunk
from alcove_dux.matching import tokens


@dataclass(frozen=True)
class CandidatePair:
    """A suspicious/source chunk candidate pair."""

    suspicious: TextChunk
    source: TextChunk
    distance: int


def simhash_candidates(
    suspicious_chunks: list[TextChunk],
    source_chunks: list[TextChunk],
    *,
    max_candidates_per_chunk: int = 20,
    max_distance: int = 28,
) -> list[CandidatePair]:
    """Return likely lexical candidates using deterministic 64-bit SimHash."""

    if max_candidates_per_chunk <= 0:
        raise ValueError("max_candidates_per_chunk must be positive")
    if max_distance < 0:
        raise ValueError("max_distance must be non-negative")

    source_fingerprints = [
        (source, simhash(source.text))
        for source in source_chunks
        if tokens(source.text)
    ]
    candidates: list[CandidatePair] = []
    for suspicious in suspicious_chunks:
        if not tokens(suspicious.text):
            continue
        suspicious_fingerprint = simhash(suspicious.text)
        ranked = sorted(
            (
                (hamming_distance(suspicious_fingerprint, source_fingerprint), source)
                for source, source_fingerprint in source_fingerprints
            ),
            key=lambda item: item[0],
        )
        for distance, source in ranked[:max_candidates_per_chunk]:
            if distance <= max_distance:
                candidates.append(
                    CandidatePair(
                        suspicious=suspicious,
                        source=source,
                        distance=distance,
                    )
                )
    return candidates


def simhash(text: str, *, bits: int = 64) -> int:
    """Return a deterministic SimHash fingerprint."""

    if bits <= 0:
        raise ValueError("bits must be positive")
    weights = [0] * bits
    for token, count in Counter(tokens(text)).items():
        token_hash = _token_hash(token, bits=bits)
        for index in range(bits):
            if token_hash & (1 << index):
                weights[index] += count
            else:
                weights[index] -= count

    fingerprint = 0
    for index, weight in enumerate(weights):
        if weight > 0:
            fingerprint |= 1 << index
    return fingerprint


def hamming_distance(left: int, right: int) -> int:
    """Return bit-level Hamming distance."""

    return (left ^ right).bit_count()


def _token_hash(token: str, *, bits: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    if bits >= 64:
        return value
    return value & ((1 << bits) - 1)
