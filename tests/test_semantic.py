import pytest

from alcove_dux.documents import chunk_text
from alcove_dux.matching import MatchEvidence
from alcove_dux.semantic import cosine_similarity, rerank_matches, semantic_chunk_matches


class FakeBackend:
    def embed_texts(self, texts):
        vectors = {
            "copied idea": [1.0, 0.0],
            "same idea": [0.95, 0.05],
            "different topic": [0.0, 1.0],
        }
        return [vectors[text] for text in texts]


class FakeReranker:
    def score_pairs(self, pairs):
        return [0.91 for _ in pairs]


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert cosine_similarity([1, 0], [0, 1]) == 0.0
    assert cosine_similarity([0, 0], [1, 0]) == 0.0

    with pytest.raises(ValueError):
        cosine_similarity([1], [1, 2])


def test_semantic_chunk_matches_returns_top_candidates():
    suspicious = chunk_text("copied idea", document_id="suspicious")
    sources = [
        *chunk_text("same idea", document_id="source-a"),
        *chunk_text("different topic", document_id="source-b"),
    ]

    matches = semantic_chunk_matches(
        suspicious,
        sources,
        FakeBackend(),
        min_score=0.90,
        top_k=1,
    )

    assert len(matches) == 1
    assert matches[0].kind == "possible_paraphrase"
    assert matches[0].source_chunk_id.startswith("source-a")


def test_rerank_matches_updates_scores():
    matches = [
        MatchEvidence(
            kind="near_duplicate",
            suspicious_chunk_id="suspicious:0",
            source_chunk_id="source:0",
            score=0.6,
            suspicious_start=0,
            suspicious_end=11,
            source_start=0,
            source_end=11,
            explanation="Baseline score.",
        )
    ]

    reranked = rerank_matches(
        matches,
        suspicious_text="hello world",
        source_texts={"source": "hello world"},
        backend=FakeReranker(),
    )

    assert reranked[0].score == 0.91
    assert "Reranker score applied" in reranked[0].explanation
