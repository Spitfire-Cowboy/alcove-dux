# Quick Start

This path installs Alcove Dux locally and runs a pairwise scan with the bundled examples.

## Install

```bash
python -m pip install ".[api]"
```

Check that the CLI is available:

```bash
alcove-dux catalog
```

## Run a pairwise scan

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

Open `reports/scan-review.html` in any browser to inspect matched passages. The `.alcove-dux` file is plain JSON and can be inspected in any text editor.

Keep generated reports under `reports/` unless they are deliberately prepared for sharing.

## Run a corpus scan

```bash
alcove-dux scan-corpus \
  examples/submitted.txt \
  examples/corpus \
  --out reports/corpus-scan.alcove-dux \
  --html reports/corpus-scan.html \
  --review-html reports/corpus-review.html
```

Open `reports/corpus-review.html` in any browser to inspect the matched passages. Use `reports/corpus-scan.alcove-dux` when you want the full machine-readable evidence record.

## Optional semantic matching

Semantic matching downloads and runs an embedding model, so it is opt-in:

```bash
python -m pip install ".[semantic]"
alcove-dux scan-corpus \
  examples/submitted.txt \
  examples/corpus \
  --out reports/corpus-semantic.alcove-dux \
  --semantic
```

First use with `--semantic` downloads roughly 130 MB of model data, so allow a minute or two on a cold cache.

## Local API

```bash
python -m pip install ".[api]"
uvicorn "alcove_dux.api:create_app" --factory --reload
```

Open `http://localhost:8000` for the local dashboard.
