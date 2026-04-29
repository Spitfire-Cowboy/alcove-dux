import pytest

from alcove_dux.candidates import hamming_distance, simhash, simhash_candidates
from alcove_dux.documents import chunk_text


def test_simhash_is_deterministic_and_near_texts_are_closer():
    base = simhash("Alpha beta gamma delta epsilon")
    near = simhash("Alpha beta gamma delta zeta")
    far = simhash("finance market earnings guidance")

    assert base == simhash("Alpha beta gamma delta epsilon")
    assert hamming_distance(base, near) < hamming_distance(base, far)


def test_simhash_candidates_returns_likely_pairs():
    suspicious = chunk_text("Alpha beta gamma delta epsilon", document_id="suspicious")
    sources = [
        *chunk_text("Alpha beta gamma delta zeta", document_id="near"),
        *chunk_text("finance market earnings guidance", document_id="far"),
    ]

    candidates = simhash_candidates(
        suspicious,
        sources,
        max_candidates_per_chunk=1,
        max_distance=64,
    )

    assert len(candidates) == 1
    assert candidates[0].source.document_id == "near"


def test_simhash_candidates_rejects_invalid_limits():
    with pytest.raises(ValueError):
        simhash_candidates([], [], max_candidates_per_chunk=0)

    with pytest.raises(ValueError):
        simhash_candidates([], [], max_distance=-1)
