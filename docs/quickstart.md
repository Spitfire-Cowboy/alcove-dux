# Quick Start

This path installs Alcove Dux locally and opens the browser-based dashboard first, then shows the CLI workflow for scripting and automation.

## Install

You'll need Python 3.11 or later. If you're not sure whether it is already installed, ask your IT department or start with [python.org](https://www.python.org/).

```bash
python -m pip install ".[api]"
```

Check that the CLI is available:

```bash
alcove-dux catalog
```

## Dashboard quick start

Start the local dashboard:

```bash
uvicorn "alcove_dux.api:create_app" --factory --reload
```

Open `http://localhost:8000` in your browser, upload the documents you want to review, and run a scan there.

This is the recommended path for teachers and reviewers who do not want to work in the terminal after installation.

## Docker quick start

If you have Docker available, you can also run the local dashboard with:

```bash
docker compose up --build
```

Then open `http://localhost:8000`.

## CLI pairwise scan

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

## Shared or institutional setup

If you are supporting a department, school, or campus installation, see [Deployment Notes](deployment.md) for the shared-server and Docker Compose path.

## Local API

```bash
python -m pip install ".[api]"
uvicorn "alcove_dux.api:create_app" --factory --reload
```

Open `http://localhost:8000` for the local dashboard.
