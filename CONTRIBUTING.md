# Contributing

Thanks for helping build Alcove Dux. The project is local-first, evidence-first, and privacy-conscious.

## Local Setup

```bash
python -m pip install -e ".[dev,api]"
python -m pytest -q
python -m ruff check .
```

Optional extras:

```bash
python -m pip install -e ".[semantic]"  # embedding similarity
python -m pip install -e ".[documents]" # PDF and DOCX ingestion
python -m pip install -e ".[eval]"      # benchmark loaders
```

## Privacy Rules

- Keep private documents, corpora, generated reports, model caches, vector indexes, and local databases out of public commits.
- Keep private paths, credentials, names, emails, and institution-specific identifiers out of docs, tests, reports, and examples.
- Prefer short opaque lowercase document IDs such as `source-a` instead of names, emails, paths, filenames, course labels, or submission titles.
- Use evidence language: `exact overlap`, `near duplicate`, `possible paraphrase`, and `needs review`.
- Prefer non-accusatory language in product surfaces.
- Handle embeddings and indexes as private artifacts because they may reveal corpus membership.

## Development Checks

Run these before proposing changes:

```bash
python -m pytest -q
python -m ruff check .
python -m build
python -m twine check dist/*
docker compose config >/dev/null
```

Benchmark reports are written under `reports/`, which is intentionally ignored by Git.

## Open Source Automation

The repository includes:

- CI and coverage upload
- CodeQL static analysis
- secret scanning
- Dependency Review for pull requests
- OpenSSF Scorecard
- Dependabot for GitHub Actions and Python dependency updates
- CodeRabbit review guidance
