"""Tests for MNT-017: Migrate all data scripts to JSONL.

Verifies that all 10 updated scripts use jsonl_utils instead of csv_utils,
reference .jsonl paths, and operate correctly with temporary JSONL files.
Real data files (.jsonl) are not yet available until MNT-018 runs the
conversion; these tests use mock JSONL data in temp directories.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import add_bug
import add_test_result
import add_workpackage
import archive_test_results
import dedup_test_ids
import finalize_wp
import run_tests
import update_architecture
import update_bug_status
import validate_workspace
from jsonl_utils import REPO_ROOT as UTIL_REPO_ROOT
from jsonl_utils import read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write rows to a JSONL file for test setup."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    write_jsonl(path, fieldnames, rows)


# ---------------------------------------------------------------------------
# 1. Import sanity — no csv_utils imports remain
# ---------------------------------------------------------------------------


def _module_source(mod) -> str:
    """Return the source code of a module loaded from a file."""
    return Path(mod.__file__).read_text(encoding="utf-8")


@pytest.mark.parametrize("mod", [
    add_workpackage, add_bug, add_test_result, run_tests,
    finalize_wp, validate_workspace, dedup_test_ids,
    archive_test_results, update_bug_status, update_architecture,
])
def test_no_csv_utils_import(mod):
    """Each migrated script must not import csv_utils."""
    src = _module_source(mod)
    assert "csv_utils" not in src, (
        f"{mod.__name__} still imports csv_utils"
    )


def test_add_wps_batch_no_csv_utils():
    """_add_wps_batch.py must not import csv_utils."""
    src = (REPO_ROOT / "scripts" / "_add_wps_batch.py").read_text(encoding="utf-8")
    assert "csv_utils" not in src


# ---------------------------------------------------------------------------
# 2. Path constants use .jsonl
# ---------------------------------------------------------------------------


def test_add_workpackage_paths():
    assert str(add_workpackage.WP_JSONL).endswith("workpackages.jsonl")
    assert str(add_workpackage.US_JSONL).endswith("user-stories.jsonl")


def test_add_bug_path():
    assert str(add_bug.JSONL_PATH).endswith("bugs.jsonl")


def test_add_test_result_path():
    assert str(add_test_result.JSONL_PATH).endswith("test-results.jsonl")


def test_run_tests_path():
    assert str(run_tests.TST_JSONL).endswith("test-results.jsonl")


def test_finalize_wp_paths():
    assert str(finalize_wp.WP_JSONL).endswith("workpackages.jsonl")
    assert str(finalize_wp.US_JSONL).endswith("user-stories.jsonl")
    assert str(finalize_wp.BUG_JSONL).endswith("bugs.jsonl")


def test_validate_workspace_paths():
    assert str(validate_workspace.WP_JSONL).endswith("workpackages.jsonl")
    assert str(validate_workspace.US_JSONL).endswith("user-stories.jsonl")
    assert str(validate_workspace.BUG_JSONL).endswith("bugs.jsonl")
    assert str(validate_workspace.TST_JSONL).endswith("test-results.jsonl")


def test_dedup_test_ids_path():
    assert str(dedup_test_ids.TST_JSONL).endswith("test-results.jsonl")


def test_archive_test_results_paths():
    assert str(archive_test_results.TST_JSONL).endswith("test-results.jsonl")
    assert str(archive_test_results.ARCHIVE_JSONL).endswith("archived-test-results.jsonl")
    assert str(archive_test_results.WP_JSONL).endswith("workpackages.jsonl")


def test_update_bug_status_path():
    assert str(update_bug_status.JSONL_PATH).endswith("bugs.jsonl")


def test_add_wps_batch_paths():
    src = (REPO_ROOT / "scripts" / "_add_wps_batch.py").read_text(encoding="utf-8")
    assert "workpackages.jsonl" in src
    assert "user-stories.jsonl" in src


# ---------------------------------------------------------------------------
# 3. Retired scripts have been deleted
# ---------------------------------------------------------------------------


def test_repair_csvs_deleted():
    assert not (REPO_ROOT / "scripts" / "_repair_csvs.py").exists(), (
        "_repair_csvs.py should have been deleted"
    )


def test_verify_deleted():
    assert not (REPO_ROOT / "scripts" / "_verify.py").exists(), (
        "_verify.py should have been deleted"
    )


# ---------------------------------------------------------------------------
# 4. Functional: _check_jsonl_structural exists and replaces _check_csv_structural
# ---------------------------------------------------------------------------


def test_check_jsonl_structural_exists():
    assert hasattr(validate_workspace, "_check_jsonl_structural")


def test_check_csv_structural_removed():
    assert not hasattr(validate_workspace, "_check_csv_structural")


def test_check_jsonl_structural_passes_valid_data(tmp_path):
    """_check_jsonl_structural should report no errors for valid JSONL files."""
    # Patch path constants temporarily
    original_wp = validate_workspace.WP_JSONL
    original_bug = validate_workspace.BUG_JSONL
    original_tst = validate_workspace.TST_JSONL
    original_us = validate_workspace.US_JSONL

    wp_file = tmp_path / "workpackages.jsonl"
    bug_file = tmp_path / "bugs.jsonl"
    tst_file = tmp_path / "test-results.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "Done", "Name": "T"}])
    _write_jsonl(bug_file, [{"ID": "BUG-001", "Status": "Open", "Title": "T"}])
    _write_jsonl(tst_file, [{"ID": "TST-1", "Status": "Pass", "Test Name": "T"}])
    _write_jsonl(us_file, [{"ID": "US-001", "Status": "Open", "Title": "T"}])

    validate_workspace.WP_JSONL = wp_file
    validate_workspace.BUG_JSONL = bug_file
    validate_workspace.TST_JSONL = tst_file
    validate_workspace.US_JSONL = us_file

    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_jsonl_structural(result)
        assert result.ok, f"Unexpected errors: {result.errors}"
        assert not result.warnings, f"Unexpected warnings: {result.warnings}"
    finally:
        validate_workspace.WP_JSONL = original_wp
        validate_workspace.BUG_JSONL = original_bug
        validate_workspace.TST_JSONL = original_tst
        validate_workspace.US_JSONL = original_us


def test_check_jsonl_structural_reports_missing_file(tmp_path):
    """_check_jsonl_structural should report warning when a JSONL file is missing."""
    original_wp = validate_workspace.WP_JSONL
    original_bug = validate_workspace.BUG_JSONL
    original_tst = validate_workspace.TST_JSONL
    original_us = validate_workspace.US_JSONL

    validate_workspace.WP_JSONL = tmp_path / "nonexistent.jsonl"
    validate_workspace.BUG_JSONL = tmp_path / "nonexistent2.jsonl"
    validate_workspace.TST_JSONL = tmp_path / "nonexistent3.jsonl"
    validate_workspace.US_JSONL = tmp_path / "nonexistent4.jsonl"

    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_jsonl_structural(result)
        # Missing files are warnings (pre-MNT-018 transition), not hard errors
        assert result.ok
        assert any("not found" in w for w in result.warnings)
    finally:
        validate_workspace.WP_JSONL = original_wp
        validate_workspace.BUG_JSONL = original_bug
        validate_workspace.TST_JSONL = original_tst
        validate_workspace.US_JSONL = original_us


def test_check_jsonl_structural_warns_invalid_enum(tmp_path):
    """_check_jsonl_structural should warn on invalid Status enum values."""
    original_wp = validate_workspace.WP_JSONL
    original_bug = validate_workspace.BUG_JSONL
    original_tst = validate_workspace.TST_JSONL
    original_us = validate_workspace.US_JSONL

    wp_file = tmp_path / "workpackages.jsonl"
    bug_file = tmp_path / "bugs.jsonl"
    tst_file = tmp_path / "test-results.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "InvalidStatus", "Name": "T"}])
    _write_jsonl(bug_file, [])
    _write_jsonl(tst_file, [])
    _write_jsonl(us_file, [])

    validate_workspace.WP_JSONL = wp_file
    validate_workspace.BUG_JSONL = bug_file
    validate_workspace.TST_JSONL = tst_file
    validate_workspace.US_JSONL = us_file

    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_jsonl_structural(result)
        assert result.ok, f"Unexpected errors: {result.errors}"
        assert any("InvalidStatus" in w for w in result.warnings)
    finally:
        validate_workspace.WP_JSONL = original_wp
        validate_workspace.BUG_JSONL = original_bug
        validate_workspace.TST_JSONL = original_tst
        validate_workspace.US_JSONL = original_us


def test_check_jsonl_structural_errors_on_corrupt_json(tmp_path):
    """_check_jsonl_structural should report error when a line is not valid JSON."""
    original_wp = validate_workspace.WP_JSONL
    original_bug = validate_workspace.BUG_JSONL
    original_tst = validate_workspace.TST_JSONL
    original_us = validate_workspace.US_JSONL

    wp_file = tmp_path / "workpackages.jsonl"
    bug_file = tmp_path / "bugs.jsonl"
    tst_file = tmp_path / "test-results.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    wp_file.write_text('{"ID": "GUI-001", "Status": "Done"}\nNOT_JSON\n', encoding="utf-8")
    _write_jsonl(bug_file, [])
    _write_jsonl(tst_file, [])
    _write_jsonl(us_file, [])

    validate_workspace.WP_JSONL = wp_file
    validate_workspace.BUG_JSONL = bug_file
    validate_workspace.TST_JSONL = tst_file
    validate_workspace.US_JSONL = us_file

    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_jsonl_structural(result)
        assert not result.ok
        assert any("structural error" in e for e in result.errors)
    finally:
        validate_workspace.WP_JSONL = original_wp
        validate_workspace.BUG_JSONL = original_bug
        validate_workspace.TST_JSONL = original_tst
        validate_workspace.US_JSONL = original_us


# ---------------------------------------------------------------------------
# 5. Functional: dedup_test_ids with temp JSONL
# ---------------------------------------------------------------------------


def test_dedup_no_duplicates(tmp_path):
    """dedup_test_ids should do nothing when no duplicates exist."""
    tst_file = tmp_path / "test-results.jsonl"
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "Test Name": "test_a", "Status": "Pass"},
        {"ID": "TST-2", "Test Name": "test_b", "Status": "Pass"},
    ])

    original = dedup_test_ids.TST_JSONL
    dedup_test_ids.TST_JSONL = tst_file
    try:
        result = dedup_test_ids.dedup(dry_run=False)
        assert result == 0
        _, rows = read_jsonl(tst_file)
        assert [r["ID"] for r in rows] == ["TST-1", "TST-2"]
    finally:
        dedup_test_ids.TST_JSONL = original


def test_dedup_renumbers_duplicates(tmp_path):
    """dedup_test_ids should renumber later occurrences of duplicate IDs."""
    tst_file = tmp_path / "test-results.jsonl"
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "Test Name": "test_a", "Status": "Pass"},
        {"ID": "TST-1", "Test Name": "test_b", "Status": "Pass"},
        {"ID": "TST-2", "Test Name": "test_c", "Status": "Fail"},
    ])

    original = dedup_test_ids.TST_JSONL
    dedup_test_ids.TST_JSONL = tst_file
    try:
        result = dedup_test_ids.dedup(dry_run=False)
        assert result == 0
        _, rows = read_jsonl(tst_file)
        ids = [r["ID"] for r in rows]
        # First TST-1 kept, second renamed, TST-2 kept
        assert ids[0] == "TST-1"
        assert ids[1] != "TST-1"
        assert ids[2] == "TST-2"
        assert len(set(ids)) == 3  # all unique
    finally:
        dedup_test_ids.TST_JSONL = original


def test_dedup_dry_run_does_not_modify(tmp_path):
    """dedup_test_ids --dry-run should not modify the file."""
    tst_file = tmp_path / "test-results.jsonl"
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "Test Name": "test_a", "Status": "Pass"},
        {"ID": "TST-1", "Test Name": "test_b", "Status": "Pass"},
    ])
    original_content = tst_file.read_text(encoding="utf-8")

    original = dedup_test_ids.TST_JSONL
    dedup_test_ids.TST_JSONL = tst_file
    try:
        dedup_test_ids.dedup(dry_run=True)
        assert tst_file.read_text(encoding="utf-8") == original_content
    finally:
        dedup_test_ids.TST_JSONL = original


# ---------------------------------------------------------------------------
# 6. Functional: archive_test_results with temp JSONL
# ---------------------------------------------------------------------------


def test_archive_moves_done_wp_results(tmp_path):
    """archive_test_results should move test rows for Done WPs to archive."""
    tst_file = tmp_path / "test-results.jsonl"
    archive_file = tmp_path / "archived-test-results.jsonl"
    wp_file = tmp_path / "workpackages.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "Done", "Name": "A"},
        {"ID": "GUI-002", "Status": "In Progress", "Name": "B"},
    ])
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "WP Reference": "GUI-001", "Status": "Pass"},
        {"ID": "TST-2", "WP Reference": "GUI-002", "Status": "Pass"},
    ])

    orig_tst = archive_test_results.TST_JSONL
    orig_arch = archive_test_results.ARCHIVE_JSONL
    orig_wp = archive_test_results.WP_JSONL
    archive_test_results.TST_JSONL = tst_file
    archive_test_results.ARCHIVE_JSONL = archive_file
    archive_test_results.WP_JSONL = wp_file
    try:
        result = archive_test_results.archive(dry_run=False)
        assert result == 0

        _, active = read_jsonl(tst_file)
        assert len(active) == 1
        assert active[0]["WP Reference"] == "GUI-002"

        _, archived = read_jsonl(archive_file)
        assert len(archived) == 1
        assert archived[0]["WP Reference"] == "GUI-001"
    finally:
        archive_test_results.TST_JSONL = orig_tst
        archive_test_results.ARCHIVE_JSONL = orig_arch
        archive_test_results.WP_JSONL = orig_wp


def test_archive_dry_run_no_change(tmp_path):
    """archive_test_results --dry-run should not modify any files."""
    tst_file = tmp_path / "test-results.jsonl"
    wp_file = tmp_path / "workpackages.jsonl"
    archive_file = tmp_path / "archived-test-results.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "Done", "Name": "A"}])
    _write_jsonl(tst_file, [{"ID": "TST-1", "WP Reference": "GUI-001", "Status": "Pass"}])
    original_content = tst_file.read_text(encoding="utf-8")

    orig_tst = archive_test_results.TST_JSONL
    orig_arch = archive_test_results.ARCHIVE_JSONL
    orig_wp = archive_test_results.WP_JSONL
    archive_test_results.TST_JSONL = tst_file
    archive_test_results.ARCHIVE_JSONL = archive_file
    archive_test_results.WP_JSONL = wp_file
    try:
        archive_test_results.archive(dry_run=True)
        assert tst_file.read_text(encoding="utf-8") == original_content
        assert not archive_file.exists()
    finally:
        archive_test_results.TST_JSONL = orig_tst
        archive_test_results.ARCHIVE_JSONL = orig_arch
        archive_test_results.WP_JSONL = orig_wp


# ---------------------------------------------------------------------------
# 7. Functional: update_bug_status with temp JSONL
# ---------------------------------------------------------------------------


def test_update_bug_status_success(tmp_path):
    """update_bug_status should update the Status of the given bug."""
    bug_file = tmp_path / "bugs.jsonl"
    _write_jsonl(bug_file, [
        {"ID": "BUG-001", "Status": "Open", "Title": "Test bug"},
    ])

    original = update_bug_status.JSONL_PATH
    update_bug_status.JSONL_PATH = bug_file
    try:
        # Simulate CLI: patch sys.argv
        import sys
        original_argv = sys.argv
        sys.argv = ["update_bug_status.py", "BUG-001", "--status", "Closed"]
        try:
            result = update_bug_status.main()
        finally:
            sys.argv = original_argv
        assert result == 0
        _, rows = read_jsonl(bug_file)
        assert rows[0]["Status"] == "Closed"
    finally:
        update_bug_status.JSONL_PATH = original


def test_update_bug_status_not_found(tmp_path):
    """update_bug_status should return 1 when bug ID not found."""
    bug_file = tmp_path / "bugs.jsonl"
    _write_jsonl(bug_file, [{"ID": "BUG-001", "Status": "Open", "Title": "Test"}])

    original = update_bug_status.JSONL_PATH
    update_bug_status.JSONL_PATH = bug_file
    try:
        import sys
        original_argv = sys.argv
        sys.argv = ["update_bug_status.py", "BUG-999", "--status", "Closed"]
        try:
            result = update_bug_status.main()
        finally:
            sys.argv = original_argv
        assert result == 1
    finally:
        update_bug_status.JSONL_PATH = original


# ---------------------------------------------------------------------------
# 8. Functional: _cascade_us_status handles JSON array Linked WPs
# ---------------------------------------------------------------------------


def test_cascade_us_status_with_list_linked_wps(tmp_path):
    """_cascade_us_status handles Linked WPs stored as a JSON array (list)."""
    wp_file = tmp_path / "workpackages.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "Done", "Name": "A", "User Story": "US-001"},
        {"ID": "GUI-002", "Status": "Done", "Name": "B", "User Story": "US-001"},
    ])
    # Linked WPs stored as list (as MNT-016 would produce after conversion)
    us_data = json.dumps({
        "ID": "US-001",
        "Status": "In Progress",
        "Name": "Test story",
        "Linked WPs": ["GUI-001", "GUI-002"],
    })
    us_file.write_text(us_data + "\n", encoding="utf-8")

    orig_wp = finalize_wp.WP_JSONL
    orig_us = finalize_wp.US_JSONL
    finalize_wp.WP_JSONL = wp_file
    finalize_wp.US_JSONL = us_file
    try:
        finalize_wp._cascade_us_status("GUI-001", dry_run=True)
        # If no exception, the list handling worked correctly
    finally:
        finalize_wp.WP_JSONL = orig_wp
        finalize_wp.US_JSONL = orig_us


def test_cascade_us_status_with_string_linked_wps(tmp_path):
    """_cascade_us_status handles Linked WPs stored as comma-separated string (fallback)."""
    wp_file = tmp_path / "workpackages.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "Done", "Name": "A", "User Story": "US-001"},
        {"ID": "GUI-002", "Status": "Done", "Name": "B", "User Story": "US-001"},
    ])
    _write_jsonl(us_file, [
        {
            "ID": "US-001",
            "Status": "In Progress",
            "Name": "T",
            "Linked WPs": "GUI-001, GUI-002",
        }
    ])

    orig_wp = finalize_wp.WP_JSONL
    orig_us = finalize_wp.US_JSONL
    finalize_wp.WP_JSONL = wp_file
    finalize_wp.US_JSONL = us_file
    try:
        finalize_wp._cascade_us_status("GUI-001", dry_run=True)
    finally:
        finalize_wp.WP_JSONL = orig_wp
        finalize_wp.US_JSONL = orig_us


# ---------------------------------------------------------------------------
# 9. Functional: _check_us_cascade handles list Linked WPs
# ---------------------------------------------------------------------------


def test_check_us_cascade_with_list_linked_wps(tmp_path):
    """_check_us_cascade handles Linked WPs stored as a JSON array."""
    wp_file = tmp_path / "workpackages.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "Done", "Name": "A"},
    ])
    us_data = json.dumps({
        "ID": "US-001",
        "Status": "In Progress",
        "Name": "T",
        "Linked WPs": ["GUI-001"],
    })
    us_file.write_text(us_data + "\n", encoding="utf-8")

    orig_wp = validate_workspace.WP_JSONL
    orig_us = validate_workspace.US_JSONL
    validate_workspace.WP_JSONL = wp_file
    validate_workspace.US_JSONL = us_file
    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_us_cascade(result)
        # Should warn that US-001 has all done WPs but is still In Progress
        assert any("US-001" in w for w in result.warnings)
    finally:
        validate_workspace.WP_JSONL = orig_wp
        validate_workspace.US_JSONL = orig_us


# ---------------------------------------------------------------------------
# 10. Functional: _check_dependency_ordering handles list Depends On
# ---------------------------------------------------------------------------


def test_check_dependency_ordering_with_list_depends_on(tmp_path):
    """_check_dependency_ordering handles Depends On stored as a JSON array."""
    wp_file = tmp_path / "workpackages.jsonl"

    # MNT-017 depends on MNT-015 (Done) and MNT-016 (Done) — no warnings
    content = (
        json.dumps({"ID": "MNT-015", "Status": "Done", "Name": "A", "Depends On": []}) + "\n"
        + json.dumps({"ID": "MNT-016", "Status": "Done", "Name": "B", "Depends On": []}) + "\n"
        + json.dumps({"ID": "MNT-017", "Status": "In Progress", "Name": "C",
                      "Depends On": ["MNT-015", "MNT-016"]}) + "\n"
    )
    wp_file.write_text(content, encoding="utf-8")

    orig_wp = validate_workspace.WP_JSONL
    validate_workspace.WP_JSONL = wp_file
    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_dependency_ordering(result)
        # All dependencies done — no warnings expected
        assert not any("MNT-017" in w for w in result.warnings), result.warnings
    finally:
        validate_workspace.WP_JSONL = orig_wp


def test_check_dependency_ordering_warns_unmet_dependency(tmp_path):
    """_check_dependency_ordering warns when a dependency is not Done."""
    wp_file = tmp_path / "workpackages.jsonl"

    content = (
        json.dumps({"ID": "MNT-015", "Status": "In Progress", "Name": "A", "Depends On": []}) + "\n"
        + json.dumps({"ID": "MNT-017", "Status": "In Progress", "Name": "C",
                      "Depends On": ["MNT-015"]}) + "\n"
    )
    wp_file.write_text(content, encoding="utf-8")

    orig_wp = validate_workspace.WP_JSONL
    validate_workspace.WP_JSONL = wp_file
    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_dependency_ordering(result)
        assert any("MNT-017" in w for w in result.warnings), result.warnings
    finally:
        validate_workspace.WP_JSONL = orig_wp
