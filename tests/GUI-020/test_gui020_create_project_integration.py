"""Tests for GUI-020 — create_project() integration with counter config.

Covers:
  1. create_project() writes counter_config.json into created workspace
  2. Default counter params produce correct config (enabled=True, threshold=20)
  3. Custom counter_enabled=False is persisted in created workspace
  4. Custom counter_threshold=5 is persisted in created workspace
  5. Counter config overrides the template's default counter_config.json
  6. create_project() still copies all template files (counter config is additive)
  7. counter_enabled and counter_threshold are keyword-only with correct defaults
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from launcher.core.project_creator import (
    _COUNTER_CONFIG_PATH,
    create_project,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEMPLATE_DIR_STRUCTURE = [
    ".github/hooks/scripts/security_gate.py",
    ".github/hooks/scripts/counter_config.json",
    "Project/README.md",
]

TEMPLATE_COUNTER_CONFIG = {"counter_enabled": True, "lockout_threshold": 20}


def _make_template(tmp_root: Path) -> Path:
    """Create a minimal fake template directory mirroring the real structure."""
    tpl = tmp_root / "template"
    tpl.mkdir()
    for rel in TEMPLATE_DIR_STRUCTURE:
        fpath = tpl / rel
        fpath.parent.mkdir(parents=True, exist_ok=True)
        if fpath.name == "counter_config.json":
            fpath.write_text(json.dumps(TEMPLATE_COUNTER_CONFIG), encoding="utf-8")
        else:
            fpath.write_text("# placeholder", encoding="utf-8")
    return tpl


def _read_counter_config(workspace: Path) -> dict:
    config_path = workspace / _COUNTER_CONFIG_PATH
    return json.loads(config_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helper to call create_project without triggering replace_template_placeholders
# errors on non-md files (they are silently skipped).
# ---------------------------------------------------------------------------

def _create(template: Path, dest: Path, name: str, **kwargs) -> Path:
    return create_project(template, dest, name, **kwargs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateProjectWritesCounterConfig:
    def test_counter_config_file_exists_after_creation(self) -> None:
        """create_project must produce a counter_config.json in the workspace."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject")
            config_path = workspace / _COUNTER_CONFIG_PATH
            assert config_path.is_file(), f"counter_config.json not found at {config_path}"

    def test_default_enabled_true_written(self) -> None:
        """Default counter_enabled=True must be written when no override supplied."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject")
            data = _read_counter_config(workspace)
        assert data["counter_enabled"] is True

    def test_default_threshold_20_written(self) -> None:
        """Default counter_threshold=20 must be written when no override supplied."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject")
            data = _read_counter_config(workspace)
        assert data["lockout_threshold"] == 20

    def test_custom_enabled_false_persisted(self) -> None:
        """counter_enabled=False must be persisted in the created workspace."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject", counter_enabled=False)
            data = _read_counter_config(workspace)
        assert data["counter_enabled"] is False

    def test_custom_threshold_persisted(self) -> None:
        """A custom counter_threshold must override the template default."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject", counter_threshold=7)
            data = _read_counter_config(workspace)
        assert data["lockout_threshold"] == 7

    def test_disabled_and_custom_threshold_together(self) -> None:
        """An explicit disabled counter with a custom threshold must both be persisted."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(
                tpl, dest, "MyProject", counter_enabled=False, counter_threshold=3
            )
            data = _read_counter_config(workspace)
        assert data["counter_enabled"] is False
        assert data["lockout_threshold"] == 3

    def test_gui_values_override_template_defaults(self) -> None:
        """GUI values must overwrite the template's counter_config.json (not merge)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            # Template ships with enabled=True, threshold=20.
            # GUI passes enabled=False, threshold=50.
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(
                tpl, dest, "MyProject", counter_enabled=False, counter_threshold=50
            )
            data = _read_counter_config(workspace)
        assert data["counter_enabled"] is False
        assert data["lockout_threshold"] == 50

    def test_template_files_still_copied(self) -> None:
        """Counter config must be additive — all other template files must still exist."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "MyProject")
            # security_gate.py from template should still be present
            assert (workspace / ".github" / "hooks" / "scripts" / "security_gate.py").is_file()

    def test_workspace_folder_prefixed_with_ts_sae(self) -> None:
        """create_project must prefix the folder name with 'TS-SAE-'."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = _create(tpl, dest, "TestProj")
        assert workspace.name == "TS-SAE-TestProj"
