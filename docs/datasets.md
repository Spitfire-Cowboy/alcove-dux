# Dataset Acquisition

Alcove Dux supports two dataset classes:

- benchmark datasets suited to lightweight local evaluation
- larger corpora that can be streamed, sampled, or stored on dedicated infrastructure

## Lightweight Evaluation Targets

Supported lightweight targets:

- MRPC through the GLUE benchmark.
- STS Benchmark through the GLUE benchmark.
- PAWS Wiki.
- PlagBench public evaluation CSV from the public GitHub artifact.

The local evaluation harness supports MRPC, STS, PAWS, and PlagBench:

```bash
python scripts/live_fire.py --limit 50
```

Reports are written to `reports/live-fire/` and are intended to stay local unless deliberately summarized for publication.

## Guarded Downloads

PAN14 Text Alignment provides span-level scoring data and uses the PAN XML truth format.

PAN-PC-11 is a larger plagiarism-specific corpus.

peS2o is a large academic-corpus backend suited to dedicated storage. The full corpus requires hundreds of GB of processed data storage.

## Policy

Recommended downloader behavior:

- write under `data/`
- keep raw datasets out of commits
- record source URL, license, version, and download timestamp
- include an explicit flag for large downloads
- preserve attribution requirements in generated benchmark reports
