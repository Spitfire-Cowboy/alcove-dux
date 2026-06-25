# Changelog

All notable changes to Alcove Dux are documented here.
This project follows the spirit of Keep a Changelog.

## [Unreleased]

### Added

- README hero and social preview assets under `docs/assets/`.
- Community health files: `CODE_OF_CONDUCT.md`, issue templates, and a pull request template.

### Changed

- Refined README, quickstart, CLI, reports, privacy, research, and contributing docs for clearer audience framing and stronger evidence-first language.
- Added `main` to CI workflow branch triggers.
- Clarified CLI positional argument names in `--help` output.
- Rewrote the release checklist into an ordered release procedure.

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

### Added

- Local-first Python package, CLI, FastAPI dashboard, and report renderers.
- Exact, fuzzy, semantic, reranked, corpus, and benchmark-oriented scan paths.
- Configurable model and dataset catalogs, multilingual candidates, and calibration profiles.
- PAN, PlagBench, PAWS, STS, MRPC, ChromaDB, zvec, and Alcove integration scaffolding.
- Privacy-preserving reports, screen-reader-friendly HTML surfaces, and open-source hardening workflows.

[Unreleased]: https://github.com/Spitfire-Cowboy/alcove-dux/compare/0.1.0...HEAD
