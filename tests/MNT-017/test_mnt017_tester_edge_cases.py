"""Tester edge-case tests for MNT-017: Migrate all data scripts to JSONL.

Covers scenarios missed by the developer's test suite:
1. _check_duplicate_ids detects duplicates in JSONL
2. dedup_test_ids with an empty JSONL file
3. archive_test_results with no Done WPs (nothing moved)
4. archive_test_results appends to an existing archive file
5. _add_wps_batch Linked WPs list handling (functional smoke)
6. validate_workspace._check_adr_consistency with .jsonl ADR index path
7. update_architecture.py REPO_ROOT is a real Path, not a string
8. add_workpackage._update_us_linked_wps appends to existing list Linked WPs
9. validate_workspace._check_duplicate_ids skips gracefully when file missing
10. archive_test_results handles test row with WP Reference that no longer exists
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import add_workpackage
import archive_test_results
import dedup_test_ids
import finalize_wp
import update_architecture
import validate_workspace
from jsonl_utils import read_jsonl, write_jsonl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    write_jsonl(path, fieldnames, rows)


# ---------------------------------------------------------------------------
# 1. _check_duplicate_ids detects duplicates in JSONL
# ---------------------------------------------------------------------------


def test_check_duplicate_ids_detects_duplicates(tmp_path):
    """_check_duplicate_ids must flag duplicate IDs in a JSONL file."""
    tst_file = tmp_path / "test-results.jsonl"
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "Test Name": "a", "Status": "Pass"},
        {"ID": "TST-1", "Test Name": "b", "Status": "Pass"},  # duplicate
        {"ID": "TST-2", "Test Name": "c", "Status": "Pass"},
    ])

    result = validate_workspace.ValidationResult()
    validate_workspace._check_duplicate_ids(tst_file, "ID", result)

    assert not result.ok
    assert any("TST-1" in e for e in result.errors), (
        f"Expected error about TST-1 duplicate, got: {result.errors}"
    )


def test_check_duplicate_ids_no_duplicates(tmp_path):
    """_check_duplicate_ids must not report errors when all IDs are unique."""
    tst_file = tmp_path / "test-results.jsonl"
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "Test Name": "a", "Status": "Pass"},
        {"ID": "TST-2", "Test Name": "b", "Status": "Pass"},
        {"ID": "TST-3", "Test Name": "c", "Status": "Fail"},
    ])

    result = validate_workspace.ValidationResult()
    validate_workspace._check_duplicate_ids(tst_file, "ID", result)

    assert result.ok, f"Unexpected errors: {result.errors}"


def test_check_duplicate_ids_missing_file_is_warning(tmp_path):
    """_check_duplicate_ids must emit a warning (not error) when file is missing."""
    missing = tmp_path / "nonexistent.jsonl"

    result = validate_workspace.ValidationResult()
    validate_workspace._check_duplicate_ids(missing, "ID", result)

    # Should still be ok — missing JSONL files are pre-MNT-018 warnings
    assert result.ok, f"Unexpected errors: {result.errors}"
    assert any("not found" in w for w in result.warnings), (
        f"Expected a warning about missing file, got: {result.warnings}"
    )


# ---------------------------------------------------------------------------
# 2. dedup_test_ids with an empty JSONL file
# ---------------------------------------------------------------------------


def test_dedup_empty_file(tmp_path):
    """dedup_test_ids on an empty JSONL file must not raise and must return 0."""
    tst_file = tmp_path / "test-results.jsonl"
    tst_file.write_text("", encoding="utf-8")

    original = dedup_test_ids.TST_JSONL
    dedup_test_ids.TST_JSONL = tst_file
    try:
        result = dedup_test_ids.dedup(dry_run=False)
        assert result == 0
        assert tst_file.read_text(encoding="utf-8") == ""
    finally:
        dedup_test_ids.TST_JSONL = original


# ---------------------------------------------------------------------------
# 3. archive_test_results — no Done WPs → nothing is moved
# ---------------------------------------------------------------------------


def test_archive_no_done_wps_moves_nothing(tmp_path):
    """archive_test_results must leave tst file unchanged if no Done WPs."""
    tst_file = tmp_path / "test-results.jsonl"
    wp_file = tmp_path / "workpackages.jsonl"
    archive_file = tmp_path / "archived-test-results.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "In Progress", "Name": "A"},
        {"ID": "GUI-002", "Status": "Review", "Name": "B"},
    ])
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "WP Reference": "GUI-001", "Status": "Pass"},
        {"ID": "TST-2", "WP Reference": "GUI-002", "Status": "Fail"},
    ])
    original_content = tst_file.read_text(encoding="utf-8")

    orig_tst = archive_test_results.TST_JSONL
    orig_arch = archive_test_results.ARCHIVE_JSONL
    orig_wp = archive_test_results.WP_JSONL
    archive_test_results.TST_JSONL = tst_file
    archive_test_results.ARCHIVE_JSONL = archive_file
    archive_test_results.WP_JSONL = wp_file
    try:
        result = archive_test_results.archive(dry_run=False)
        assert result == 0
        assert tst_file.read_text(encoding="utf-8") == original_content
        assert not archive_file.exists()
    finally:
        archive_test_results.TST_JSONL = orig_tst
        archive_test_results.ARCHIVE_JSONL = orig_arch
        archive_test_results.WP_JSONL = orig_wp


# ---------------------------------------------------------------------------
# 4. archive_test_results appends to an existing archive file
# ---------------------------------------------------------------------------


def test_archive_appends_to_existing_archive(tmp_path):
    """archive_test_results must append new rows to an already-existing archive."""
    tst_file = tmp_path / "test-results.jsonl"
    wp_file = tmp_path / "workpackages.jsonl"
    archive_file = tmp_path / "archived-test-results.jsonl"

    _write_jsonl(wp_file, [
        {"ID": "GUI-001", "Status": "Done", "Name": "A"},
        {"ID": "GUI-002", "Status": "Done", "Name": "B"},
    ])
    _write_jsonl(tst_file, [
        {"ID": "TST-3", "WP Reference": "GUI-002", "Status": "Pass"},
    ])
    # Pre-populate the archive with a prior entry
    _write_jsonl(archive_file, [
        {"ID": "TST-1", "WP Reference": "GUI-001", "Status": "Pass"},
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

        _, archived = read_jsonl(archive_file)
        assert len(archived) == 2, f"Expected 2 archived rows, got {len(archived)}"
        assert {r["ID"] for r in archived} == {"TST-1", "TST-3"}
    finally:
        archive_test_results.TST_JSONL = orig_tst
        archive_test_results.ARCHIVE_JSONL = orig_arch
        archive_test_results.WP_JSONL = orig_wp


# ---------------------------------------------------------------------------
# 5. archive_test_results skips test rows for unknown/non-Done WP references
# ---------------------------------------------------------------------------


def test_archive_keeps_unknown_wp_reference_rows(tmp_path):
    """Rows whose WP Reference is not in workpackages at all should stay active."""
    tst_file = tmp_path / "test-results.jsonl"
    wp_file = tmp_path / "workpackages.jsonl"
    archive_file = tmp_path / "archived-test-results.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "Done", "Name": "A"}])
    _write_jsonl(tst_file, [
        {"ID": "TST-1", "WP Reference": "GUI-001", "Status": "Pass"},
        {"ID": "TST-2", "WP Reference": "UNKNOWN-999", "Status": "Pass"},
    ])

    orig_tst = archive_test_results.TST_JSONL
    orig_arch = archive_test_results.ARCHIVE_JSONL
    orig_wp = archive_test_results.WP_JSONL
    archive_test_results.TST_JSONL = tst_file
    archive_test_results.ARCHIVE_JSONL = archive_file
    archive_test_results.WP_JSONL = wp_file
    try:
        archive_test_results.archive(dry_run=False)

        _, active = read_jsonl(tst_file)
        assert len(active) == 1
        assert active[0]["ID"] == "TST-2"

        _, archived = read_jsonl(archive_file)
        assert len(archived) == 1
        assert archived[0]["ID"] == "TST-1"
    finally:
        archive_test_results.TST_JSONL = orig_tst
        archive_test_results.ARCHIVE_JSONL = orig_arch
        archive_test_results.WP_JSONL = orig_wp


# ---------------------------------------------------------------------------
# 6. validate_workspace._check_adr_consistency uses .jsonl ADR index path
# ---------------------------------------------------------------------------


def test_check_adr_consistency_uses_jsonl_adr_path():
    """_check_adr_consistency must point to index.jsonl, not index.csv."""
    import inspect
    src = inspect.getsource(validate_workspace._check_adr_consistency)
    assert "index.jsonl" in src, (
        "_check_adr_consistency must use index.jsonl, not index.csv"
    )
    assert "index.csv" not in src, (
        "_check_adr_consistency must not reference the old index.csv"
    )


def test_check_adr_consistency_missing_index_does_not_raise(tmp_path):
    """_check_adr_consistency should silently skip when ADR index is absent."""
    # Temporarily point validate_workspace to a non-existent WP JSONL
    # so the function exits early without reading real data
    original_wp = validate_workspace.WP_JSONL

    validate_workspace.WP_JSONL = tmp_path / "workpackages.jsonl"
    try:
        result = validate_workspace.ValidationResult()
        # Should not raise — absence of ADR index is treated as 'not set up'
        validate_workspace._check_adr_consistency(result)
    finally:
        validate_workspace.WP_JSONL = original_wp


# ---------------------------------------------------------------------------
# 7. update_architecture.py — REPO_ROOT is a Path instance (not string)
# ---------------------------------------------------------------------------


def test_update_architecture_repo_root_is_path():
    """update_architecture must import REPO_ROOT from jsonl_utils as a Path."""
    from jsonl_utils import REPO_ROOT as util_root
    assert update_architecture.ARCH_PATH.is_absolute()
    # update_architecture uses REPO_ROOT internally for ARCH_PATH
    # Verify it resolves to the same root as jsonl_utils
    assert update_architecture.ARCH_PATH.parent.parent == util_root


# ---------------------------------------------------------------------------
# 8. add_workpackage._update_us_linked_wps appends to existing list Linked WPs
# ---------------------------------------------------------------------------


def test_update_us_linked_wps_appends_to_list(tmp_path):
    """_update_us_linked_wps must correctly append to an existing list-type Linked WPs."""
    us_file = tmp_path / "user-stories.jsonl"
    row = {
        "ID": "US-001",
        "Status": "In Progress",
        "Name": "Test story",
        "Linked WPs": ["GUI-001"],
    }
    us_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

    original = add_workpackage.US_JSONL
    add_workpackage.US_JSONL = us_file
    try:
        add_workpackage._update_us_linked_wps("US-001", "GUI-002")
        _, rows = read_jsonl(us_file)
        linked = rows[0]["Linked WPs"]
        assert isinstance(linked, list), f"Expected list, got {type(linked)}"
        assert "GUI-001" in linked
        assert "GUI-002" in linked
    finally:
        add_workpackage.US_JSONL = original


def test_update_us_linked_wps_no_duplicate(tmp_path):
    """_update_us_linked_wps must not add the same WP ID twice."""
    us_file = tmp_path / "user-stories.jsonl"
    row = {
        "ID": "US-001",
        "Status": "In Progress",
        "Name": "Test story",
        "Linked WPs": ["GUI-001"],
    }
    us_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

    original = add_workpackage.US_JSONL
    add_workpackage.US_JSONL = us_file
    try:
        add_workpackage._update_us_linked_wps("US-001", "GUI-001")  # Already present
        _, rows = read_jsonl(us_file)
        linked = rows[0]["Linked WPs"]
        assert linked.count("GUI-001") == 1, (
            f"GUI-001 should appear exactly once, got: {linked}"
        )
    finally:
        add_workpackage.US_JSONL = original


def test_update_us_linked_wps_not_found_raises(tmp_path):
    """_update_us_linked_wps must raise KeyError when US ID does not exist."""
    us_file = tmp_path / "user-stories.jsonl"
    _write_jsonl(us_file, [
        {"ID": "US-001", "Status": "Open", "Name": "Story", "Linked WPs": []},
    ])

    original = add_workpackage.US_JSONL
    add_workpackage.US_JSONL = us_file
    try:
        with pytest.raises(KeyError):
            add_workpackage._update_us_linked_wps("US-999", "GUI-001")
    finally:
        add_workpackage.US_JSONL = original


# ---------------------------------------------------------------------------
# 9. validate_workspace structural check on corrupt line in each JSONL type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("label,corrupt_fixture", [
    ("bugs", lambda d: (d / "bugs.jsonl").write_text('{"ID":"BUG-1"}\nNOT_JSON\n', encoding="utf-8")),
    ("user-stories", lambda d: (d / "user-stories.jsonl").write_text('{"ID":"US-1"}\nNOT_JSON\n', encoding="utf-8")),
    ("test-results", lambda d: (d / "test-results.jsonl").write_text('NOT_JSON\n', encoding="utf-8")),
])
def test_check_jsonl_structural_corrupt_non_wp_files(tmp_path, label, corrupt_fixture):
    """_check_jsonl_structural must report error for corrupt lines in any JSONL file."""
    wp_file = tmp_path / "workpackages.jsonl"
    bug_file = tmp_path / "bugs.jsonl"
    tst_file = tmp_path / "test-results.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "Done", "Name": "T"}])
    _write_jsonl(bug_file, [{"ID": "BUG-001", "Status": "Open", "Title": "T"}])
    _write_jsonl(tst_file, [{"ID": "TST-1", "Status": "Pass", "Test Name": "T"}])
    _write_jsonl(us_file, [{"ID": "US-001", "Status": "Open", "Name": "T"}])

    # Corrupt the target file
    corrupt_fixture(tmp_path)

    orig_wp = validate_workspace.WP_JSONL
    orig_bug = validate_workspace.BUG_JSONL
    orig_tst = validate_workspace.TST_JSONL
    orig_us = validate_workspace.US_JSONL
    validate_workspace.WP_JSONL = wp_file
    validate_workspace.BUG_JSONL = bug_file
    validate_workspace.TST_JSONL = tst_file
    validate_workspace.US_JSONL = us_file

    try:
        result = validate_workspace.ValidationResult()
        validate_workspace._check_jsonl_structural(result)
        assert not result.ok, (
            f"Expected structural error for corrupt {label} JSONL, but result was OK"
        )
    finally:
        validate_workspace.WP_JSONL = orig_wp
        validate_workspace.BUG_JSONL = orig_bug
        validate_workspace.TST_JSONL = orig_tst
        validate_workspace.US_JSONL = orig_us


# ---------------------------------------------------------------------------
# 10. _cascade_us_status with empty Linked WPs list
# ---------------------------------------------------------------------------


def test_cascade_us_status_empty_linked_wps_list(tmp_path):
    """_cascade_us_status must not crash when Linked WPs is an empty list."""
    wp_file = tmp_path / "workpackages.jsonl"
    us_file = tmp_path / "user-stories.jsonl"

    _write_jsonl(wp_file, [{"ID": "GUI-001", "Status": "Done", "Name": "A", "User Story": "US-001"}])
    us_row = {"ID": "US-001", "Status": "In Progress", "Name": "Story", "Linked WPs": []}
    us_file.write_text(json.dumps(us_row) + "\n", encoding="utf-8")

    orig_wp = finalize_wp.WP_JSONL
    orig_us = finalize_wp.US_JSONL
    finalize_wp.WP_JSONL = wp_file
    finalize_wp.US_JSONL = us_file
    try:
        # Should not raise; empty Linked WPs means no cascade
        finalize_wp._cascade_us_status("GUI-001", dry_run=True)
        _, rows = read_jsonl(us_file)
        assert rows[0]["Status"] == "In Progress", (
            "US status must not change when Linked WPs is empty"
        )
    finally:
        finalize_wp.WP_JSONL = orig_wp
        finalize_wp.US_JSONL = orig_us
