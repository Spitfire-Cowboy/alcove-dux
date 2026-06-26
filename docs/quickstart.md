# Quick Start

This path installs Alcove Dux locally and runs a pairwise scan with the bundled examples.

## Install

For the full local workflow, including the upload dashboard and PDF/DOCX ingestion:

```bash
python -m pip install -e ".[dev,api,documents]"
```

If you only want plain-text CLI scans, `.[dev]` is enough.

Check that the CLI is available:

```bash
alcove-dux catalog
```

## Run A Pairwise Scan

```bash
alcove-dux scan \
  examples/submitted.txt \
  examples/source.txt \
  --out reports/scan.alcove-dux \
  --html reports/scan.html \
  --review-html reports/scan-review.html
```

Outputs:

- `reports/scan.alcove-dux`: JSON evidence report.
- `reports/scan.html`: public-safe HTML summary without raw matched text.
- `reports/scan-review.html`: local review page with matched text snippets.

Keep generated reports under `reports/` unless they are deliberately prepared for sharing.

## Run A Corpus Scan

```bash
alcove-dux scan-corpus \
  examples/submitted.txt \
  examples/corpus \
  --out reports/corpus-scan.alcove-dux \
  --html reports/corpus-scan.html \
  --review-html reports/corpus-review.html
```

## Optional Semantic Matching

Semantic matching downloads and runs an embedding model, so it is opt-in:

```bash
python -m pip install -e ".[semantic]"
alcove-dux scan-corpus \
  examples/submitted.txt \
  examples/corpus \
  --out reports/corpus-semantic.alcove-dux \
  --semantic
```

## Local API

```bash
python -m pip install -e ".[api]"
uvicorn "alcove_dux.api:create_app" --factory --reload
```

That `.[api]` install is enough for pasted text and plain-text uploads.
For PDF/DOCX uploads in the local dashboard, install:

```bash
python -m pip install -e ".[api,documents]"
```

Open `http://localhost:8000` for the local dashboard.
