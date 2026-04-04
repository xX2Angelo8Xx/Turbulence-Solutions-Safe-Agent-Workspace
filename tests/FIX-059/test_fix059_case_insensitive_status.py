"""FIX-059: Validate case-insensitive Status recognition in the workspace validator.

Tests that _check_tst_coverage() correctly recognises 'PASS', 'Pass', and 'pass'
as passing statuses, and that normalized JSONL entries have correct column alignment.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from validate_workspace import ValidationResult, _check_tst_coverage  # noqa: E402


def _make_wp_rows(wp_ids: list[str]) -> list[dict]:
    """Create minimal WP rows for testing."""
    return [{"ID": wp_id, "Status": "Done", "Comments": ""} for wp_id in wp_ids]


def _make_tst_rows(entries: list[tuple[str, str]]) -> list[dict]:
    """Create minimal TST rows: list of (WP Reference, Status)."""
    return [{"WP Reference": wp, "Status": status} for wp, status in entries]


def test_pass_uppercase_recognized():
    """'PASS' (uppercase) must be recognized as passing."""
    result = ValidationResult()
    wp_rows = _make_wp_rows(["FIX-100"])
    tst_rows = _make_tst_rows([("FIX-100", "PASS")])
    with patch("validate_workspace.read_jsonl") as mock_jsonl:
        mock_jsonl.side_effect = [
            ([], wp_rows),  # WP JSONL
            ([], tst_rows),  # TST JSONL
        ]
        _check_tst_coverage(result)
    assert result.ok, f"Unexpected errors: {result.errors}"


def test_pass_titlecase_recognized():
    """'Pass' (title-case) must be recognized as passing."""
    result = ValidationResult()
    wp_rows = _make_wp_rows(["FIX-100"])
    tst_rows = _make_tst_rows([("FIX-100", "Pass")])
    with patch("validate_workspace.read_jsonl") as mock_jsonl:
        mock_jsonl.side_effect = [
            ([], wp_rows),
            ([], tst_rows),
        ]
        _check_tst_coverage(result)
    assert result.ok, f"Unexpected errors: {result.errors}"


def test_pass_lowercase_recognized():
    """'pass' (lowercase) must be recognized as passing."""
    result = ValidationResult()
    wp_rows = _make_wp_rows(["FIX-100"])
    tst_rows = _make_tst_rows([("FIX-100", "pass")])
    with patch("validate_workspace.read_jsonl") as mock_jsonl:
        mock_jsonl.side_effect = [
            ([], wp_rows),
            ([], tst_rows),
        ]
        _check_tst_coverage(result)
    assert result.ok, f"Unexpected errors: {result.errors}"


def test_fail_not_counted_as_pass():
    """'Fail' status must NOT count as a passing entry."""
    result = ValidationResult()
    wp_rows = _make_wp_rows(["FIX-100"])
    tst_rows = _make_tst_rows([("FIX-100", "Fail")])
    with patch("validate_workspace.read_jsonl") as mock_jsonl:
        mock_jsonl.side_effect = [
            ([], wp_rows),
            ([], tst_rows),
        ]
        _check_tst_coverage(result)
    assert not result.ok, "Expected an error for Fail-only WP"
    assert any("FIX-100" in e for e in result.errors)


def test_normalized_jsonl_column_alignment():
    """Verify the 14 normalized legacy entries now have correct WP Reference."""
    jsonl_path = Path(__file__).resolve().parents[2] / "docs" / "test-results" / "test-results.jsonl"
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from jsonl_utils import read_jsonl

    _, rows = read_jsonl(jsonl_path)

    # These TST IDs were the 14 legacy entries that had misaligned columns
    legacy_ids = {
        "TST-1813", "TST-1814", "TST-1815", "TST-1816", "TST-1817", "TST-1818",
        "TST-1891", "TST-1892", "TST-1893", "TST-1894", "TST-1895", "TST-1896",
        "TST-1897", "TST-1898",
    }

    for row in rows:
        if row["ID"] in legacy_ids:
            assert row["WP Reference"] in ("FIX-037", "FIX-042"), (
                f"{row['ID']}: WP Reference should be FIX-037 or FIX-042, "
                f"got '{row['WP Reference']}'"
            )
            assert row["Status"] == "Pass", (
                f"{row['ID']}: Status should be 'Pass', got '{row['Status']}'"
            )
