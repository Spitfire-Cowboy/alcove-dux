# Configuration

Alcove Dux keeps model and dataset choices configurable. The public catalog is [`config/catalog.yaml`](../config/catalog.yaml), and the package also ships a JSON mirror so the base install has no YAML dependency.

## Model Selection

The app exposes three configurable model slots:

- `embedding_model`: default semantic similarity model.
- `long_context_embedding_model`: optional model for long chunks or document-level comparison.
- `reranker_model`: optional cross-encoder for top candidate pairs.

Initial defaults:

```yaml
embedding_model: baai_bge_small_en_v1_5
long_context_embedding_model: nomic_embed_text_v1_5
reranker_model: cross_encoder_ms_marco_minilm_l6_v2
```

Threshold calibration is dataset-specific. Cosine similarity is a model score, not a universal probability.

The baseline lexical threshold is `0.50`, chosen from PlagBench and PAN14 calibration sweeps. It is not a policy boundary.

## Dataset Selection

Dataset loaders can be enabled independently. The evaluation catalog includes:

- PAN-PC-11 for plagiarism detection.
- PAN 2014 Text Alignment for passage offsets and PlagDet-style metrics.
- PlagBench for LLM-generated paraphrase, summary, and reuse cases.
- PAWS for high-overlap paraphrase and false-positive checks.
- STS Benchmark for semantic similarity calibration.
- MRPC for compact paraphrase checks.

Large corpora like peS2o stay disabled by default until local storage, sampling, and attribution requirements are clear.

## Report Provenance

Scan reports record the resolved model and dataset configuration, including IDs, licenses, thresholds, chunking strategy, and document hashes. This keeps Alcove Dux evidence auditable.

Public reports are designed to omit private paths, credentials, device names, and personally identifying information unless a user deliberately exports document text.

Alcove Dux report files use the `.alcove-dux` extension and JSON content. The public schema lives at [`schemas/alcove-dux-report.schema.json`](../schemas/alcove-dux-report.schema.json).
