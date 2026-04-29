"""SQLite persistence for local Alcove Dux API workflows."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alcove_dux.documents import Document, chunk_text
from alcove_dux.reports import ScanReport, validate_report_dict


@dataclass(frozen=True)
class StoredDocument:
    """A locally persisted document."""

    id: str
    text: str
    sha256: str
    metadata: dict[str, str]
    created_at: str

    @property
    def summary(self) -> dict:
        """Privacy-conscious document summary."""

        return {
            "id": self.id,
            "sha256": self.sha256,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "text_length": len(self.text),
        }


@dataclass(frozen=True)
class StoredChunk:
    """A locally persisted document chunk."""

    id: str
    document_id: str
    start: int
    end: int
    text: str

    @property
    def summary(self) -> dict:
        """Chunk summary without raw text."""

        return {
            "id": self.id,
            "document_id": self.document_id,
            "start": self.start,
            "end": self.end,
            "text_length": len(self.text),
        }


@dataclass(frozen=True)
class StoredScan:
    """A locally persisted scan report."""

    id: str
    report: dict[str, Any]
    status: str
    created_at: str

    @property
    def summary(self) -> dict:
        """Scan summary without raw document text."""

        return {
            "id": self.id,
            "status": self.status,
            "created_at": self.created_at,
            "suspicious_document_id": self.report.get("suspicious_document_id"),
            "source_document_id": self.report.get("source_document_id"),
            "match_count": len(self.report.get("matches", [])),
            "top_score": max(
                (float(match.get("score", 0)) for match in self.report.get("matches", [])),
                default=0.0,
            ),
        }


class AlcoveDuxStore:
    """Small SQLite store for local documents and scan reports."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def put_document(self, document: Document) -> StoredDocument:
        """Persist a normalized document."""

        created_at = _now()
        chunks = chunk_text(document.text, document_id=document.id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, text, sha256, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    text = excluded.text,
                    sha256 = excluded.sha256,
                    metadata_json = excluded.metadata_json
                """,
                (
                    document.id,
                    document.text,
                    document.sha256,
                    json.dumps(document.metadata, sort_keys=True),
                    created_at,
                ),
            )
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document.id,))
            connection.executemany(
                """
                INSERT INTO chunks (id, document_id, start, end, text)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (chunk.id, chunk.document_id, chunk.start, chunk.end, chunk.text)
                    for chunk in chunks
                ],
            )
        return StoredDocument(
            id=document.id,
            text=document.text,
            sha256=document.sha256,
            metadata=dict(document.metadata),
            created_at=created_at,
        )

    def get_document(self, document_id: str) -> StoredDocument | None:
        """Return a stored document by ID."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, text, sha256, metadata_json, created_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
        return _document_from_row(row) if row else None

    def list_documents(self) -> list[dict]:
        """Return document summaries."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, text, sha256, metadata_json, created_at
                FROM documents
                ORDER BY created_at DESC, id ASC
                """
            ).fetchall()
        return [_document_from_row(row).summary for row in rows]

    def list_chunks(self, document_id: str) -> list[StoredChunk]:
        """Return persisted chunks for a document."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, start, end, text
                FROM chunks
                WHERE document_id = ?
                ORDER BY start ASC, id ASC
                """,
                (document_id,),
            ).fetchall()
        return [_chunk_from_row(row) for row in rows]

    def put_scan(self, report: ScanReport) -> StoredScan:
        """Persist a scan report."""

        payload = report.to_dict()
        errors = validate_report_dict(payload)
        if errors:
            raise ValueError(f"Invalid Alcove Dux report: {'; '.join(errors)}")
        created_at = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scans (id, report_json, status, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    report_json = excluded.report_json,
                    status = excluded.status
                """,
                (
                    report.scan_id,
                    json.dumps(payload, sort_keys=True),
                    "complete",
                    created_at,
                ),
            )
        return StoredScan(
            id=report.scan_id,
            report=payload,
            status="complete",
            created_at=created_at,
        )

    def get_scan(self, scan_id: str) -> StoredScan | None:
        """Return a stored scan by ID."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, report_json, status, created_at
                FROM scans
                WHERE id = ?
                """,
                (scan_id,),
            ).fetchone()
        return _scan_from_row(row) if row else None

    def list_scans(self) -> list[dict]:
        """Return scan summaries."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, report_json, status, created_at
                FROM scans
                ORDER BY created_at DESC, id ASC
                """
            ).fetchall()
        return [_scan_from_row(row).summary for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY,
                    report_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def _document_from_row(row: sqlite3.Row) -> StoredDocument:
    return StoredDocument(
        id=str(row["id"]),
        text=str(row["text"]),
        sha256=str(row["sha256"]),
        metadata=json.loads(str(row["metadata_json"])),
        created_at=str(row["created_at"]),
    )


def _chunk_from_row(row: sqlite3.Row) -> StoredChunk:
    return StoredChunk(
        id=str(row["id"]),
        document_id=str(row["document_id"]),
        start=int(row["start"]),
        end=int(row["end"]),
        text=str(row["text"]),
    )


def _scan_from_row(row: sqlite3.Row) -> StoredScan:
    return StoredScan(
        id=str(row["id"]),
        report=json.loads(str(row["report_json"])),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
