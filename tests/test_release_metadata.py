import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_version_file_matches_package_metadata():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert version == pyproject["project"]["version"]


def test_changelog_has_current_version_entry():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert f"## {version} -" in changelog
