"""Baseline lexical matching for Alcove Dux."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from alcove_dux.documents import Document, TextChunk, chunk_text, normalize_text

_CJK_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x3040, 0x309F),
    (0x30A0, 0x30FF),
    (0xAC00, 0xD7AF),
)
_THAI_RANGE = (0x0E00, 0x0E7F)
_THAI_COMBINING_RANGES = (
    (0x0E31, 0x0E31),
    (0x0E34, 0x0E3A),
    (0x0E47, 0x0E4E),
)


@dataclass(frozen=True)
class TokenPosition:
    """A normalized token with character offsets."""

    value: str
    start: int
    end: int


@dataclass(frozen=True)
class MatchEvidence:
    """Evidence that two text spans are similar."""

    kind: str
    suspicious_chunk_id: str
    source_chunk_id: str
    score: float
    suspicious_start: int
    suspicious_end: int
    source_start: int
    source_end: int
    explanation: str


def compare_texts(
    suspicious_text: str,
    source_text: str,
    *,
    suspicious_id: str = "suspicious",
    source_id: str = "source",
    min_score: float = 0.50,
) -> list[MatchEvidence]:
    """Compare two text strings and return baseline evidence."""

    suspicious = Document.from_text(suspicious_text, document_id=suspicious_id)
    source = Document.from_text(source_text, document_id=source_id)
    suspicious_chunks = chunk_text(suspicious.text, document_id=suspicious.id)
    source_chunks = chunk_text(source.text, document_id=source.id)
    exact_evidence = exact_token_sequence_matches(
        suspicious.text,
        source.text,
        suspicious_id=suspicious.id,
        source_id=source.id,
    )
    chunk_evidence = compare_chunks(suspicious_chunks, source_chunks, min_score=min_score)
    return _dedupe_and_sort([*exact_evidence, *chunk_evidence])


def exact_token_sequence_matches(
    suspicious_text: str,
    source_text: str,
    *,
    suspicious_id: str = "suspicious",
    source_id: str = "source",
    min_tokens: int = 8,
    max_matches: int = 100,
) -> list[MatchEvidence]:
    """Find exact shared token sequences and return span-level evidence."""

    if min_tokens <= 0:
        raise ValueError("min_tokens must be positive")
    suspicious_tokens = token_positions(suspicious_text)
    source_tokens = token_positions(source_text)
    if len(suspicious_tokens) < min_tokens or len(source_tokens) < min_tokens:
        return []

    source_index: dict[tuple[str, ...], list[int]] = {}
    for source_index_start in range(len(source_tokens) - min_tokens + 1):
        key = tuple(
            token.value
            for token in source_tokens[source_index_start : source_index_start + min_tokens]
        )
        source_index.setdefault(key, []).append(source_index_start)

    candidates: list[tuple[int, int, int]] = []
    for suspicious_index_start in range(len(suspicious_tokens) - min_tokens + 1):
        key = tuple(
            token.value
            for token in suspicious_tokens[
                suspicious_index_start : suspicious_index_start + min_tokens
            ]
        )
        for source_index_start in source_index.get(key, []):
            length = _extend_exact_match(
                suspicious_tokens,
                source_tokens,
                suspicious_index_start,
                source_index_start,
            )
            if length >= min_tokens:
                candidates.append((length, suspicious_index_start, source_index_start))

    selected: list[tuple[int, int, int]] = []
    used_suspicious: list[tuple[int, int]] = []
    used_source: list[tuple[int, int]] = []
    for length, suspicious_index_start, source_index_start in sorted(candidates, reverse=True):
        suspicious_range = (suspicious_index_start, suspicious_index_start + length)
        source_range = (source_index_start, source_index_start + length)
        if _token_range_overlaps(suspicious_range, used_suspicious):
            continue
        if _token_range_overlaps(source_range, used_source):
            continue
        selected.append((length, suspicious_index_start, source_index_start))
        used_suspicious.append(suspicious_range)
        used_source.append(source_range)
        if len(selected) >= max_matches:
            break

    evidence: list[MatchEvidence] = []
    for match_index, (length, suspicious_index_start, source_index_start) in enumerate(selected):
        suspicious_start = suspicious_tokens[suspicious_index_start].start
        suspicious_end = suspicious_tokens[suspicious_index_start + length - 1].end
        source_start = source_tokens[source_index_start].start
        source_end = source_tokens[source_index_start + length - 1].end
        evidence.append(
            MatchEvidence(
                kind="exact_token_sequence",
                suspicious_chunk_id=f"{suspicious_id}:exact:{match_index}",
                source_chunk_id=f"{source_id}:exact:{match_index}",
                score=1.0,
                suspicious_start=suspicious_start,
                suspicious_end=suspicious_end,
                source_start=source_start,
                source_end=source_end,
                explanation=f"Exact shared token sequence of {length} tokens.",
            )
        )
    return evidence


def compare_chunks(
    suspicious_chunks: list[TextChunk],
    source_chunks: list[TextChunk],
    *,
    min_score: float = 0.50,
) -> list[MatchEvidence]:
    """Compare two chunk lists with exact, containment, and Jaccard signals."""

    evidence: list[MatchEvidence] = []
    for suspicious in suspicious_chunks:
        for source in source_chunks:
            exact = exact_overlap_score(suspicious.text, source.text)
            containment = token_containment(suspicious.text, source.text)
            jaccard = token_jaccard(suspicious.text, source.text)
            order = token_order_similarity(suspicious.text, source.text)
            score = max(exact, containment * order**2, jaccard * order**2)
            if score < min_score:
                continue
            evidence.append(
                MatchEvidence(
                    kind=_kind_for_scores(exact=exact, containment=containment, jaccard=jaccard),
                    suspicious_chunk_id=suspicious.id,
                    source_chunk_id=source.id,
                    score=round(score, 4),
                    suspicious_start=suspicious.start,
                    suspicious_end=suspicious.end,
                    source_start=source.start,
                    source_end=source.end,
                    explanation=_explanation(exact=exact, containment=containment, jaccard=jaccard),
                )
            )

    return sorted(evidence, key=lambda item: item.score, reverse=True)


def exact_overlap_score(left: str, right: str) -> float:
    """Return 1.0 for exact normalized equality or substring containment."""

    left_norm = normalize_text(left).casefold()
    right_norm = normalize_text(right).casefold()
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    shorter, longer = sorted((left_norm, right_norm), key=len)
    if len(shorter) >= 40 and shorter in longer:
        return len(shorter) / len(longer)
    return 0.0


def token_jaccard(left: str, right: str) -> float:
    """Return token-set Jaccard similarity."""

    left_tokens = set(tokens(left))
    right_tokens = set(tokens(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def token_containment(left: str, right: str) -> float:
    """Return how much the smaller token set is contained in the larger one."""

    left_tokens = set(tokens(left))
    right_tokens = set(tokens(right))
    if not left_tokens or not right_tokens:
        return 0.0
    smaller, larger = sorted((left_tokens, right_tokens), key=len)
    return len(smaller & larger) / len(smaller)


def token_order_similarity(left: str, right: str) -> float:
    """Return sequence similarity over token order."""

    left_tokens = tokens(left)
    right_tokens = tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return SequenceMatcher(None, left_tokens, right_tokens, autojunk=False).ratio()


def tokens(text: str) -> list[str]:
    """Lowercase tokens with basic multilingual segmentation."""

    return [token.value for token in token_positions(text)]


def token_positions(text: str) -> list[TokenPosition]:
    """Lowercase tokens with offsets and basic multilingual segmentation."""

    positions: list[TokenPosition] = []
    cursor = 0
    while cursor < len(text):
        character = text[cursor]
        if character.isspace() or not _is_token_character(character):
            cursor += 1
            continue
        if _is_cjk_character(character):
            positions.append(
                TokenPosition(value=character.casefold(), start=cursor, end=cursor + 1)
            )
            cursor += 1
            continue
        if _is_thai_character(character):
            start = cursor
            cursor += 1
            while cursor < len(text) and _is_thai_combining_mark(text[cursor]):
                cursor += 1
            positions.append(
                TokenPosition(value=text[start:cursor].casefold(), start=start, end=cursor)
            )
            continue
        start = cursor
        cursor += 1
        while cursor < len(text) and _continues_word_token(text[cursor]):
            cursor += 1
        positions.append(
            TokenPosition(value=text[start:cursor].casefold(), start=start, end=cursor)
        )
    return positions


def _extend_exact_match(
    suspicious_tokens: list[TokenPosition],
    source_tokens: list[TokenPosition],
    suspicious_index_start: int,
    source_index_start: int,
) -> int:
    length = 0
    while (
        suspicious_index_start + length < len(suspicious_tokens)
        and source_index_start + length < len(source_tokens)
        and suspicious_tokens[suspicious_index_start + length].value
        == source_tokens[source_index_start + length].value
    ):
        length += 1
    return length


def _token_range_overlaps(candidate: tuple[int, int], selected: list[tuple[int, int]]) -> bool:
    return any(candidate[0] < existing[1] and existing[0] < candidate[1] for existing in selected)


def _dedupe_and_sort(evidence: list[MatchEvidence]) -> list[MatchEvidence]:
    seen = set()
    unique: list[MatchEvidence] = []
    for item in sorted(evidence, key=lambda match: match.score, reverse=True):
        key = (
            item.kind,
            item.suspicious_start,
            item.suspicious_end,
            item.source_start,
            item.source_end,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _kind_for_scores(*, exact: float, containment: float, jaccard: float) -> str:
    if exact >= 0.95:
        return "exact_overlap"
    if containment >= 0.8:
        return "near_duplicate"
    if jaccard >= 0.55:
        return "lexical_similarity"
    return "needs_review"


def _explanation(*, exact: float, containment: float, jaccard: float) -> str:
    if exact >= 0.95:
        return "Normalized text spans are exact or near-exact matches."
    if containment >= 0.8:
        return "Most tokens from the shorter span appear in the longer span."
    if jaccard >= 0.55:
        return "The spans share a high proportion of unique tokens."
    return "The spans crossed the configured baseline review threshold."


def _is_token_character(character: str) -> bool:
    return character.isalnum() or character == "'" or _is_cjk_character(character)


def _continues_word_token(character: str) -> bool:
    return (
        _is_token_character(character)
        and not _is_cjk_character(character)
        and not _is_thai_character(character)
    )


def _is_cjk_character(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _CJK_RANGES)


def _is_thai_character(character: str) -> bool:
    codepoint = ord(character)
    return _THAI_RANGE[0] <= codepoint <= _THAI_RANGE[1]


def _is_thai_combining_mark(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _THAI_COMBINING_RANGES)
