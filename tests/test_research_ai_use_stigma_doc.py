from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "research-ai-use-stigma.md"
README = Path(__file__).resolve().parents[1] / "README.md"
RESEARCH = Path(__file__).resolve().parents[1] / "docs" / "research.md"


def test_stigma_doc_exists_and_has_core_sections():
    text = DOC.read_text(encoding="utf-8")
    assert "AI-use stigma, underreporting" in text
    assert "Why this matters for Alcove Dux" in text
    assert "Product implications" in text
    assert "Research and evaluation implications" in text
    assert "confession extractor" in text


def test_readme_links_to_stigma_doc():
    text = README.read_text(encoding="utf-8")
    assert "docs/research-ai-use-stigma.md" in text


def test_research_notes_link_to_stigma_doc():
    text = RESEARCH.read_text(encoding="utf-8")
    assert "research-ai-use-stigma.md" in text
