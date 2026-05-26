# CLI Usage

The `alcove-dux` CLI supports catalog inspection, pairwise document scans, and local corpus scans.

## Catalog

Print the configured model and dataset catalog:

```bash
alcove-dux catalog
```

The default candidate catalog is stored in [`config/catalog.yaml`](../config/catalog.yaml) and mirrored in the package as JSON.
Run `alcove-dux catalog` when you need the valid model or dataset IDs for flags such as `--embedding-model` and `--dataset`.

## Pairwise Scan

Compare one submitted document to one known source:

```bash
alcove-dux scan submitted.txt source.txt --out reports/scan.alcove-dux
```

Argument order is `SUBMITTED_FILE SOURCE_FILE`.

Useful options:

- `--min-score`: lexical threshold for evidence inclusion.
- `--html`: public-safe HTML summary output.
- `--review-html`: local review HTML report with matched text snippets.
- `--calibration-profile`: apply a saved threshold profile.
- `--semantic`: enable semantic chunk matching.
- `--rerank`: rerank candidate matches with the configured cross-encoder.
- `--embedding-model`: choose a configured embedding model.
- `--language`: record a language hint in the runtime configuration.
- `--dataset`: record enabled benchmark or dataset context.

First use with `--semantic` downloads roughly 130 MB of model data, so allow a minute or two on a cold cache.

## Corpus Scan

Scan one submitted document against a local folder of source files:

```bash
alcove-dux scan-corpus submitted.txt corpus/ --out reports/corpus-scan.alcove-dux
```

Corpus scans support plain text and Markdown source folders. Pairwise and API workflows can also ingest PDF and DOCX when document extras are installed.
After a scan, open the generated `--review-html` file in a browser for local side-by-side review, or inspect the `.alcove-dux` JSON directly.

## Calibration

Create a lexical threshold profile:

```bash
python scripts/calibrate_threshold.py \
  --dataset plagbench \
  --limit 1000 \
  --out reports/calibration/plagbench.json
```

Apply it during a scan:

```bash
alcove-dux scan submitted.txt source.txt \
  --calibration-profile reports/calibration/plagbench.json \
  --out reports/calibrated.alcove-dux
```

## Benchmark Helpers

Run local checks:

```bash
python scripts/live_fire.py --limit 50
python scripts/threshold_sweep.py --dataset plagbench --limit 4000
```

Generated benchmark outputs are written under `reports/` unless they are deliberately summarized for publication.
