"""PAN text-alignment dataset helpers."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PanAnnotation:
    """A PAN plagiarism annotation span."""

    suspicious_offset: int
    suspicious_length: int
    source_reference: str
    source_offset: int
    source_length: int
    obfuscation: str | None = None


@dataclass(frozen=True)
class PanPair:
    """A suspicious/source document pair from a PAN corpus."""

    suspicious_reference: str
    source_reference: str
    suspicious_path: Path
    source_path: Path
    annotations: tuple[PanAnnotation, ...]


@dataclass(frozen=True)
class PanPc11Document:
    """A suspicious PAN-PC-11 document and its annotations."""

    reference: str
    path: Path
    annotation_path: Path | None
    annotations: tuple[PanAnnotation, ...]


def iter_pan_pairs(root: str | Path, *, limit: int | None = None) -> list[PanPair]:
    """Load pairs from a PAN text-alignment corpus root."""

    root_path = Path(root)
    pairs_path = root_path / "pairs"
    if not pairs_path.exists():
        raise FileNotFoundError(f"PAN pairs file not found: {pairs_path}")

    pairs: list[PanPair] = []
    for line in pairs_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        suspicious_reference, source_reference = line.split()
        pairs.append(
            PanPair(
                suspicious_reference=suspicious_reference,
                source_reference=source_reference,
                suspicious_path=root_path / "susp" / suspicious_reference,
                source_path=root_path / "src" / source_reference,
                annotations=_load_annotations(
                    root_path,
                    suspicious_reference=suspicious_reference,
                    source_reference=source_reference,
                ),
            )
        )
        if limit is not None and len(pairs) >= limit:
            break
    return pairs


def iter_pan_pc11_documents(
    root: str | Path,
    *,
    limit: int | None = None,
) -> list[PanPc11Document]:
    """Load suspicious documents from a PAN-PC-11 corpus root.

    PAN-PC-11 packages suspicious document text files with same-stem XML
    annotation files. The corpus has appeared in a few unpacked directory
    shapes, so this loader discovers files recursively instead of requiring one
    fixed root layout.
    """

    documents: list[PanPc11Document] = []
    for suspicious_path in _iter_pan_pc11_suspicious_paths(Path(root)):
        annotation_path = suspicious_path.with_suffix(".xml")
        annotations = (
            _load_pan_pc11_annotations(annotation_path)
            if annotation_path.exists()
            else ()
        )
        documents.append(
            PanPc11Document(
                reference=suspicious_path.name,
                path=suspicious_path,
                annotation_path=annotation_path if annotation_path.exists() else None,
                annotations=annotations,
            )
        )
        if limit is not None and len(documents) >= limit:
            break
    return documents


def iter_pan_pc11_pairs(root: str | Path, *, limit: int | None = None) -> list[PanPair]:
    """Load PAN-PC-11 suspicious/source pairs grouped by source reference."""

    root_path = Path(root)
    source_index = _pan_pc11_source_index(root_path)
    pairs: list[PanPair] = []
    for document in iter_pan_pc11_documents(root_path):
        annotations_by_source: dict[str, list[PanAnnotation]] = {}
        for annotation in document.annotations:
            annotations_by_source.setdefault(annotation.source_reference, []).append(annotation)
        for source_reference, source_annotations in annotations_by_source.items():
            pairs.append(
                PanPair(
                    suspicious_reference=document.reference,
                    source_reference=source_reference,
                    suspicious_path=document.path,
                    source_path=source_index.get(source_reference, root_path / source_reference),
                    annotations=tuple(source_annotations),
                )
            )
            if limit is not None and len(pairs) >= limit:
                return pairs
    return pairs


def _load_annotations(
    root: Path,
    *,
    suspicious_reference: str,
    source_reference: str,
) -> tuple[PanAnnotation, ...]:
    annotation_name = (
        f"{Path(suspicious_reference).stem}-{Path(source_reference).stem}.xml"
    )
    annotations: list[PanAnnotation] = []
    for annotation_path in root.glob(f"*/{annotation_name}"):
        document = ET.parse(annotation_path).getroot()
        for feature in document.findall("feature"):
            if feature.attrib.get("name") != "plagiarism":
                continue
            annotations.append(
                PanAnnotation(
                    suspicious_offset=int(feature.attrib["this_offset"]),
                    suspicious_length=int(feature.attrib["this_length"]),
                    source_reference=feature.attrib["source_reference"],
                    source_offset=int(feature.attrib["source_offset"]),
                    source_length=int(feature.attrib["source_length"]),
                    obfuscation=feature.attrib.get("obfuscation"),
                )
            )
    return tuple(annotations)


def _iter_pan_pc11_suspicious_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("suspicious-document*.txt")
        if path.is_file()
    )


def _pan_pc11_source_index(root: Path) -> dict[str, Path]:
    return {
        path.name: path
        for path in root.rglob("source-document*.txt")
        if path.is_file()
    }


def _load_pan_pc11_annotations(annotation_path: Path) -> tuple[PanAnnotation, ...]:
    annotations: list[PanAnnotation] = []
    document = ET.parse(annotation_path).getroot()
    for feature in document.findall("feature"):
        if feature.attrib.get("name") != "plagiarism":
            continue
        annotations.append(
            PanAnnotation(
                suspicious_offset=int(feature.attrib["this_offset"]),
                suspicious_length=int(feature.attrib["this_length"]),
                source_reference=feature.attrib["source_reference"],
                source_offset=int(feature.attrib["source_offset"]),
                source_length=int(feature.attrib["source_length"]),
                obfuscation=feature.attrib.get("obfuscation"),
            )
        )
    return tuple(annotations)
