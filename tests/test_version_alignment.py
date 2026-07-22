"""Keep package, extension, lockfile, and bundled skill versions aligned."""

from __future__ import annotations

import json
from pathlib import Path
import re


try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SKILL = ROOT / "src" / "perplexity_web_mcp" / "data"
PROJECT_SKILL = ROOT / "skills" / "perplexity-web-mcp"


def _skill_version(path: Path) -> str:
    match = re.search(r'^\s+version:\s+"([^"]+)"$', path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None, f"No skill version found in {path}"
    return match.group(1)


def test_release_versions_are_aligned() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = pyproject["project"]["version"]
    manifest = json.loads((ROOT / "desktop-extension" / "manifest.json").read_text(encoding="utf-8"))
    lockfile = (ROOT / "uv.lock").read_text(encoding="utf-8")

    assert manifest["version"] == package_version
    assert _skill_version(PACKAGE_SKILL / "SKILL.md") == package_version
    assert _skill_version(PROJECT_SKILL / "SKILL.md") == package_version
    assert f"## [{package_version}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(
        rf'name = "perplexity-web-mcp-cli"\nversion = "{re.escape(package_version)}"',
        lockfile,
    )


def test_project_and_packaged_skill_trees_match() -> None:
    package_files = {path.relative_to(PACKAGE_SKILL) for path in PACKAGE_SKILL.rglob("*") if path.is_file()}
    project_files = {path.relative_to(PROJECT_SKILL) for path in PROJECT_SKILL.rglob("*") if path.is_file()}

    assert project_files == package_files
    for relative_path in sorted(package_files):
        assert (PROJECT_SKILL / relative_path).read_bytes() == (PACKAGE_SKILL / relative_path).read_bytes()
