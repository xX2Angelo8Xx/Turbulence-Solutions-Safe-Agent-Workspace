"""Tests for FIX-108: Verify pyyaml is declared as a dev dependency."""
import importlib.metadata
import re
from pathlib import Path

PYPROJECT_PATH = Path(__file__).parents[2] / "pyproject.toml"


def _get_dev_deps():
    text = PYPROJECT_PATH.read_text(encoding="utf-8")
    # Find the dev = [ ... ] block
    match = re.search(r'\[project\.optional-dependencies\].*?^dev\s*=\s*\[(.*?)\]', text, re.DOTALL | re.MULTILINE)
    if not match:
        return []
    block = match.group(1)
    return [item.strip().strip('"').strip("'") for item in block.split(",") if item.strip().strip('"').strip("'")]


def test_pyyaml_in_pyproject_dev_deps():
    deps = _get_dev_deps()
    pyyaml_entries = [d for d in deps if d.lower().startswith("pyyaml")]
    assert pyyaml_entries, f"pyyaml not found in pyproject.toml dev deps. Found: {deps}"


def test_pyyaml_version_constraint():
    deps = _get_dev_deps()
    pyyaml_entries = [d for d in deps if d.lower().startswith("pyyaml")]
    assert pyyaml_entries, "pyyaml not found in dev deps"
    entry = pyyaml_entries[0]
    assert ">=6" in entry, f"Expected pyyaml>=6 constraint, got: {entry}"


def test_yaml_import_succeeds():
    import yaml  # noqa: F401
    assert yaml is not None


def test_yaml_version_gte_6():
    import yaml
    version_str = yaml.__version__
    major = int(version_str.split(".")[0])
    assert major >= 6, f"yaml version {version_str} is less than 6"
