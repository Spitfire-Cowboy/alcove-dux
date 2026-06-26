import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_all_extra_includes_alcove():
    payload = _pyproject()
    all_extra = payload["project"]["optional-dependencies"]["all"]

    assert 'alcove-dux[semantic,vector-chroma,documents,yaml,eval,api,alcove]' in all_extra


def test_uv_conflicts_do_not_block_alcove_plus_documents_or_all():
    payload = _pyproject()

    assert "tool" not in payload or "uv" not in payload["tool"] or "conflicts" not in payload["tool"]["uv"]


def test_vector_store_docs_mark_zvec_as_not_yet_stable():
    text = (ROOT / "docs/vector-stores.md").read_text(encoding="utf-8")

    assert "stable runtime adapter for it yet" in text
