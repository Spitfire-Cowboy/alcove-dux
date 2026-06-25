# Alcove Dux Release Checklist

This checklist keeps the public package identity, privacy boundary, and release workflow consistent.

- GitHub repository: `Spitfire-Cowboy/alcove-dux`
- Python package: `alcove-dux`
- Python import path: `alcove_dux`
- Product/plugin name: `Alcove Dux`

## Release Rules

- Keep generated reports, local corpora, model caches, vector indexes, and device-specific paths out of version control.
- Keep private documents, local paths, credentials, PII, and private infrastructure details out of public docs and examples.
- Cut releases from `main`.
- Treat `develop` as the integration branch and merge it into `main` only after security, dependency, and CI checks are green.

## Current Release Milestones

1. **Security baseline on `develop`**
   - Merge dependency and workflow hardening changes into `develop`.
   - Confirm Dependabot alerts are closed against the default branch.
   - Confirm open code-scanning alerts remain at zero.
2. **Release candidate merge to `main`**
   - Open a `develop` → `main` PR after `develop` is green.
   - Review the branch diff for dependency, workflow, and docs changes that will ship.
   - Confirm release notes and version metadata are ready before merging.
3. **Publish from `main`**
   - Merge the release PR into `main`.
   - Create the GitHub release from `main`.
   - Let the release workflow build and, when intended, publish to PyPI from `main`.

## Readiness Checklist

- Confirm project metadata uses `alcove-dux`.
- Confirm the import package uses `alcove_dux`.
- Confirm CLI entry points and docs use `alcove-dux` or `alcove_dux` as appropriate.
- Confirm Alcove plugin entry points use the public package name.
- Rebuild examples, docs, CI badges, release metadata, and PyPI publishing configuration.
- Recommended release gate: publish after privacy, generated-artifact, and package metadata checks pass.

## `develop` → `main` Merge Prep

- Confirm the `develop` head has:
  - passing CI,
  - passing CodeQL,
  - passing secret scan,
  - passing Codecov patch status,
  - and no open blocking review threads.
- Check `git log origin/main..origin/develop` and summarize the commits that will land in `main`.
- Check `git diff --stat origin/main...origin/develop` for unexpected files or generated artifacts.
- Confirm `CHANGELOG.md` has an `Unreleased` section that matches the release candidate scope.
- Confirm `VERSION` and `pyproject.toml` match the intended release number before the merge PR lands.
- If `main` contains docs or release-process changes not yet on `develop`, merge or cherry-pick them back so the branches do not drift after the release.

## Release Cut Sequence

1. Merge the final security/dependency PR into `develop`.
2. Re-check GitHub Security:
   - Dependabot: 0 open alerts.
   - Code scanning: 0 open alerts.
3. Open and review the `develop` → `main` release PR.
4. Update `VERSION` and `CHANGELOG.md` if cutting a new version such as `0.1.1`.
5. Merge the release PR into `main`.
6. Create the GitHub release targeting the merge commit on `main`.
7. Verify the Release workflow finishes its build checks.
8. If publishing is intended, verify the PyPI publish job ran from `main` and succeeded.
