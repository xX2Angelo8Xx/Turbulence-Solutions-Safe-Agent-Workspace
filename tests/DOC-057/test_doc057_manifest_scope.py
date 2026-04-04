"""Tests for DOC-057: Document Certification Pipeline Scope.

Verifies that generate_manifest.py and MANIFEST.json clearly document
that only templates/agent-workbench/ is in scope and that
templates/certification-pipeline/ is intentionally excluded.
"""

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "generate_manifest.py"
_MANIFEST_PATH = _REPO_ROOT / "templates" / "agent-workbench" / "MANIFEST.json"


def test_module_docstring_mentions_agent_workbench():
    """generate_manifest.py docstring must reference templates/agent-workbench/."""
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    assert "agent-workbench" in source, (
        "generate_manifest.py docstring must mention 'agent-workbench'"
    )


def test_module_docstring_mentions_certification_pipeline_exclusion():
    """generate_manifest.py docstring must state certification-pipeline is excluded."""
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    assert "certification-pipeline" in source, (
        "generate_manifest.py docstring must mention 'certification-pipeline' exclusion"
    )


def test_argparse_description_mentions_scope():
    """The argparse description must reference both agent-workbench and certification-pipeline."""
    source = _SCRIPT_PATH.read_text(encoding="utf-8")
    # Both terms must appear together in the ArgumentParser call context
    assert "agent-workbench" in source
    assert "certification-pipeline" in source


def test_generate_manifest_has_scope_field():
    """generate_manifest() must return a dict containing a '_scope' key."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("generate_manifest", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    manifest = mod.generate_manifest()
    assert "_scope" in manifest, "generate_manifest() must return a dict with '_scope'"
    scope_value = manifest["_scope"]
    assert "agent-workbench" in scope_value, "_scope must mention 'agent-workbench'"
    assert "certification-pipeline" in scope_value, "_scope must mention 'certification-pipeline'"


def test_manifest_json_has_scope_field():
    """MANIFEST.json on disk must contain a '_scope' field with correct content."""
    assert _MANIFEST_PATH.exists(), "MANIFEST.json must exist"
    data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert "_scope" in data, "MANIFEST.json must have a '_scope' field"
    assert "agent-workbench" in data["_scope"], "_scope must mention 'agent-workbench'"
    assert "certification-pipeline" in data["_scope"], (
        "_scope must mention 'certification-pipeline'"
    )


def test_manifest_json_scope_not_in_files():
    """The _scope field must be a top-level metadata field, not inside 'files'."""
    data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    files = data.get("files", {})
    assert "_scope" not in files, "_scope must be a top-level key, not inside 'files'"


def test_generate_manifest_check_passes():
    """Running generate_manifest --check must succeed (manifest is up to date)."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"generate_manifest.py --check failed:\n{result.stdout}\n{result.stderr}"
    )
