"""
FIX-130 regression tests — Fix 16 CI test failures for v3.4.0

Verifies the four root causes were correctly resolved:
1. GUI-007 mock pollution: app._window.after uses .side_effect not direct assignment
2. GUI-018 geometry assertion: updated to 480x720
3. Clean-workspace .gitattributes: line-ending rules added
4. Regression baseline: FIX-125 CI environment entry added
"""
import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Fix 1: GUI-007 mock pollution
# ---------------------------------------------------------------------------

class TestGui007MockPollution:
    def _assert_side_effect(self, path: Path) -> None:
        source = path.read_text(encoding="utf-8")
        assert "app._window.after = lambda" not in source, (
            f"{path.name} still uses direct lambda assignment "
            "— must use .side_effect"
        )
        assert "app._window.after.side_effect = lambda" in source, (
            f"{path.name} does not use .side_effect for after callback"
        )

    def test_edge_cases_uses_side_effect(self) -> None:
        self._assert_side_effect(
            REPO_ROOT / "tests" / "GUI-007" / "test_gui007_edge_cases.py"
        )

    def test_tester_additions_uses_side_effect(self) -> None:
        self._assert_side_effect(
            REPO_ROOT / "tests" / "GUI-007" / "test_gui007_tester_additions.py"
        )

    def test_validation_uses_side_effect(self) -> None:
        self._assert_side_effect(
            REPO_ROOT / "tests" / "GUI-007" / "test_gui007_validation.py"
        )


# ---------------------------------------------------------------------------
# Fix 2: GUI-018 geometry assertion updated to 480x720
# ---------------------------------------------------------------------------

class TestGui018GeometryAssertion:
    def test_geometry_asserts_480x720(self) -> None:
        path = REPO_ROOT / "tests" / "GUI-018" / "test_gui018_edge_cases.py"
        source = path.read_text(encoding="utf-8")
        assert "assert_called_with(\"480x620\")" not in source, (
            "GUI-018 still asserts 480x620 — must assert 480x720"
        )
        assert "assert_called_with(\"480x720\")" in source, (
            "GUI-018 does not assert the correct 480x720 geometry"
        )

    def test_method_name_updated(self) -> None:
        path = REPO_ROOT / "tests" / "GUI-018" / "test_gui018_edge_cases.py"
        source = path.read_text(encoding="utf-8")
        assert "def test_dialog_geometry_is_480x620" not in source, (
            "GUI-018 method name still says 480x620"
        )
        assert "def test_dialog_geometry_is_480x720" in source, (
            "GUI-018 method name must be test_dialog_geometry_is_480x720"
        )


# ---------------------------------------------------------------------------
# Fix 3: .gitattributes has clean-workspace line-ending rules
# ---------------------------------------------------------------------------

class TestGitattributesCleanWorkspace:
    def test_clean_workspace_py_rule_present(self) -> None:
        path = REPO_ROOT / ".gitattributes"
        source = path.read_text(encoding="utf-8")
        assert "templates/clean-workspace/.github/hooks/scripts/*.py text eol=lf" in source

    def test_clean_workspace_json_rule_present(self) -> None:
        path = REPO_ROOT / ".gitattributes"
        source = path.read_text(encoding="utf-8")
        assert "templates/clean-workspace/.github/hooks/scripts/*.json text eol=lf" in source

    def test_clean_workspace_md_rule_present(self) -> None:
        path = REPO_ROOT / ".gitattributes"
        source = path.read_text(encoding="utf-8")
        assert "templates/clean-workspace/*.md text eol=lf" in source


# ---------------------------------------------------------------------------
# Fix 4: Regression baseline contains FIX-125 CI entry
# ---------------------------------------------------------------------------

class TestRegressionBaseline:
    def test_fix125_ci_entry_present(self) -> None:
        path = REPO_ROOT / "tests" / "regression-baseline.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        key = (
            "tests.FIX-125.test_fix125_build_fixes."
            "TestFindIsccLocalAppData."
            "test_find_iscc_localappdata_path_wins_over_absent_system_paths"
        )
        assert key in data["known_failures"], (
            f"FIX-125 CI environment failure not found in regression baseline"
        )

    def test_count_matches_entries(self) -> None:
        path = REPO_ROOT / "tests" / "regression-baseline.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["_count"] == len(data["known_failures"]), (
            f"_count={data['_count']} does not match "
            f"actual entries={len(data['known_failures'])}"
        )
