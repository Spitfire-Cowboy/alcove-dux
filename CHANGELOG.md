# Changelog

All notable changes to Alcove Dux are documented here.

## Unreleased

### Added

- Dashboard-first README and quickstart guidance for teachers, reviewers, and institutional deployments.
- Public-safe documentation updates for privacy, local-first deployment, and report interpretation.
- GitHub Pages demo and release-process templates for contributors and maintainers.

### Changed

- Tightened report wording, evidence framing, and release guidance across docs.
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
