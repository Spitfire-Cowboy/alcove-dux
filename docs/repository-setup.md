# Repository Setup

Alcove Dux keeps third-party automation optional where possible. The repository ships
configuration files, but maintainers can decide which services to enable.

## Default Branch

Use `develop` as the default branch for active development. Keep `main` for
stable release points after package and PyPI setup.

## Review And Quality Services

- CodeRabbit: optional. Install the GitHub app for the repository to use
  `.coderabbit.yaml`.
- Codecov: optional. Install the Codecov GitHub app or configure repository
  access. CI uploads `coverage.xml` from the coverage job and does not fail if
  Codecov is unavailable.
- CodeQL: optional through `.github/workflows/codeql.yml` for Python security and
  quality queries. Set repository variable `CODEQL_ENABLED=true` after GitHub
  Code Security/code scanning is enabled for the repository.
- Semgrep: optional CodeQL complement. Set repository variable
  `SEMGREP_ENABLED=true` to run it on pushes and PRs. Set
  `SEMGREP_BLOCKING=true` when maintainers want findings to block CI.
- Gitleaks: enabled through `.github/workflows/secrets.yml`.
- Dependency Review: optional. Set repository variable
  `DEPENDENCY_REVIEW_ENABLED=true` after Dependency Graph and GitHub Advanced
  Security are available for the repository.
- OpenSSF Scorecard: enabled for `develop` and scheduled runs.
- Dependabot: configured for GitHub Actions and Python package updates.
- `uv.lock`: checked in for reproducible workflow and container dependency resolution.

## Scorecard Follow-Up

Some current Scorecard findings require maintainer or repository-governance follow-through rather
than code-only changes:

- `MaintainedID`: cannot clear until the repository is older than 90 days.
- `CodeReviewID`: depends on reviewed pull request history accumulating over time.
- `CIIBestPracticesID`: requires pursuing the OpenSSF Best Practices badge externally.
- `FuzzingID`: requires adding a real fuzzing target and automation; this is feature work, not a
  workflow-only fix.
- `SecurityPolicyID`: keep `SECURITY.md` linked to GitHub private reporting and verify GitHub shows
  the repository policy at `Security -> Policy`.

## PyPI

Recommended publishing gate: review the package metadata, release workflow, and
privacy boundary together. The release workflow expects a `pypi` GitHub environment and supports
trusted publishing through PyPI's GitHub Actions publisher flow.

PyPI publishing is configured for releases from `main`. The workflow can build packages
from a GitHub Release or a manual dispatch, and the upload job runs when
the release target is `main`, or when a maintainer manually dispatches the
workflow from `main` with `publish=true`.

## Privacy Boundary

Before making the repository public, run a tracked-file scan for:

- private paths
- credentials or tokens
- private infrastructure names
- raw corpus excerpts
- generated reports outside `examples/reports`
- legacy package or project names
