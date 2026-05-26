# Alcove Dux release checklist

This checklist keeps the public package identity, privacy boundary, and release workflow consistent.

- GitHub repository: `Spitfire-Cowboy/alcove-dux`
- Python package: `alcove-dux`
- Python import path: `alcove_dux`
- Product/plugin name: `Alcove Dux`

## Release rules

- Keep generated reports, local corpora, model caches, vector indexes, and device-specific paths out of version control.
- Keep private documents, local paths, credentials, PII, and private infrastructure details out of public docs and examples.

## Release steps

1. Confirm project metadata still uses `alcove-dux` and the import package still uses `alcove_dux`.
2. Update `VERSION`, `pyproject.toml`, and `CHANGELOG.md` for the release.
3. Rebuild any public examples or docs that are meant to ship with the release.
4. Run the release gate locally:
   ```bash
   python -m pytest tests/test_release_metadata.py -q
   python -m pytest -q
   python -m build
   python -m twine check dist/*
   ```
5. Confirm the CLI, docs, and Alcove plugin entry points still use `alcove-dux` or `alcove_dux` as appropriate.
6. Push the release commit to `main`.
7. Create a GitHub Release targeting `main`. Publishing the GitHub Release triggers `.github/workflows/release.yml`.
8. Confirm the release workflow builds successfully and, when appropriate, publishes to PyPI through the trusted publisher.
