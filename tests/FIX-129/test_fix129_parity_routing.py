"""Tests for FIX-129: parity verification and upgrader template routing.

Covers:
  - _detect_template() — all branches
  - _load_manifest() — agent-workbench and clean-workspace
  - .github/template file presence in both template directories
  - verify_create_project_parity() end-to-end
  - Upgrader _NEVER_TOUCH_PATTERNS includes .github/template
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_TEMPLATES_DIR = _REPO_ROOT / "templates"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from launcher.core.workspace_upgrader import (  # noqa: E402
    _NEVER_TOUCH_PATTERNS,
    _detect_template,
    _load_manifest,
)

import verify_parity as vp  # noqa: E402


# ---------------------------------------------------------------------------
# _detect_template() tests
# ---------------------------------------------------------------------------

class TestDetectTemplate:
    def test_agent_workbench(self, tmp_path: Path) -> None:
        """Returns 'agent-workbench' when .github/template contains that value."""
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "template").write_text("agent-workbench", encoding="utf-8")
        assert _detect_template(tmp_path) == "agent-workbench"

    def test_clean_workspace(self, tmp_path: Path) -> None:
        """Returns 'clean-workspace' when .github/template contains that value."""
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "template").write_text("clean-workspace", encoding="utf-8")
        assert _detect_template(tmp_path) == "clean-workspace"

    def test_missing_file_defaults_to_agent_workbench(self, tmp_path: Path) -> None:
        """Returns 'agent-workbench' when .github/template does not exist (legacy workspace)."""
        assert _detect_template(tmp_path) == "agent-workbench"

    def test_unknown_value_defaults_to_agent_workbench(self, tmp_path: Path) -> None:
        """Returns 'agent-workbench' when .github/template contains an unrecognised name."""
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "template").write_text("some-unknown-template", encoding="utf-8")
        assert _detect_template(tmp_path) == "agent-workbench"

    def test_whitespace_stripped(self, tmp_path: Path) -> None:
        """Leading/trailing whitespace in .github/template is stripped."""
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "template").write_text("  clean-workspace\n", encoding="utf-8")
        assert _detect_template(tmp_path) == "clean-workspace"


# ---------------------------------------------------------------------------
# _load_manifest() tests
# ---------------------------------------------------------------------------

class TestLoadManifest:
    def test_loads_agent_workbench_manifest(self) -> None:
        """Successfully loads the agent-workbench manifest."""
        manifest = _load_manifest("agent-workbench")
        assert manifest is not None
        assert manifest.get("template") == "agent-workbench"
        assert "files" in manifest

    def test_loads_clean_workspace_manifest(self) -> None:
        """Successfully loads the clean-workspace manifest."""
        manifest = _load_manifest("clean-workspace")
        assert manifest is not None
        assert manifest.get("template") == "clean-workspace"
        assert "files" in manifest

    def test_load_default_is_agent_workbench(self) -> None:
        """Default parameter loads agent-workbench manifest."""
        manifest = _load_manifest()
        assert manifest is not None
        assert manifest.get("template") == "agent-workbench"

    def test_nonexistent_template_returns_none(self) -> None:
        """Returns None for a template directory that does not exist."""
        result = _load_manifest("does-not-exist")
        assert result is None


# ---------------------------------------------------------------------------
# .github/template file in template directories
# ---------------------------------------------------------------------------

class TestTemplateFiles:
    def test_agent_workbench_template_file_exists(self) -> None:
        """templates/agent-workbench/.github/template exists."""
        template_file = _TEMPLATES_DIR / "agent-workbench" / ".github" / "template"
        assert template_file.exists(), (
            f".github/template not found in agent-workbench template at {template_file}"
        )

    def test_agent_workbench_template_file_content(self) -> None:
        """templates/agent-workbench/.github/template contains 'agent-workbench'."""
        template_file = _TEMPLATES_DIR / "agent-workbench" / ".github" / "template"
        content = template_file.read_text(encoding="utf-8").strip()
        assert content == "agent-workbench"

    def test_clean_workspace_template_file_exists(self) -> None:
        """templates/clean-workspace/.github/template exists."""
        template_file = _TEMPLATES_DIR / "clean-workspace" / ".github" / "template"
        assert template_file.exists(), (
            f".github/template not found in clean-workspace template at {template_file}"
        )

    def test_clean_workspace_template_file_content(self) -> None:
        """templates/clean-workspace/.github/template contains 'clean-workspace'."""
        template_file = _TEMPLATES_DIR / "clean-workspace" / ".github" / "template"
        content = template_file.read_text(encoding="utf-8").strip()
        assert content == "clean-workspace"


# ---------------------------------------------------------------------------
# _NEVER_TOUCH_PATTERNS protects .github/template
# ---------------------------------------------------------------------------

class TestNeverTouchPatterns:
    def test_github_template_in_never_touch(self) -> None:
        """.github/template is in _NEVER_TOUCH_PATTERNS so the upgrader won't overwrite it."""
        assert ".github/template" in _NEVER_TOUCH_PATTERNS, (
            ".github/template must be in _NEVER_TOUCH_PATTERNS to prevent the upgrader "
            "from overwriting the routing file"
        )


# ---------------------------------------------------------------------------
# verify_create_project_parity() end-to-end
# ---------------------------------------------------------------------------

class TestVerifyCreateProjectParity:
    def test_parity_passes(self) -> None:
        """verify_create_project_parity() returns True with a clean template."""
        result = vp.verify_create_project_parity(verbose=False)
        assert result is True, (
            "create_project parity check failed — unexpected divergence detected"
        )

    def test_parity_verbose_does_not_raise(self) -> None:
        """verify_create_project_parity(verbose=True) runs without exceptions."""
        # Should not raise regardless of output.
        vp.verify_create_project_parity(verbose=True)


# ---------------------------------------------------------------------------
# _NEVER_SECURITY_CRITICAL in generate_manifest excludes .github/template
# ---------------------------------------------------------------------------

class TestManifestNeverSecurityCritical:
    def test_github_template_not_security_critical_in_agent_workbench(self) -> None:
        """MANIFEST.json for agent-workbench does not mark .github/template as security_critical."""
        manifest = _load_manifest("agent-workbench")
        assert manifest is not None
        files = manifest.get("files", {})
        entry = files.get(".github/template")
        assert entry is not None, ".github/template must be tracked in agent-workbench MANIFEST.json"
        assert not entry.get("security_critical", False), (
            ".github/template must NOT be security_critical in agent-workbench manifest"
        )

    def test_github_template_not_security_critical_in_clean_workspace(self) -> None:
        """MANIFEST.json for clean-workspace does not mark .github/template as security_critical."""
        manifest = _load_manifest("clean-workspace")
        assert manifest is not None
        files = manifest.get("files", {})
        entry = files.get(".github/template")
        assert entry is not None, ".github/template must be tracked in clean-workspace MANIFEST.json"
        assert not entry.get("security_critical", False), (
            ".github/template must NOT be security_critical in clean-workspace manifest"
        )
