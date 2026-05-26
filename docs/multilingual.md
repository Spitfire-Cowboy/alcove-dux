# Multilingual Detection

Alcove Dux can scan Unicode text in any language at the lexical layer, but high-quality similarity review outside English requires language-specific calibration.

## Current Support

- Plain text normalization preserves Unicode text.
- Exact token sequence matching is configured for languages with whitespace-separated words.
- Semantic matching can be configured with multilingual embedding models.
- Runtime reports can record a language hint such as `en`, `es`, `fr`, or `multilingual`.

## Model Candidates

Configured multilingual candidates:

- `sentence_transformers_paraphrase_multilingual_minilm_l12_v2`
- `intfloat_multilingual_e5_small`

Use the multilingual model override when scanning non-English or cross-lingual corpora:

```bash
alcove-dux scan examples/submitted.txt examples/source.txt \
  --language es \
  --embedding-model intfloat_multilingual_e5_small \
  --semantic
```

## Calibration Rule

English thresholds are not a reliable default for every language. Calibrate by language, writing system, domain, and task type:

- exact reuse
- lightly edited reuse
- paraphrase
- cross-lingual reuse
- machine-translated reuse

Calibration profiles support `language` and `task_type` fields:

```bash
python scripts/calibrate_threshold.py \
  --dataset plagbench \
  --language en \
  --task-type paraphrase \
  --out reports/calibration/en-paraphrase.json
```

For datasets that include language metadata, use grouped profiles:

```bash
python scripts/calibrate_threshold.py \
  --dataset plagbench \
  --group-by-language \
  --task-type paraphrase \
  --out reports/calibration/by-language.json
```

## Benchmark Candidates

- PAWS-X for multilingual high-overlap paraphrase and false-positive pressure.
- SemEval 2017 STS for multilingual and cross-lingual semantic similarity.
- PAN at FIRE 2011 Cross-Language Indian Text Reuse for English-Hindi document-level reuse.
- BUCC Bitext Mining for cross-lingual sentence retrieval, with license unknown and disabled by default.

## Known Gaps

- Cross-lingual similarity review uses multilingual embeddings and reranking rather than English lexical thresholds.
- Public multilingual plagiarism benchmarks need license review before inclusion in default CI.
