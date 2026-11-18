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

### Policy-cap score calibration

For a detector that emits normalized scores from 0 to 1, calibrate against held-out labeled
examples at the false-positive-rate cap required by the deployment policy. The
input is a JSON object with parallel `labels` (booleans) and `scores` (numbers)
arrays. The held-out set must contain at least one positive and one negative:
a negatives-only set can measure FPR but cannot measure TPR for selection.

```json
{
  "labels": [true, true, false, false],
  "scores": [0.91, 0.73, 0.42, 0.18]
}
```

Select the threshold with the highest true-positive rate that stays within a
1% false-positive cap:

```bash
python scripts/calibrate_score_threshold.py \
  --input reports/held-out-scores.json \
  --dataset-id held-out-2026-11 \
  --detector-id detector-v2 \
  --fpr-cap 0.01 \
  --out reports/calibration/detector-v2-policy-cap.json
```

Pass `--threshold` repeatedly to publish results for a fixed threshold grid.
Without explicit thresholds, the script evaluates each observed score plus a
conservative threshold above the maximum when that threshold remains within the
0-to-1 scan range. When the maximum score is 1, the grid stops at 1 and strict
caps may have no qualifying threshold. The profile records FPR, FNR, and TPR at
every threshold, the selected threshold, and the policy cap. Calibration
fails if the labels contain no negative examples or none of the supplied
thresholds satisfies the cap; it does not treat an unmeasurable FPR as zero.

The `detector_id` is binding provenance, not a display label. The `scan` and
`scan-corpus` commands use `baseline_lexical` and reject any other profile
detector ID before applying its threshold. Other detector profiles remain
publishable artifacts but cannot control lexical scans.

Generated reports are written under `reports/live-fire/` and are intended to stay local unless deliberately summarized for publication.

## Large peS2o Chroma Stress Runs

The peS2o batch harness indexes bounded slices into Chroma, writes checkpoint
state, and exits. Re-running the same command resumes from `next_shard` and
`next_line`.

```bash
python scripts/pes2o_chroma_batch.py \
  --run-id pes2o-train-1m-bge-chroma-batched \
  --target-passages 1000000 \
  --batch-passages 25000 \
  --flush-size 512 \
  --max-seconds 600 \
  --hf-cache /path/to/hf-cache \
  --device cuda
```

For inspection-only planning, print the next slice without loading Chroma or an
embedding model:

```bash
python scripts/pes2o_chroma_batch.py --plan-only
```

Useful controls for bounded stress runs:

- `--batch-passages`: limits how many passages one invocation indexes.
- `--flush-size`: controls the Chroma upsert chunk size.
- `--max-seconds`: asks the process to checkpoint and exit after a time budget.
- `--gpu-max-temp-c`: pauses before indexing when `nvidia-smi` reports a hot GPU.
- `--max-upsert-seconds`: flags slow Chroma persistence after a completed batch.
- `--min-passages-per-second`: flags low total throughput after a completed batch.
- `--collection-shard-size`: writes into suffixed Chroma collections once a shard
  reaches the configured size.

For large Chroma stress tests, collection sharding can keep later batches easier
to inspect:

```bash
python scripts/pes2o_chroma_batch.py \
  --run-id pes2o-train-1m-bge-chroma-batched \
  --target-passages 1000000 \
  --batch-passages 5000 \
  --flush-size 2048 \
  --collection-shard-size 250000 \
  --max-seconds 240 \
  --max-upsert-seconds 75 \
  --min-passages-per-second 80 \
  --hf-cache /path/to/hf-cache \
  --device cuda
```

The base Chroma collection counts as shard 0. Later writes go to suffixed
collections such as `pes2o_train_bge_small_shard_0001`. Retrieval over sharded
Chroma collections should query each collection and merge the top-k hits.

One completed 1M-passage peS2o stress run using this harness reported
`target_reached` with 630,000 records in the base collection, 250,000 records in
`pes2o_train_bge_small_shard_0001`, and 120,000 records in
`pes2o_train_bge_small_shard_0002`. The run reported about 86 minutes of summed
batch wall time excluding manual inspection pauses, and a local vectorstore size
of about 2.33 GiB.

## Interpretation

Benchmark scores are similarity evidence, not document-level plagiarism labels. Include the dataset, split, sample size, model ID, thresholds, and command when publishing results.
