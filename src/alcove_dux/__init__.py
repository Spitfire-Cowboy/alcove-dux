"""Local-first plagiarism and text-reuse evidence toolkit."""

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

__version__ = "0.1.0"
