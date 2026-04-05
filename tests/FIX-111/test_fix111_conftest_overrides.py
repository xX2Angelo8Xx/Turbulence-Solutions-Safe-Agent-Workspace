"""Tests for FIX-111: Verify FIX-092 conftest fixture overrides.

Confirms that tests/FIX-092/conftest.py exists and defines all three
autouse fixture overrides required to prevent global conftest interference.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

CONFTEST = Path(__file__).parent.parent / "FIX-092" / "conftest.py"
FIXTURE_NAMES = {
    "_prevent_vscode_launch",
    "_prevent_vscode_detection",
    "_subprocess_popen_sentinel",
}


def _parse_fixture_names(path: Path) -> set:
    """Return names of all @pytest.fixture-decorated functions in path."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            # Unwrap Call nodes: @pytest.fixture(autouse=True) -> func=Attribute
            inner = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(inner, ast.Attribute) and inner.attr == "fixture":
                names.add(node.name)
                break
            if isinstance(inner, ast.Name) and inner.id == "fixture":
                names.add(node.name)
                break
    return names


class TestConftestExists:
    def test_conftest_file_exists(self):
        assert CONFTEST.is_file(), f"Missing: {CONFTEST}"


class TestConftestDefinesFixtures:
    def test_conftest_defines_prevent_vscode_launch(self):
        names = _parse_fixture_names(CONFTEST)
        assert "_prevent_vscode_launch" in names

    def test_conftest_defines_prevent_vscode_detection(self):
        names = _parse_fixture_names(CONFTEST)
        assert "_prevent_vscode_detection" in names

    def test_conftest_defines_subprocess_popen_sentinel(self):
        names = _parse_fixture_names(CONFTEST)
        assert "_subprocess_popen_sentinel" in names

    def test_all_three_fixtures_present(self):
        names = _parse_fixture_names(CONFTEST)
        missing = FIXTURE_NAMES - names
        assert not missing, f"Missing fixtures: {missing}"


class TestFix092TestsPass:
    def test_fix092_tests_pass(self):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/FIX-092/", "-q", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        assert result.returncode == 0, (
            f"FIX-092 tests failed:\n{result.stdout}\n{result.stderr}"
        )
