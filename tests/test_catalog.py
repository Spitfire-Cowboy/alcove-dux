from alcove_dux.catalog import load_catalog


def test_load_catalog_has_defaults():
    catalog = load_catalog()

    assert catalog.schema_version == 1
    assert catalog.model_defaults["embedding_model"] == "baai_bge_small_en_v1_5"
    assert catalog.dataset_defaults["primary_llm_plagiarism"] == "plagbench"


def test_enabled_catalog_entries_are_available_by_id():
    catalog = load_catalog()

    enabled_model_ids = {model.id for model in catalog.enabled_models}
    enabled_dataset_ids = {dataset.id for dataset in catalog.enabled_datasets}

    assert "baai_bge_small_en_v1_5" in enabled_model_ids
    assert "pan_pc_11" in enabled_dataset_ids
    assert catalog.model("nomic_embed_text_v1_5").license == "Apache-2.0"
    assert catalog.dataset("plagbench").kind == "llm_plagiarism_benchmark"
