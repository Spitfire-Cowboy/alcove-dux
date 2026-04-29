# Benchmark Scorecard

Alcove Dux reports separate benchmark metrics instead of a single blended score.

## Metrics

- PAN precision, recall, granularity, and PlagDet when available.
- PAN text-alignment span precision and span recall.
- PlagBench F1 by category: verbatim, paraphrase, and summarization.
- PAWS false-positive rate for high-overlap non-paraphrases.
- MRPC F1 for paraphrase checks.
- STS error or rank correlation for semantic similarity calibration.

## Dataset Roles

- PAN-PC-11: plagiarism-specific evaluation.
- PAN 2014 Text Alignment: passage offsets and PlagDet-style metrics.
- PlagBench: generated verbatim, paraphrase, summary, and reuse cases.
- PAWS: high-overlap false-positive checks.
- STS Benchmark: semantic similarity calibration.
- MRPC: paraphrase classification checks.

## Commands

Run local evaluation checks:

```bash
python scripts/live_fire.py --limit 50
```

Run a threshold sweep:

```bash
python scripts/threshold_sweep.py --dataset plagbench --limit 4000
```

Save a calibration profile:

```bash
python scripts/calibrate_threshold.py --dataset plagbench --limit 1000
```

Generated reports are written under `reports/live-fire/` and are intended to stay local unless deliberately summarized for publication.

## Interpretation

Benchmark scores are similarity evidence, not document-level plagiarism labels. Include the dataset, split, sample size, model ID, thresholds, and command when publishing results.
