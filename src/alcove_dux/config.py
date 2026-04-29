"""Runtime scan configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from alcove_dux.catalog import Catalog


@dataclass(frozen=True)
class RuntimeConfig:
    """Resolved model, dataset, and threshold choices for a scan."""

    schema_version: int
    catalog_schema_version: int
    embedding_model_id: str | None
    long_context_embedding_model_id: str | None
    multilingual_embedding_model_id: str | None
    reranker_model_id: str | None
    baseline_lexical_threshold: float
    semantic_similarity_threshold: float
    semantic_top_k: int
    calibration_profile_id: str | None
    language: str | None
    enabled_dataset_ids: tuple[str, ...]

    @classmethod
    def from_catalog(
        cls,
        catalog: Catalog,
        *,
        embedding_model_id: str | None = None,
        long_context_embedding_model_id: str | None = None,
        multilingual_embedding_model_id: str | None = None,
        reranker_model_id: str | None = None,
        baseline_lexical_threshold: float | None = None,
        semantic_similarity_threshold: float = 0.72,
        semantic_top_k: int = 5,
        calibration_profile_id: str | None = None,
        language: str | None = None,
        enabled_dataset_ids: tuple[str, ...] | None = None,
    ) -> RuntimeConfig:
        """Resolve runtime config from a catalog and optional overrides."""

        resolved_embedding = embedding_model_id or catalog.model_defaults.get("embedding_model")
        resolved_long_context = (
            long_context_embedding_model_id
            or catalog.model_defaults.get("long_context_embedding_model")
        )
        resolved_multilingual = (
            multilingual_embedding_model_id
            or catalog.model_defaults.get("multilingual_embedding_model")
        )
        resolved_reranker = reranker_model_id or catalog.model_defaults.get("reranker_model")
        for model_id in (
            resolved_embedding,
            resolved_long_context,
            resolved_multilingual,
            resolved_reranker,
        ):
            if model_id:
                catalog.model(model_id)

        resolved_datasets = enabled_dataset_ids or tuple(
            dataset.id for dataset in catalog.enabled_datasets
        )
        for dataset_id in resolved_datasets:
            catalog.dataset(dataset_id)

        return cls(
            schema_version=1,
            catalog_schema_version=catalog.schema_version,
            embedding_model_id=resolved_embedding,
            long_context_embedding_model_id=resolved_long_context,
            multilingual_embedding_model_id=resolved_multilingual,
            reranker_model_id=resolved_reranker,
            baseline_lexical_threshold=(
                baseline_lexical_threshold
                if baseline_lexical_threshold is not None
                else _catalog_threshold(catalog)
            ),
            semantic_similarity_threshold=semantic_similarity_threshold,
            semantic_top_k=semantic_top_k,
            calibration_profile_id=calibration_profile_id,
            language=language,
            enabled_dataset_ids=tuple(resolved_datasets),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["enabled_dataset_ids"] = list(self.enabled_dataset_ids)
        return payload


def _catalog_threshold(catalog: Catalog) -> float:
    value = catalog.model_defaults.get("baseline_lexical_threshold", "0.50")
    return float(value)
