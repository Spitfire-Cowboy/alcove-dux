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


def test_project_urls_cover_repo_docs_and_issues():
    urls = _pyproject()["project"]["urls"]

    assert urls["Homepage"] == "https://github.com/Spitfire-Cowboy/alcove-dux"
    assert urls["Documentation"].endswith("/blob/develop/README.md")
    assert urls["Issues"].endswith("/issues")


def test_readme_uses_absolute_links_for_docs():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "](docs/" not in readme
    assert "](roadmap.md)" not in readme
    assert "https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/quickstart.md" in readme
