"""Edge-case tests for FIX-108: PyYAML dev dependency.

Tests boundary conditions and robustness of the pyyaml dependency declaration.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

PYPROJECT_PATH = Path(__file__).parents[2] / "pyproject.toml"
PYPROJECT_TEXT = PYPROJECT_PATH.read_text(encoding="utf-8")


def _get_dev_section() -> str:
    """Extract the raw dev = [...] block from pyproject.toml."""
    match = re.search(
        r'\[project\.optional-dependencies\].*?^dev\s*=\s*\[(.*?)\]',
        PYPROJECT_TEXT,
        re.DOTALL | re.MULTILINE,
    )
    assert match, "Could not find [project.optional-dependencies] dev section"
    return match.group(1)


def test_pyyaml_not_duplicated():
    """pyyaml must appear exactly once in dev deps to avoid pip resolution issues."""
    block = _get_dev_section()
    entries = [item.strip().strip('"').strip("'") for item in block.split(",") if item.strip().strip('"').strip("'")]
    pyyaml_entries = [e for e in entries if e.lower().startswith("pyyaml")]
    assert len(pyyaml_entries) == 1, f"Expected exactly 1 pyyaml entry, found {len(pyyaml_entries)}: {pyyaml_entries}"


def test_pyyaml_upper_bound_present():
    """pyyaml spec must include an upper bound (<7) to prevent major version surprises."""
    block = _get_dev_section()
    # Extract each quoted entry as a whole (handles commas inside version specs)
    quoted_entries = re.findall(r'["\']([^"\']+)["\']', block)
    pyyaml_entries = [e for e in quoted_entries if e.lower().startswith("pyyaml")]
    assert pyyaml_entries, "pyyaml not found in dev deps"
    assert "<7" in pyyaml_entries[0], f"Expected upper bound <7 in: {pyyaml_entries[0]}"


def test_yaml_safe_load_works():
    """yaml.safe_load must parse a basic YAML document without raising."""
    doc = yaml.safe_load("key: value\nlist:\n  - item1\n  - item2")
    assert doc == {"key": "value", "list": ["item1", "item2"]}


def test_yaml_dumps_and_reloads():
    """yaml.dump/safe_load round-trip must be lossless for simple structures."""
    data = {"name": "FIX-108", "version": 6, "active": True}
    dumped = yaml.dump(data)
    reloaded = yaml.safe_load(dumped)
    assert reloaded == data


def test_yaml_handles_empty_document():
    """yaml.safe_load on an empty string returns None — not an exception."""
    result = yaml.safe_load("")
    assert result is None


def test_yaml_safe_load_rejects_arbitrary_objects():
    """yaml.safe_load (not full_load) must refuse !!python/object tags."""
    import pytest
    evil_yaml = "!!python/object/apply:os.system ['echo evil']"
    with pytest.raises(yaml.constructor.ConstructorError):
        yaml.safe_load(evil_yaml)


def test_pyyaml_in_toml_under_dev_section_not_main():
    """pyyaml must be a dev (optional) dep, not a mandatory runtime dep."""
    # Runtime deps are under [project] dependencies = [...]
    runtime_match = re.search(
        r'^\[project\][^\[]*?^dependencies\s*=\s*\[(.*?)\]',
        PYPROJECT_TEXT,
        re.DOTALL | re.MULTILINE,
    )
    if runtime_match:
        runtime_block = runtime_match.group(1)
        assert "pyyaml" not in runtime_block.lower(), (
            "pyyaml must NOT appear in runtime dependencies, only in dev optional-deps"
        )
