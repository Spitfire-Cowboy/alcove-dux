"""Model and dataset catalog loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelCandidate:
    """A configured model candidate."""

    id: str
    provider: str
    model_id: str
    kind: str
    license: str
    source_url: str
    enabled_by_default: bool = False
    dimensions: int | None = None
    max_sequence_length: int | None = None


@dataclass(frozen=True)
class DatasetCandidate:
    """A configured dataset candidate."""

    id: str
    name: str
    kind: str
    license: str
    source_url: str
    acquisition: str
    enabled_by_default: bool = False


@dataclass(frozen=True)
class Catalog:
    """Resolved Alcove Dux catalog."""

    schema_version: int
    updated: str
    model_defaults: dict[str, str]
    dataset_defaults: dict[str, str]
    models: tuple[ModelCandidate, ...]
    datasets: tuple[DatasetCandidate, ...]
    raw: dict[str, Any]

    def model(self, candidate_id: str) -> ModelCandidate:
        """Return a model by catalog ID."""

        for candidate in self.models:
            if candidate.id == candidate_id:
                return candidate
        raise KeyError(f"Unknown model candidate: {candidate_id}")

    def dataset(self, candidate_id: str) -> DatasetCandidate:
        """Return a dataset by catalog ID."""

        for candidate in self.datasets:
            if candidate.id == candidate_id:
                return candidate
        raise KeyError(f"Unknown dataset candidate: {candidate_id}")

    @property
    def enabled_models(self) -> tuple[ModelCandidate, ...]:
        """Models enabled by default."""

        return tuple(candidate for candidate in self.models if candidate.enabled_by_default)

    @property
    def enabled_datasets(self) -> tuple[DatasetCandidate, ...]:
        """Datasets enabled by default."""

        return tuple(candidate for candidate in self.datasets if candidate.enabled_by_default)


def load_catalog(path: str | Path | None = None) -> Catalog:
    """Load the built-in JSON catalog, or a JSON catalog from ``path``."""

    if path is None:
        payload = resources.files("alcove_dux").joinpath("catalog.json").read_text(encoding="utf-8")
        data = json.loads(payload)
    else:
        catalog_path = Path(path)
        if catalog_path.suffix.lower() not in {".json"}:
            raise ValueError("Only JSON catalogs are supported by the base package today")
        data = json.loads(catalog_path.read_text(encoding="utf-8"))

    return Catalog(
        schema_version=int(data["schema_version"]),
        updated=str(data["updated"]),
        model_defaults=dict(data.get("model_defaults", {})),
        dataset_defaults=dict(data.get("dataset_defaults", {})),
        models=tuple(_model_from_mapping(item) for item in data.get("models", [])),
        datasets=tuple(_dataset_from_mapping(item) for item in data.get("datasets", [])),
        raw=data,
    )


def _model_from_mapping(item: dict[str, Any]) -> ModelCandidate:
    return ModelCandidate(
        id=str(item["id"]),
        provider=str(item["provider"]),
        model_id=str(item["model_id"]),
        kind=str(item["kind"]),
        license=str(item["license"]),
        source_url=str(item["source_url"]),
        enabled_by_default=bool(item.get("enabled_by_default", False)),
        dimensions=item.get("dimensions"),
        max_sequence_length=item.get("max_sequence_length"),
    )


def _dataset_from_mapping(item: dict[str, Any]) -> DatasetCandidate:
    return DatasetCandidate(
        id=str(item["id"]),
        name=str(item["name"]),
        kind=str(item["kind"]),
        license=str(item["license"]),
        source_url=str(item["source_url"]),
        acquisition=str(item["acquisition"]),
        enabled_by_default=bool(item.get("enabled_by_default", False)),
    )
