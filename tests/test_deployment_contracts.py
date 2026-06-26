from pathlib import Path


def test_release_workflow_installs_api_extra_for_metadata_check():
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "uv sync --locked --extra dev --extra api" in workflow


def test_dockerfile_installs_documents_extra_for_upload_api():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "uv sync --locked --no-dev --extra api --extra documents" in dockerfile


def test_hosted_postgres_healthcheck_uses_env_overrides():
    compose = Path("docker-compose.hosted.yml").read_text(encoding="utf-8")

    assert "pg_isready -U ${POSTGRES_USER:-alcove_dux} -d ${POSTGRES_DB:-alcove_dux}" in compose


def test_quickstart_uses_full_install_for_dashboard_uploads():
    quickstart = Path("docs/quickstart.md").read_text(encoding="utf-8")

    assert 'python -m pip install -e ".[dev,api,documents]"' in quickstart


def test_ci_validates_extras_resolver_contracts():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "uv sync --locked --extra alcove --extra documents" in workflow
    assert "uv sync --locked --extra all" in workflow
