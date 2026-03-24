"""GUI-020 tester edge-case tests.

Additional tests covering boundary conditions, JSON type correctness,
directory creation when the template lacks .github/hooks/scripts/,
and app-level threshold validation behaviour.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from launcher.core.project_creator import (
    _COUNTER_CONFIG_PATH,
    _DEFAULT_COUNTER_THRESHOLD,
    create_project,
    write_counter_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_and_read(tmp_dir: Path, enabled: bool, threshold: int) -> dict:
    """Ensure parent exists, call write_counter_config, return parsed JSON."""
    config_path = tmp_dir / _COUNTER_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_counter_config(tmp_dir, enabled, threshold)
    return json.loads(config_path.read_text(encoding="utf-8"))


def _make_template_no_hooks(tmp_root: Path) -> Path:
    """Create a minimal template that does NOT contain .github/hooks/scripts/."""
    tpl = tmp_root / "template_no_hooks"
    tpl.mkdir()
    # Only the bare minimum — no .github directory at all.
    (tpl / "Project").mkdir()
    (tpl / "Project" / "README.md").write_text("# {{PROJECT_NAME}}", encoding="utf-8")
    return tpl


def _make_template_with_hooks(tmp_root: Path) -> Path:
    """Create a minimal template with .github/hooks/scripts/ but no counter_config."""
    tpl = tmp_root / "template_with_hooks"
    tpl.mkdir()
    hooks_dir = tpl / ".github" / "hooks" / "scripts"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "security_gate.py").write_text("# stub", encoding="utf-8")
    (tpl / "Project").mkdir()
    (tpl / "Project" / "README.md").write_text("# {{PROJECT_NAME}}", encoding="utf-8")
    return tpl


# ---------------------------------------------------------------------------
# Boundary threshold values
# ---------------------------------------------------------------------------

class TestBoundaryThresholds:
    def test_threshold_1_is_minimum_valid_boundary(self) -> None:
        """Threshold of 1 (lowest positive value) must be written as integer 1."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 1)
        assert data["lockout_threshold"] == 1

    def test_threshold_large_value_written_correctly(self) -> None:
        """Very large threshold (999999) must be written and read back intact."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 999999)
        assert data["lockout_threshold"] == 999999

    def test_disabled_with_threshold_1(self) -> None:
        """counter_enabled=False with threshold=1 must both be persisted."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), False, 1)
        assert data["counter_enabled"] is False
        assert data["lockout_threshold"] == 1

    def test_threshold_default_constant_is_20(self) -> None:
        """_DEFAULT_COUNTER_THRESHOLD must be 20 — tests rely on this constant."""
        assert _DEFAULT_COUNTER_THRESHOLD == 20


# ---------------------------------------------------------------------------
# JSON type correctness (not just value equality)
# ---------------------------------------------------------------------------

class TestJsonTypeCorrectness:
    def test_counter_enabled_true_is_json_boolean_not_string(self) -> None:
        """counter_enabled must be a Python bool (JSON boolean), not a string."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert isinstance(data["counter_enabled"], bool), (
            f"counter_enabled should be bool, got {type(data['counter_enabled'])}"
        )

    def test_counter_enabled_false_is_json_boolean_not_string(self) -> None:
        """counter_enabled=False must decode as Python False (JSON false), not string."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), False, 20)
        assert isinstance(data["counter_enabled"], bool)
        assert data["counter_enabled"] is False

    def test_lockout_threshold_is_json_integer_not_string(self) -> None:
        """lockout_threshold must decode as Python int, not a string."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _write_and_read(Path(tmp), True, 20)
        assert isinstance(data["lockout_threshold"], int), (
            f"lockout_threshold should be int, got {type(data['lockout_threshold'])}"
        )

    def test_written_file_is_parseable_without_bom(self) -> None:
        """Written JSON must not have a UTF-8 BOM — must parse cleanly as UTF-8."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_counter_config(tmp_dir, True, 20)
            raw_bytes = config_path.read_bytes()
        # UTF-8 BOM is EF BB BF
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), "File must not begin with UTF-8 BOM"
        # Must be parseable as plain UTF-8 JSON
        json.loads(raw_bytes.decode("utf-8"))


# ---------------------------------------------------------------------------
# Template without .github/hooks/scripts/ — directory auto-creation
# ---------------------------------------------------------------------------

class TestTemplateWithoutHooksDir:
    def test_write_counter_config_creates_missing_parent_dirs(self) -> None:
        """write_counter_config must create .github/hooks/scripts/ when it is absent."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            # Do NOT pre-create the parent directory — simulate a template without hooks.
            config_path = tmp_dir / _COUNTER_CONFIG_PATH
            assert not config_path.parent.exists(), "Pre-condition: parent must not exist"
            write_counter_config(tmp_dir, True, 20)
            assert config_path.is_file(), "Config file must be created even with missing parent"

    def test_create_project_writes_config_when_template_has_no_hooks_dir(self) -> None:
        """create_project must write counter_config.json even when template has no .github dir."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template_no_hooks(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = create_project(tpl, dest, "NoHooksProj", counter_enabled=True, counter_threshold=15)
            config_path = workspace / _COUNTER_CONFIG_PATH
            assert config_path.is_file(), (
                "counter_config.json must exist even when template had no .github/hooks/scripts/"
            )
            data = json.loads(config_path.read_text(encoding="utf-8"))
            assert data["lockout_threshold"] == 15
            assert data["counter_enabled"] is True

    def test_create_project_disabled_counter_template_without_hooks(self) -> None:
        """Disabled counter config is correctly written when template lacks hooks dir."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template_no_hooks(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = create_project(tpl, dest, "DisabledProj", counter_enabled=False, counter_threshold=5)
            data = json.loads((workspace / _COUNTER_CONFIG_PATH).read_text(encoding="utf-8"))
        assert data["counter_enabled"] is False
        assert data["lockout_threshold"] == 5

    def test_create_project_counter_config_with_hooks_dir_but_no_existing_config(self) -> None:
        """If template has hooks dir but no counter_config.json, config must be created fresh."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tpl = _make_template_with_hooks(tmp_dir)
            dest = tmp_dir / "dest"
            dest.mkdir()
            workspace = create_project(tpl, dest, "FreshConfig", counter_threshold=42)
            data = json.loads((workspace / _COUNTER_CONFIG_PATH).read_text(encoding="utf-8"))
        assert data["lockout_threshold"] == 42


# ---------------------------------------------------------------------------
# App-level threshold validation (get_counter_threshold edge cases)
# ---------------------------------------------------------------------------

class TestAppThresholdValidation:
    def _make_app(self):
        from launcher.gui.app import App
        sys.modules["customtkinter"].reset_mock()
        return App()

    def test_get_counter_threshold_raises_for_zero(self) -> None:
        """get_counter_threshold must raise ValueError for threshold=0."""
        app = self._make_app()
        app.counter_threshold_var.get.return_value = "0"
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_get_counter_threshold_raises_for_negative(self) -> None:
        """get_counter_threshold must raise ValueError for negative threshold."""
        app = self._make_app()
        app.counter_threshold_var.get.return_value = "-5"
        with pytest.raises(ValueError):
            app.get_counter_threshold()

    def test_get_counter_threshold_returns_int_for_valid_value(self) -> None:
        """get_counter_threshold must return an int for a valid positive string."""
        app = self._make_app()
        app.counter_threshold_var.get.return_value = "25"
        result = app.get_counter_threshold()
        assert result == 25
        assert isinstance(result, int)

    def test_on_create_project_zero_threshold_falls_back_to_20(self) -> None:
        """When get_counter_threshold raises (threshold=0), create_project gets fallback 20."""
        app = self._make_app()
        app.project_name_entry.get.return_value = "TestProject"
        app.project_type_dropdown.get.return_value = "Coding"
        app.destination_entry.get.return_value = "/some/dest"
        app.project_name_error_label.configure = MagicMock()
        app.destination_error_label.configure = MagicMock()
        app.counter_enabled_var.get.return_value = True
        # threshold_var returns "0" and get_counter_threshold raises for it
        app.counter_threshold_var.get.return_value = "0"

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_threshold") == 20, (
            f"Expected fallback 20 for invalid threshold=0, got {kwargs.get('counter_threshold')}"
        )

    def test_on_create_project_negative_threshold_falls_back_to_20(self) -> None:
        """When get_counter_threshold raises (threshold negative), fallback 20 is used."""
        app = self._make_app()
        app.project_name_entry.get.return_value = "TestProject"
        app.project_type_dropdown.get.return_value = "Coding"
        app.destination_entry.get.return_value = "/some/dest"
        app.project_name_error_label.configure = MagicMock()
        app.destination_error_label.configure = MagicMock()
        app.counter_enabled_var.get.return_value = True
        app.counter_threshold_var.get.return_value = "-10"

        with patch("launcher.gui.app.validate_folder_name", return_value=(True, "")), \
             patch("launcher.gui.app.validate_destination_path", return_value=(True, "")), \
             patch("launcher.gui.app.check_duplicate_folder", return_value=False), \
             patch("launcher.gui.app.list_templates", return_value=["coding"]), \
             patch("launcher.gui.app.verify_ts_python", return_value=(True, "ok")), \
             patch("launcher.gui.app.create_project", return_value=Path("/fake/path")) as mock_create:
            app._on_create_project()

        assert mock_create.called
        _, kwargs = mock_create.call_args
        assert kwargs.get("counter_threshold") == 20
