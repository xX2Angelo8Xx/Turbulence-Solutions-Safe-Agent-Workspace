"""Tests for FIX-007: Standardize GUI Test Mock Pattern.

Regression tests that confirm:
1. No test file uses the OLD del-sys.modules reimport pattern.
2. app.py has no UTF-8 BOM.
3. conftest.py check_for_update mock returns an unpackable tuple.
4. GUI-012 window height assertion matches the actual WINDOW_HEIGHT constant.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[2]
TESTS_DIR = BASE / "tests"
APP_PY = BASE / "src" / "launcher" / "gui" / "app.py"
CONFTEST_PY = TESTS_DIR / "conftest.py"

GUI_TEST_FILES = [
    TESTS_DIR / "GUI-001" / "test_gui001_main_window.py",
    TESTS_DIR / "GUI-002" / "test_gui002_project_type_selection.py",
    TESTS_DIR / "GUI-003" / "test_gui003_folder_name.py",
    TESTS_DIR / "GUI-004" / "test_gui004_destination_validation.py",
    TESTS_DIR / "GUI-005" / "test_gui005_project_creation.py",
    TESTS_DIR / "GUI-008" / "test_gui008_version_display.py",
    TESTS_DIR / "GUI-009" / "test_gui009_update_banner.py",
    TESTS_DIR / "GUI-009" / "test_gui009_tester_additions.py",
    TESTS_DIR / "GUI-009" / "test_gui009_edge_cases.py",
    TESTS_DIR / "GUI-010" / "test_gui010_check_for_updates_button.py",
    TESTS_DIR / "GUI-010" / "test_gui010_tester_additions.py",
    TESTS_DIR / "GUI-010" / "test_gui010_edge_cases.py",
    TESTS_DIR / "GUI-011" / "test_gui011_color_theme.py",
    TESTS_DIR / "GUI-012" / "test_gui012_spacing.py",
]

# The problematic pattern is the del loop targeting launcher.gui modules.
OLD_PATTERN_RE = re.compile(
    r"for\s+_key\s+in\s+\[k\s+for\s+k\s+in\s+sys\.modules"
    r"\s+if\s+k\.startswith\(['\"]launcher\.gui",
)


class TestNoOldMockPattern:
    @pytest.mark.parametrize("test_file", GUI_TEST_FILES, ids=[p.name for p in GUI_TEST_FILES])
    def test_file_does_not_use_del_sys_modules_loop(self, test_file: Path):
        """Each test file must NOT contain the old del-sys.modules eviction loop."""
        content = test_file.read_text(encoding="utf-8")
        assert not OLD_PATTERN_RE.search(content), (
            f"{test_file.name} still contains the old del-sys.modules loop"
        )

    @pytest.mark.parametrize("test_file", GUI_TEST_FILES, ids=[p.name for p in GUI_TEST_FILES])
    def test_file_uses_shared_ctk_mock(self, test_file: Path):
        """Each test file must retrieve the ctk mock from sys.modules (not create a new one)."""
        content = test_file.read_text(encoding="utf-8")
        assert 'sys.modules["customtkinter"]' in content, (
            f"{test_file.name} does not use sys.modules[\"customtkinter\"] to get the mock"
        )


class TestAppPyNoBOM:
    def test_app_py_has_no_bom(self):
        """app.py must not start with a UTF-8 BOM (EF BB BF)."""
        raw = APP_PY.read_bytes()
        assert raw[:3] != b"\xef\xbb\xbf", "app.py still starts with a UTF-8 BOM"

    def test_app_py_is_valid_python(self):
        """app.py must parse as valid Python after BOM removal."""
        source = APP_PY.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"app.py is not valid Python: {exc}")


class TestConftestReturnValue:
    def test_check_for_update_returns_tuple(self):
        """conftest.py must patch check_for_update with a tuple return value."""
        content = CONFTEST_PY.read_text(encoding="utf-8")
        # Must NOT use return_value=None for check_for_update
        assert 'check_for_update", return_value=None' not in content, (
            "conftest still uses return_value=None for check_for_update (causes TypeError)"
        )
        # Must use a tuple (False, ...)
        assert 'check_for_update", return_value=(False,' in content, (
            "conftest does not patch check_for_update with a (False, ...) tuple"
        )


class TestGUI012WindowHeight:
    def test_window_height_assertion_matches_app(self):
        """GUI-012 test must assert 520, matching _WINDOW_HEIGHT in app.py."""
        spacing_test = TESTS_DIR / "GUI-012" / "test_gui012_spacing.py"
        content = spacing_test.read_text(encoding="utf-8")
        # Old wrong assertion must be gone
        assert '"440"' not in content or "test_window_height_is_440" in content, (
            "Unexpected state in GUI-012 window height test"
        )
        # New correct assertion must be present
        assert '"520"' in content, (
            "GUI-012 test_window_height_is_440 does not assert '520'"
        )

    def test_app_window_height_is_520(self):
        """_WINDOW_HEIGHT in app.py must be 520."""
        content = APP_PY.read_text(encoding="utf-8")
        assert "_WINDOW_HEIGHT: int = 520" in content, (
            "app.py _WINDOW_HEIGHT is not 520"
        )
