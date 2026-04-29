# Alcove Dux Release Checklist

This checklist keeps the public package identity, privacy boundary, and release workflow consistent.

- GitHub repository: `Spitfire-Cowboy/alcove-dux`
- Python package: `alcove-dux`
- Python import path: `alcove_dux`
- Product/plugin name: `Alcove Dux`

## Release Rules

- Keep generated reports, local corpora, model caches, vector indexes, and device-specific paths out of version control.
- Keep private documents, local paths, credentials, PII, and private infrastructure details out of public docs and examples.

## Readiness Checklist

- Confirm project metadata uses `alcove-dux`.
- Confirm the import package uses `alcove_dux`.
- Confirm CLI entry points and docs use `alcove-dux` or `alcove_dux` as appropriate.
- Confirm Alcove plugin entry points use the public package name.
- Rebuild examples, docs, CI badges, release metadata, and PyPI publishing configuration.
- Recommended release gate: publish after privacy, generated-artifact, and package metadata checks pass.
