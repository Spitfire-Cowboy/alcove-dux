import pytest

from alcove_dux.matching import (
    compare_texts,
    exact_token_sequence_matches,
    token_containment,
    token_jaccard,
    token_order_similarity,
    token_positions,
)


def test_token_scores_for_overlap():
    left = "The quick brown fox jumps"
    right = "A quick brown fox jumps"

    assert token_jaccard(left, right) == 4 / 6
    assert token_containment(left, right) == 4 / 5
    assert token_order_similarity(left, left) == 1.0


def test_compare_texts_finds_exact_overlap():
    matches = compare_texts(
        "This sentence is copied exactly.",
        "This sentence is copied exactly.",
    )

    assert matches
    assert matches[0].kind == "exact_overlap"
    assert matches[0].score == 1.0


def test_compare_texts_uses_evidence_language():
    matches = compare_texts(
        "Local-first tools keep documents on the user's machine.",
        "Documents stay on the user's machine in local-first tools.",
        min_score=0.2,
    )

    assert matches
    assert "plagiar" not in matches[0].explanation.lower()


def test_reordered_high_overlap_text_is_not_strong_baseline_evidence():
    matches = compare_texts(
        "The dog bit the man during the walk.",
        "The man bit the dog during the walk.",
        min_score=0.80,
    )

    assert matches == []


def test_token_positions_include_offsets():
    positions = token_positions("A quick, brown fox.")

    assert [(token.value, token.start, token.end) for token in positions] == [
        ("a", 0, 1),
        ("quick", 2, 7),
        ("brown", 9, 14),
        ("fox", 15, 18),
    ]


def test_token_positions_segment_cjk_text_with_offsets():
    positions = token_positions("中文文本 reuse")

    assert [(token.value, token.start, token.end) for token in positions] == [
        ("中", 0, 1),
        ("文", 1, 2),
        ("文", 2, 3),
        ("本", 3, 4),
        ("reuse", 5, 10),
    ]


def test_exact_token_sequence_matches_cjk_text():
    suspicious = "前言 这是一个用于检测文本复用的中文句子。结尾"
    source = "来源 这是一个用于检测文本复用的中文句子。附录"

    matches = exact_token_sequence_matches(suspicious, source, min_tokens=8)

    assert matches
    assert suspicious[matches[0].suspicious_start : matches[0].suspicious_end] == (
        "这是一个用于检测文本复用的中文句子"
    )


def test_thai_text_produces_offset_preserving_tokens():
    positions = token_positions("ภาษาไทย")

    assert positions
    assert positions[0].start == 0
    assert positions[-1].end == len("ภาษาไทย")


def test_exact_token_sequence_matches_offsets():
    suspicious = "Intro. Alpha beta gamma delta epsilon zeta eta theta iota. Outro."
    source = "Other text. Alpha beta gamma delta epsilon zeta eta theta iota. Tail."

    matches = exact_token_sequence_matches(suspicious, source, min_tokens=5)

    assert matches
    assert matches[0].kind == "exact_token_sequence"
    assert suspicious[matches[0].suspicious_start : matches[0].suspicious_end] == (
        "Alpha beta gamma delta epsilon zeta eta theta iota"
    )
    assert source[matches[0].source_start : matches[0].source_end] == (
        "Alpha beta gamma delta epsilon zeta eta theta iota"
    )


def test_exact_token_sequence_rejects_invalid_window():
    with pytest.raises(ValueError):
        exact_token_sequence_matches("a b c", "a b c", min_tokens=0)
