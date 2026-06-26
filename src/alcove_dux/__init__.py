"""Local-first plagiarism and text-reuse evidence toolkit."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from alcove_dux.catalog import Catalog, DatasetCandidate, ModelCandidate, load_catalog
from alcove_dux.documents import Document, TextChunk, chunk_text, normalize_text, sha256_text
from alcove_dux.matching import MatchEvidence, compare_texts
from alcove_dux.reports import ScanReport

__all__ = [
    "Catalog",
    "DatasetCandidate",
    "Document",
    "MatchEvidence",
    "ModelCandidate",
    "ScanReport",
    "TextChunk",
    "chunk_text",
    "compare_texts",
    "load_catalog",
    "normalize_text",
    "sha256_text",
]


def _detect_version() -> str:
    try:
        return version("alcove-dux")
    except PackageNotFoundError:
        version_file = Path(__file__).resolve().parents[2] / "VERSION"
        return version_file.read_text(encoding="utf-8").strip()


__version__ = _detect_version()
