import pytest

from alcove_dux.catalog import load_catalog
from alcove_dux.config import RuntimeConfig


def test_runtime_config_uses_catalog_defaults():
    catalog = load_catalog()

    config = RuntimeConfig.from_catalog(catalog)

    assert config.embedding_model_id == "baai_bge_small_en_v1_5"
    assert config.long_context_embedding_model_id == "nomic_embed_text_v1_5"
    assert config.multilingual_embedding_model_id == (
        "sentence_transformers_paraphrase_multilingual_minilm_l12_v2"
    )
    assert config.reranker_model_id == "cross_encoder_ms_marco_minilm_l6_v2"
    assert config.baseline_lexical_threshold == 0.50
    assert config.semantic_similarity_threshold == 0.72
    assert config.semantic_top_k == 5
    assert config.calibration_profile_id is None
    assert "pan_2014_text_alignment" in config.enabled_dataset_ids


def test_runtime_config_allows_catalog_overrides():
    catalog = load_catalog()

    config = RuntimeConfig.from_catalog(
        catalog,
        embedding_model_id="sentence_transformers_all_minilm_l6_v2",
        multilingual_embedding_model_id="intfloat_multilingual_e5_small",
        enabled_dataset_ids=("plagbench",),
        baseline_lexical_threshold=0.42,
        semantic_similarity_threshold=0.81,
        semantic_top_k=3,
        calibration_profile_id="reports/calibration/profile.json",
        language="es",
    )

    assert config.embedding_model_id == "sentence_transformers_all_minilm_l6_v2"
    assert config.multilingual_embedding_model_id == "intfloat_multilingual_e5_small"
    assert config.enabled_dataset_ids == ("plagbench",)
    assert config.to_dict()["enabled_dataset_ids"] == ["plagbench"]
    assert config.baseline_lexical_threshold == 0.42
    assert config.semantic_similarity_threshold == 0.81
    assert config.semantic_top_k == 3
    assert config.calibration_profile_id == "reports/calibration/profile.json"
    assert config.language == "es"


def test_runtime_config_rejects_unknown_catalog_ids():
    catalog = load_catalog()

    with pytest.raises(KeyError):
        RuntimeConfig.from_catalog(catalog, embedding_model_id="missing_model")

    with pytest.raises(KeyError):
        RuntimeConfig.from_catalog(catalog, enabled_dataset_ids=("missing_dataset",))
