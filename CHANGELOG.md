# Changelog

All notable changes to Alcove Dux are documented here.

## Unreleased

## 0.1.1 - 2026-06-25

### Added

- AI-use stigma research note tying self-report bias in educational AI-use surveys to Alcove Dux positioning, review UX, and research methods.
- README links for the new AI-use stigma note.

### Changed

- Updated GitHub Actions dependencies: `actions/setup-python` 6.3.0, `actions/checkout` 7.0.0, `codecov/codecov-action` 7.0.0, and `astral-sh/setup-uv` 8.2.0.
- Dashboard-first README and quickstart guidance for teachers, reviewers, and institutional deployments.
- Public-safe documentation updates for privacy, local-first deployment, report interpretation, and evidence-first review framing.
- Tightened report wording and release guidance across docs.
- Updated CodeRabbit configuration to use supported review instructions.
- Updated the Scorecard workflow to avoid noisy SARIF/code-scanning publication while keeping the security signal.

### Security

- Locked patched dependency versions for `pypdf`, `idna`, and `urllib3`.
- Updated the `alcove-search` extra to avoid pulling a vulnerable `pypdf` chain.
- Added `uv` conflict metadata so incompatible extras do not resolve together silently.

## 0.1.0 - 2026-04-28

- Seeded the local-first Python package, CLI, FastAPI dashboard, and report renderers.
- Added exact, fuzzy, semantic, reranked, corpus, and benchmark-oriented scan paths.
- Added configurable model and dataset catalogs, multilingual candidates, and calibration profiles.
- Added PAN, PlagBench, PAWS, STS, MRPC, ChromaDB, zvec, and Alcove integration scaffolding.
- Added privacy-preserving reports, screen-reader-friendly HTML surfaces, and open-source hardening workflows.
