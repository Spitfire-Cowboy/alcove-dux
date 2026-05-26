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

## Proposing changes

1. Fork the repository and branch from `develop`.
2. Make the smallest change that clearly solves the problem.
3. Run the local checks below before opening a PR.
4. Open the PR against `develop` and summarize the user-visible impact, tests, and any privacy considerations.

If you are looking for something useful to tackle, check the roadmap for current priorities before starting a larger change.

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

Please follow the project's [Code of Conduct](CODE_OF_CONDUCT.md) in issues, reviews, and pull requests.
