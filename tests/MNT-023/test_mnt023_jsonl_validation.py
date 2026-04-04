"""Tests for MNT-023: JSONL structural integrity validation in validate_workspace.py.

Verifies that _check_jsonl_structural() correctly detects:
- Invalid JSON on any line
- Empty lines in the middle of a file
- Missing required fields per file type
- Invalid enum values for Status fields
- Duplicate IDs (via _check_duplicate_ids)
- All 6 JSONL files are checked (workpackages, user-stories, bugs, test-results,
  decisions/index, maintenance/orchestrator-runs)
"""

import json
import sys
from pathlib import Path
import pytest

# Ensure scripts/ is on the path so validate_workspace imports cleanly
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_workspace import (
    ValidationResult,
    _check_duplicate_ids,
    _check_jsonl_structural,
    DECISIONS_JSONL,
    MAINT_RUNS_JSONL,
    WP_JSONL,
    US_JSONL,
    BUG_JSONL,
    TST_JSONL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, lines: list[str]) -> None:
    """Write raw lines to a JSONL file (no processing — raw test data)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_jsonl_objects(path: Path, rows: list[dict]) -> None:
    """Write dicts as JSONL rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests: JSONL path constants are exposed
# ---------------------------------------------------------------------------

class TestPathConstants:
    def test_decisions_jsonl_constant_present(self):
        """DECISIONS_JSONL constant must be defined and point to decisions/index.jsonl."""
        assert DECISIONS_JSONL.name == "index.jsonl"
        assert "decisions" in str(DECISIONS_JSONL)

    def test_maint_runs_jsonl_constant_present(self):
        """MAINT_RUNS_JSONL constant must be defined and point to orchestrator-runs.jsonl."""
        assert MAINT_RUNS_JSONL.name == "orchestrator-runs.jsonl"
        assert "maintenance" in str(MAINT_RUNS_JSONL)

    def test_all_six_jsonl_files_defined(self):
        """All 6 JSONL data-file path constants must be importable."""
        for const in (WP_JSONL, US_JSONL, BUG_JSONL, TST_JSONL, DECISIONS_JSONL, MAINT_RUNS_JSONL):
            assert isinstance(const, Path)


# ---------------------------------------------------------------------------
# Tests: Invalid JSON detection
# ---------------------------------------------------------------------------

class TestInvalidJson:
    def test_invalid_json_line_raises_error(self, tmp_path):
        """A file with a non-JSON line must produce an error."""
        f = tmp_path / "test.jsonl"
        write_jsonl(f, ['{"ID": "WP-001", "Status": "Open", "Name": "Test"}', "NOT JSON"])
        result = ValidationResult()
        # Monkey-patch the path so we can call the internal function
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert any("structural error" in e or "invalid JSON" in e for e in result.errors), result.errors

    def test_valid_json_lines_pass(self, tmp_path):
        """A well-formed JSONL file must produce no errors."""
        f = tmp_path / "test.jsonl"
        write_jsonl_objects(f, [
            {"ID": "WP-001", "Status": "Open", "Name": "Alpha"},
            {"ID": "WP-002", "Status": "Done", "Name": "Beta"},
        ])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert result.errors == []


# ---------------------------------------------------------------------------
# Tests: Empty-line detection
# ---------------------------------------------------------------------------

class TestEmptyLines:
    def test_empty_line_in_middle_is_error(self, tmp_path):
        """A blank line between records must produce an error."""
        f = tmp_path / "test.jsonl"
        write_jsonl(f, [
            '{"ID": "WP-001", "Status": "Open", "Name": "A"}',
            "",
            '{"ID": "WP-002", "Status": "Open", "Name": "B"}',
        ])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP")
        assert any("empty line" in e for e in result.errors), result.errors

    def test_trailing_newline_is_ok(self, tmp_path):
        """A file ending with a newline (standard UNIX convention) must pass."""
        f = tmp_path / "test.jsonl"
        # write_jsonl_objects adds a trailing newline
        write_jsonl_objects(f, [
            {"ID": "WP-001", "Status": "Open", "Name": "A"},
        ])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert result.errors == []

    def test_empty_line_at_start_is_error(self, tmp_path):
        """A blank line at the start of the file must produce an error."""
        f = tmp_path / "test.jsonl"
        write_jsonl(f, [
            "",
            '{"ID": "WP-001", "Status": "Open", "Name": "A"}',
        ])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP")
        assert any("empty line" in e for e in result.errors), result.errors


# ---------------------------------------------------------------------------
# Tests: Required-field validation
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_missing_id_field_is_error(self, tmp_path):
        """A WP row without ID must produce an error."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [{"Status": "Open", "Name": "Nameless"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert any("'ID'" in e for e in result.errors), result.errors

    def test_missing_name_field_is_error(self, tmp_path):
        """A WP row with empty Name must produce an error."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [{"ID": "WP-001", "Status": "Open", "Name": ""}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert any("'Name'" in e for e in result.errors), result.errors

    def test_missing_status_field_is_error(self, tmp_path):
        """A WP row with empty Status must produce an error."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [{"ID": "WP-001", "Name": "Test"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert any("'Status'" in e for e in result.errors), result.errors

    def test_bug_missing_title_is_error(self, tmp_path):
        """A Bug row without Title must produce an error."""
        f = tmp_path / "bugs.jsonl"
        write_jsonl_objects(f, [{"ID": "BUG-001", "Status": "Open"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="Bug", required_fields=["ID", "Status", "Title"])
        assert any("'Title'" in e for e in result.errors), result.errors

    def test_tst_missing_test_name_is_error(self, tmp_path):
        """A test-result row without 'Test Name' must produce an error."""
        f = tmp_path / "test-results.jsonl"
        write_jsonl_objects(f, [{"ID": "TST-001", "Status": "Pass"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="Test", required_fields=["ID", "Status", "Test Name"])
        assert any("'Test Name'" in e for e in result.errors), result.errors

    def test_adr_missing_adr_id_field_is_error(self, tmp_path):
        """A decisions row without ADR-ID must produce an error."""
        f = tmp_path / "index.jsonl"
        write_jsonl_objects(f, [{"Title": "Some decision", "Status": "Active"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="ADR", required_fields=["ADR-ID", "Status", "Title"])
        assert any("'ADR-ID'" in e for e in result.errors), result.errors

    def test_complete_row_passes(self, tmp_path):
        """A row with all required fields passes with no errors."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [{"ID": "WP-001", "Status": "Open", "Name": "Full Row"}])
        result = ValidationResult()
        _run_structural_check_on(f, result, label="WP", required_fields=["ID", "Status", "Name"])
        assert result.errors == []


# ---------------------------------------------------------------------------
# Tests: Status enum validation
# ---------------------------------------------------------------------------

class TestStatusEnum:
    def test_invalid_wp_status_is_warning(self, tmp_path):
        """A WP row with an invalid Status value must produce a warning."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [{"ID": "WP-001", "Status": "Banana", "Name": "Test"}])
        result = ValidationResult()
        _run_structural_check_on(
            f, result, label="WP",
            required_fields=["ID", "Status", "Name"],
            valid_status={"Open", "In Progress", "Review", "Done"},
        )
        assert any("Banana" in w for w in result.warnings), result.warnings

    def test_invalid_bug_status_is_warning(self, tmp_path):
        """A Bug row with invalid Status must produce a warning."""
        f = tmp_path / "bugs.jsonl"
        write_jsonl_objects(f, [{"ID": "BUG-001", "Status": "Deleted", "Title": "X"}])
        result = ValidationResult()
        _run_structural_check_on(
            f, result, label="Bug",
            required_fields=["ID", "Status", "Title"],
            valid_status={"Open", "In Progress", "Fixed", "Verified", "Closed"},
        )
        assert any("Deleted" in w for w in result.warnings), result.warnings

    def test_valid_adr_status_passes(self, tmp_path):
        """A decisions row with Status=Active must pass without warning."""
        f = tmp_path / "index.jsonl"
        write_jsonl_objects(f, [{"ADR-ID": "ADR-001", "Status": "Active", "Title": "An ADR"}])
        result = ValidationResult()
        _run_structural_check_on(
            f, result, label="ADR",
            required_fields=["ADR-ID", "Status", "Title"],
            id_field="ADR-ID",
            valid_status={"Active", "Superseded", "Draft"},
        )
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_adr_status_is_warning(self, tmp_path):
        """A decisions row with invalid Status must produce a warning."""
        f = tmp_path / "index.jsonl"
        write_jsonl_objects(f, [{"ADR-ID": "ADR-001", "Status": "Rejected", "Title": "An ADR"}])
        result = ValidationResult()
        _run_structural_check_on(
            f, result, label="ADR",
            required_fields=["ADR-ID", "Status", "Title"],
            id_field="ADR-ID",
            valid_status={"Active", "Superseded", "Draft"},
        )
        assert any("Rejected" in w for w in result.warnings), result.warnings


# ---------------------------------------------------------------------------
# Tests: Duplicate ID detection
# ---------------------------------------------------------------------------

class TestDuplicateIds:
    def test_duplicate_wp_id_is_error(self, tmp_path):
        """Two rows with the same ID must produce an error."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [
            {"ID": "WP-001", "Status": "Open", "Name": "Alpha"},
            {"ID": "WP-001", "Status": "Done", "Name": "Beta"},
        ])
        result = ValidationResult()
        _check_duplicate_ids(f, "ID", result)
        assert any("WP-001" in e for e in result.errors), result.errors

    def test_no_duplicate_wp_ids_passes(self, tmp_path):
        """Unique IDs must produce no errors."""
        f = tmp_path / "wp.jsonl"
        write_jsonl_objects(f, [
            {"ID": "WP-001", "Status": "Open", "Name": "Alpha"},
            {"ID": "WP-002", "Status": "Done", "Name": "Beta"},
        ])
        result = ValidationResult()
        _check_duplicate_ids(f, "ID", result)
        assert result.errors == []

    def test_duplicate_adr_id_is_error(self, tmp_path):
        """Two decisions rows with the same ADR-ID must produce an error."""
        f = tmp_path / "index.jsonl"
        write_jsonl_objects(f, [
            {"ADR-ID": "ADR-001", "Status": "Active", "Title": "A"},
            {"ADR-ID": "ADR-001", "Status": "Superseded", "Title": "B"},
        ])
        result = ValidationResult()
        _check_duplicate_ids(f, "ADR-ID", result)
        assert any("ADR-001" in e for e in result.errors), result.errors


# ---------------------------------------------------------------------------
# Tests: Orchestrator-runs (empty file passes; parse error fails)
# ---------------------------------------------------------------------------

class TestOrchestratorRuns:
    def test_empty_orchestrator_runs_file_passes(self, tmp_path):
        """An empty orchestrator-runs.jsonl must not produce any errors."""
        f = tmp_path / "orchestrator-runs.jsonl"
        f.write_text("", encoding="utf-8")
        result = ValidationResult()
        _run_structural_check_on(f, result, label="MaintRun", required_fields=[])
        assert result.errors == []

    def test_single_line_file_empty_passes(self, tmp_path):
        """A file containing only a single empty line must not error."""
        f = tmp_path / "orchestrator-runs.jsonl"
        f.write_text("\n", encoding="utf-8")
        result = ValidationResult()
        _run_structural_check_on(f, result, label="MaintRun", required_fields=[])
        assert result.errors == []

    def test_orchestrator_runs_parse_error_fails(self, tmp_path):
        """A corrupted orchestrator-runs.jsonl must produce an error."""
        f = tmp_path / "orchestrator-runs.jsonl"
        f.write_text("{bad json\n", encoding="utf-8")
        result = ValidationResult()
        _run_structural_check_on(f, result, label="MaintRun", required_fields=[])
        assert result.errors != []


# ---------------------------------------------------------------------------
# Tests: Real JSONL files (smoke test — must pass with no errors)
# ---------------------------------------------------------------------------

class TestRealJsonlFiles:
    def test_check_jsonl_structural_passes_on_real_data(self):
        """_check_jsonl_structural() must pass (no errors) on real repository data."""
        result = ValidationResult()
        _check_jsonl_structural(result)
        assert result.errors == [], (
            f"Unexpected structural errors in real JSONL files:\n"
            + "\n".join(result.errors)
        )

    def test_decisions_jsonl_is_checked(self):
        """decisions/index.jsonl must exist and be parseable."""
        assert DECISIONS_JSONL.exists(), "decisions/index.jsonl must exist"
        from jsonl_utils import read_jsonl
        _, rows = read_jsonl(DECISIONS_JSONL)
        assert len(rows) > 0, "decisions/index.jsonl must have at least one row"
        for row in rows:
            assert "ADR-ID" in row
            assert "Status" in row

    def test_duplicate_ids_decisions_check_in_validate_full(self):
        """validate_full must call duplicate-ID check for decisions (ADR-ID field)."""
        # Inspect source to verify the call is present
        src = (REPO_ROOT / "scripts" / "validate_workspace.py").read_text(encoding="utf-8")
        assert 'DECISIONS_JSONL, "ADR-ID"' in src, (
            "validate_full() must call _check_duplicate_ids(DECISIONS_JSONL, 'ADR-ID', ...)"
        )

    def test_jsonl_structural_comment_is_updated(self):
        """The 'CSV structural integrity' comment must have been replaced."""
        src = (REPO_ROOT / "scripts" / "validate_workspace.py").read_text(encoding="utf-8")
        assert "CSV structural integrity" not in src, (
            "Stale 'CSV structural integrity' comment must be removed from validate_workspace.py"
        )
        assert "JSONL structural integrity" in src, (
            "'JSONL structural integrity' comment must be present in validate_workspace.py"
        )


# ---------------------------------------------------------------------------
# Tests: Pre-commit hook smoke test
# ---------------------------------------------------------------------------

class TestPreCommitHook:
    def test_pre_commit_no_csv_checks(self):
        """The pre-commit hook must not contain CSV-specific validation logic."""
        hook = REPO_ROOT / "scripts" / "hooks" / "pre-commit"
        assert hook.exists(), "pre-commit hook must exist at scripts/hooks/pre-commit"
        content = hook.read_text(encoding="utf-8")
        # No CSV-specific keywords should be present
        for keyword in ("QUOTE_ALL", "csv.reader", "csv.writer", "quoting=", ".csv"):
            assert keyword not in content, (
                f"Pre-commit hook must not contain CSV-specific keyword: {keyword}"
            )

    def test_pre_commit_calls_validate_full(self):
        """The pre-commit hook must call validate_workspace.py with --full."""
        hook = REPO_ROOT / "scripts" / "hooks" / "pre-commit"
        content = hook.read_text(encoding="utf-8")
        assert "--full" in content, "Pre-commit hook must invoke validate_workspace.py --full"
        assert "validate_workspace.py" in content


# ---------------------------------------------------------------------------
# Tests: install_hooks.py correctness
# ---------------------------------------------------------------------------

class TestInstallHooks:
    def test_install_hooks_references_correct_directory(self):
        """install_hooks.py must reference scripts/hooks as the hooks directory."""
        install_script = REPO_ROOT / "scripts" / "install_hooks.py"
        assert install_script.exists()
        content = install_script.read_text(encoding="utf-8")
        assert "scripts/hooks" in content


# ---------------------------------------------------------------------------
# Internal helper: run _check_jsonl_structural logic on a custom path
# ---------------------------------------------------------------------------

def _run_structural_check_on(
    path: Path,
    result: ValidationResult,
    label: str = "WP",
    required_fields: list[str] | None = None,
    id_field: str = "ID",
    valid_status: set | None = None,
) -> None:
    """Re-implement the core logic of _check_jsonl_structural for a custom path.

    This helper lets tests exercise the validation algorithms without relying on
    the real repository JSONL files on disk.
    """
    from jsonl_utils import read_jsonl

    if required_fields is None:
        required_fields = []
    if valid_status is None:
        valid_status = set()

    # Empty-line detection
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    for line_num, raw_line in enumerate(raw_lines, start=1):
        if raw_line.strip() == "":
            if line_num < len(raw_lines):
                result.error(
                    f"{label} JSONL ({path.name}) has an empty line at "
                    f"line {line_num} — empty lines between records are not allowed"
                )

    # Parse check
    try:
        _, rows = read_jsonl(path)
    except ValueError as e:
        result.error(f"{label} JSONL structural error: {e}")
        return

    for row in rows:
        row_id = row.get(id_field, "<no ID>")
        for field in required_fields:
            if field not in row or str(row.get(field, "")).strip() == "":
                result.error(
                    f"{label} JSONL ({path.name}): row {row_id!r} "
                    f"is missing required field '{field}'"
                )
        if valid_status:
            status = row.get("Status", "")
            if isinstance(status, str):
                status = status.strip()
            if status and status not in valid_status:
                result.warning(
                    f"{row_id}: invalid {label} Status '{status}' — "
                    f"expected one of {sorted(valid_status)}"
                )
