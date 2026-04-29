"""Small local vector index for MVP retrieval."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alcove_dux.semantic import cosine_similarity


@dataclass(frozen=True)
class VectorRecord:
    """A chunk vector and enough metadata to trace it back to evidence."""

    id: str
    document_id: str
    chunk_id: str
    start: int
    end: int
    vector: tuple[float, ...]

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> VectorRecord:
        """Create a record from JSON-compatible data."""

        return cls(
            id=str(item["id"]),
            document_id=str(item["document_id"]),
            chunk_id=str(item["chunk_id"]),
            start=int(item["start"]),
            end=int(item["end"]),
            vector=tuple(float(value) for value in item["vector"]),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["vector"] = list(self.vector)
        return payload


@dataclass(frozen=True)
class VectorHit:
    """A vector search result."""

    record: VectorRecord
    score: float


class LocalVectorIndex:
    """In-memory vector index with JSONL persistence."""

    def __init__(self, records: list[VectorRecord] | None = None) -> None:
        self._records = list(records or [])

    @property
    def records(self) -> tuple[VectorRecord, ...]:
        """Indexed records in insertion order."""

        return tuple(self._records)

    def upsert(self, record: VectorRecord) -> None:
        """Insert or replace a vector by record ID."""

        self._records = [existing for existing in self._records if existing.id != record.id]
        self._records.append(record)

    def query(self, vector: list[float] | tuple[float, ...], *, top_k: int = 5) -> list[VectorHit]:
        """Return the top cosine-similar records."""

        hits = [
            VectorHit(record=record, score=cosine_similarity(vector, record.vector))
            for record in self._records
        ]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]

    def save_jsonl(self, path: str | Path) -> None:
        """Save the index as local JSONL."""

        index_path = Path(path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(record.to_dict(), sort_keys=True) for record in self._records]
        index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @classmethod
    def load_jsonl(cls, path: str | Path) -> LocalVectorIndex:
        """Load an index from local JSONL."""

        index_path = Path(path)
        records = [
            VectorRecord.from_mapping(json.loads(line))
            for line in index_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return cls(records)


class ChromaVectorIndex:
    """Optional ChromaDB-backed vector index."""

    def __init__(self, path: str | Path, *, collection_name: str = "alcove_dux") -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "Chroma vector storage requires: python -m pip install -e "
                '".[vector-chroma]"'
            ) from exc
        client = chromadb.PersistentClient(path=str(path))
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, record: VectorRecord) -> None:
        """Insert or replace a vector record."""

        self.collection.upsert(
            ids=[record.id],
            embeddings=[list(record.vector)],
            metadatas=[
                {
                    "document_id": record.document_id,
                    "chunk_id": record.chunk_id,
                    "start": record.start,
                    "end": record.end,
                }
            ],
        )

    def query(self, vector: list[float] | tuple[float, ...], *, top_k: int = 5) -> list[VectorHit]:
        """Return top cosine-similar records from Chroma."""

        result = self.collection.query(
            query_embeddings=[list(vector)],
            n_results=top_k,
            include=["metadatas", "distances", "embeddings"],
        )
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        embeddings = result.get("embeddings", [[]])[0]
        hits = []
        for record_id, metadata, distance, embedding in zip(
            ids,
            metadatas,
            distances,
            embeddings,
            strict=True,
        ):
            hits.append(
                VectorHit(
                    record=VectorRecord(
                        id=str(record_id),
                        document_id=str(metadata["document_id"]),
                        chunk_id=str(metadata["chunk_id"]),
                        start=int(metadata["start"]),
                        end=int(metadata["end"]),
                        vector=tuple(float(value) for value in embedding),
                    ),
                    score=max(0.0, min(1.0, 1.0 - float(distance))),
                )
            )
        return hits


def zvec_unavailable_message() -> str:
    """Return the current zvec adapter status."""

    return (
        "zvec is tracked as an experimental optional backend for Alcove-compatible "
        "embedded deployments; Alcove Dux's stable optional adapter is ChromaDB first."
    )
