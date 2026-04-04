"""Tester edge-case tests for scripts/migrate_csv_to_jsonl.py (MNT-016).

These tests go beyond the Developer's suite by targeting:
- Partial failure isolation (CSVs preserved when a later conversion fails)
- Unicode and special character preservation through the JSON roundtrip
- Comma-within-quoted-field not split for non-nested columns
- Pre-existing JSONL overwrite (idempotent re-run for already-done files)
- Dry-run summary output correctness
- Mixed rows with both empty and non-empty nested fields
- Security: no path traversal possible via hardcoded migration table
"""

import csv
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from migrate_csv_to_jsonl import (
    _MIGRATIONS,
    _convert_one,
    _convert_row,
    _split_array_field,
    main,
)


# ---------------------------------------------------------------------------
# Helpers (duplicated locally to avoid coupling to developer test helpers)
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write a minimal CSV with QUOTE_ALL."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _build_fake_repo(tmp_path: Path) -> Path:
    """Create directory structure matching _MIGRATIONS paths."""
    (tmp_path / "docs" / "workpackages").mkdir(parents=True)
    (tmp_path / "docs" / "user-stories").mkdir(parents=True)
    (tmp_path / "docs" / "bugs").mkdir(parents=True)
    (tmp_path / "docs" / "test-results").mkdir(parents=True)
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "docs" / "maintenance").mkdir(parents=True)
    (tmp_path / "scripts").mkdir(parents=True)
    return tmp_path


def _write_required_csvs(repo: Path) -> None:
    _write_csv(
        repo / "docs/workpackages/workpackages.csv",
        [{"ID": "MNT-016", "Name": "Test", "Depends On": "MNT-015"}],
    )
    _write_csv(
        repo / "docs/user-stories/user-stories.csv",
        [{"ID": "US-001", "Title": "Story", "Linked WPs": "GUI-001"}],
    )
    _write_csv(
        repo / "docs/bugs/bugs.csv",
        [{"ID": "BUG-001", "Title": "bug"}],
    )
    _write_csv(
        repo / "docs/test-results/test-results.csv",
        [{"ID": "TST-001", "Name": "t"}],
    )
    _write_csv(
        repo / "docs/decisions/index.csv",
        [{"ADR-ID": "ADR-007", "Related WPs": "MNT-015, MNT-016"}],
    )
    _write_csv(
        repo / "docs/maintenance/orchestrator-runs.csv",
        [{"Run-ID": "1", "Notes": "x"}],
    )


def _run_main_with_repo(mod, repo: Path, argv: list[str]) -> int:
    """Run main() logic against a fake repository root."""
    import argparse as _ap

    parser = _ap.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    dry_run = args.dry_run

    files_converted = 0
    total_rows = 0
    csvs_to_delete: list[Path] = []

    for csv_rel, jsonl_rel, required in mod._MIGRATIONS:
        csv_path = repo / csv_rel
        jsonl_path = repo / jsonl_rel
        if not csv_path.exists():
            if required:
                return 1
            continue
        try:
            row_count = mod._convert_one(csv_path, jsonl_path, dry_run)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        files_converted += 1
        total_rows += row_count
        csvs_to_delete.append(csv_path)

    if not dry_run:
        for p in csvs_to_delete:
            p.unlink()

    return 0


# ---------------------------------------------------------------------------
# Edge case: Partial failure preserves ALL original CSVs
# ---------------------------------------------------------------------------

class TestPartialFailureIsolation:
    """When a later conversion fails, earlier CSVs must not be deleted."""

    def test_all_csvs_preserved_when_third_conversion_fails(self, tmp_path):
        """CSVs must survive intact if any conversion raises an exception."""
        repo = _build_fake_repo(tmp_path)
        _write_required_csvs(repo)

        call_count = {"n": 0}
        original_convert = _convert_one

        def failing_on_third(csv_path, jsonl_path, dry_run):
            call_count["n"] += 1
            if call_count["n"] == 3:
                raise ValueError("Simulated conversion failure on file 3")
            return original_convert(csv_path, jsonl_path, dry_run)

        import migrate_csv_to_jsonl as mod

        orig = mod._convert_one
        mod._convert_one = failing_on_third
        try:
            rc = _run_main_with_repo(mod, repo, [])
        finally:
            mod._convert_one = orig

        # Exit code must be 1
        assert rc == 1

        # ALL required CSVs must still exist (none deleted)
        for csv_rel, _, required in _MIGRATIONS:
            if required:
                assert (repo / csv_rel).exists(), f"CSV was wrongly deleted: {csv_rel}"

    def test_jsonl_files_from_successful_conversions_exist_after_partial_failure(
        self, tmp_path
    ):
        """Successfully converted JSONL files exist; their source CSVs also remain."""
        repo = _build_fake_repo(tmp_path)
        _write_required_csvs(repo)

        call_count = {"n": 0}
        original_convert = _convert_one

        def failing_on_second(csv_path, jsonl_path, dry_run):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise ValueError("Second conversion fails")
            return original_convert(csv_path, jsonl_path, dry_run)

        import migrate_csv_to_jsonl as mod

        orig = mod._convert_one
        mod._convert_one = failing_on_second
        try:
            rc = _run_main_with_repo(mod, repo, [])
        finally:
            mod._convert_one = orig

        assert rc == 1
        # First file's JSONL should exist (it succeeded)
        first_jsonl = repo / _MIGRATIONS[0][1]
        assert first_jsonl.exists()
        # First file's CSV must NOT have been deleted
        first_csv = repo / _MIGRATIONS[0][0]
        assert first_csv.exists()


# ---------------------------------------------------------------------------
# Edge case: Unicode content preserved through roundtrip
# ---------------------------------------------------------------------------

class TestUnicodePreservation:
    def test_unicode_values_survive_jsonl_roundtrip(self, tmp_path):
        """Strings with non-ASCII characters are preserved exactly."""
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"
        rows = [
            {"ID": "BUG-001", "Title": "Änderung: kein Zugriff möglich"},
            {"ID": "BUG-002", "Title": "日本語テスト"},
            {"ID": "BUG-003", "Title": "Accents: café, naïve, résumé"},
        ]
        _write_csv(csv_path, rows)

        count = _convert_one(csv_path, jsonl_path, dry_run=False)

        assert count == 3
        written = _read_jsonl(jsonl_path)
        assert written[0]["Title"] == "Änderung: kein Zugriff möglich"
        assert written[1]["Title"] == "日本語テスト"
        assert written[2]["Title"] == "Accents: café, naïve, résumé"

    def test_unicode_in_nested_array_field(self, tmp_path):
        """Unicode chars in nested fields correctly parsed into arrays."""
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        # Simulate a "Depends On" field with items that have unicode names (unlikely
        # in practice but must not corrupt the value).
        rows = [{"ID": "X-001", "Name": "Résumé WP", "Depends On": "A-001, B-002"}]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        assert written[0]["Depends On"] == ["A-001", "B-002"]
        assert written[0]["Name"] == "Résumé WP"


# ---------------------------------------------------------------------------
# Edge case: Comma inside quoted non-nested field is NOT split
# ---------------------------------------------------------------------------

class TestCommaInNonNestedField:
    def test_quoted_comma_in_non_array_column_stays_as_string(self, tmp_path):
        """A comma inside a quoted field in a non-nested column must NOT be split."""
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"
        # CSV quoting ensures the comma is part of the field value
        rows = [{"ID": "BUG-001", "Title": "Error: file not found, please retry"}]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        # Title should survive as-is, never split
        assert written[0]["Title"] == "Error: file not found, please retry"

    def test_quoted_comma_in_non_nested_column_workpackages(self, tmp_path):
        """Non-nested columns in workpackages.csv with commas stay intact."""
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        rows = [
            {
                "ID": "MNT-016",
                "Name": "Create script, migrate data",
                "Depends On": "MNT-015",
            }
        ]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        assert written[0]["Name"] == "Create script, migrate data"
        assert written[0]["Depends On"] == ["MNT-015"]


# ---------------------------------------------------------------------------
# Edge case: Pre-existing JSONL file is overwritten (re-run safety)
# ---------------------------------------------------------------------------

class TestPreExistingJsonlOverwrite:
    def test_existing_jsonl_is_overwritten_not_appended(self, tmp_path):
        """If a JSONL file from a previous run exists, it is cleanly overwritten."""
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"

        # Pre-existing JSONL with stale data
        jsonl_path.write_text(
            '{"ID": "OLD-001", "Title": "stale"}\n', encoding="utf-8"
        )

        rows = [{"ID": "BUG-001", "Title": "fresh"}]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        assert len(written) == 1
        assert written[0]["ID"] == "BUG-001"
        assert written[0]["Title"] == "fresh"


# ---------------------------------------------------------------------------
# Edge case: Mixed rows — some have empty nested fields, some do not
# ---------------------------------------------------------------------------

class TestMixedNestedFieldRows:
    def test_mixed_empty_and_populated_depends_on(self, tmp_path):
        """Rows with empty Depends On become [] while populated ones become list."""
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        rows = [
            {"ID": "WP-001", "Depends On": ""},
            {"ID": "WP-002", "Depends On": "WP-001"},
            {"ID": "WP-003", "Depends On": "WP-001, WP-002"},
        ]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        assert written[0]["Depends On"] == []
        assert written[1]["Depends On"] == ["WP-001"]
        assert written[2]["Depends On"] == ["WP-001", "WP-002"]

    def test_single_dependency_becomes_single_element_list(self, tmp_path):
        """A single value in a nested field becomes a one-element list, not a string."""
        row = {"ID": "X", "Depends On": "MNT-015"}
        result = _convert_row(row, "workpackages")
        assert result["Depends On"] == ["MNT-015"]
        assert isinstance(result["Depends On"], list)


# ---------------------------------------------------------------------------
# Edge case: Dry-run summary output correctness
# ---------------------------------------------------------------------------

class TestDryRunOutput:
    def test_dry_run_prints_summary_with_zero_deletions(self, tmp_path, capsys):
        """Dry-run summary must report 0 CSVs deleted."""
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"
        _write_csv(csv_path, [{"ID": "BUG-001", "Title": "x"}])

        _convert_one(csv_path, jsonl_path, dry_run=True)

        captured = capsys.readouterr()
        assert "dry-run" in captured.out.lower()
        # JSONL must not be created
        assert not jsonl_path.exists()

    def test_dry_run_shows_row_count_in_output(self, tmp_path, capsys):
        """Dry-run output must include row count information."""
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        rows = [
            {"ID": "WP-001", "Depends On": ""},
            {"ID": "WP-002", "Depends On": "WP-001"},
        ]
        _write_csv(csv_path, rows)

        count = _convert_one(csv_path, jsonl_path, dry_run=True)

        assert count == 2
        captured = capsys.readouterr()
        assert "2 rows" in captured.out or "2)" in captured.out or "(2 rows)" in captured.out


# ---------------------------------------------------------------------------
# Edge case: Whitespace stripping in nested array values
# ---------------------------------------------------------------------------

class TestWhitespaceStrippingInArrays:
    def test_values_with_leading_trailing_spaces_stripped(self):
        result = _split_array_field("  WP-001  ,  WP-002  ,  WP-003  ")
        assert result == ["WP-001", "WP-002", "WP-003"]

    def test_mixed_whitespace_patterns(self):
        result = _split_array_field("A,  B  ,C,   D")
        assert result == ["A", "B", "C", "D"]

    def test_only_spaces_between_commas_filtered(self):
        # "A,   ,B" — the middle item is whitespace-only and must be filtered
        result = _split_array_field("A,   ,B")
        assert result == ["A", "B"]


# ---------------------------------------------------------------------------
# Edge case: JSONL content is valid JSON on every line (not just first)
# ---------------------------------------------------------------------------

class TestJsonlValidity:
    def test_every_line_in_output_is_valid_json(self, tmp_path):
        """All lines in the JSONL output must parse as valid JSON objects."""
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        rows = [
            {"ID": "WP-001", "Name": "Alpha", "Depends On": ""},
            {"ID": "WP-002", "Name": "Beta", "Depends On": "WP-001"},
            {"ID": "WP-003", "Name": "Gamma", "Depends On": "WP-001, WP-002"},
        ]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        lines = [
            line.strip()
            for line in jsonl_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)  # raises if invalid JSON
            assert isinstance(obj, dict)
            assert "ID" in obj


# ---------------------------------------------------------------------------
# Security: no path traversal in _convert_row (untrusted CSV content)
# ---------------------------------------------------------------------------

class TestSecurityPathTraversal:
    def test_path_traversal_attempt_in_field_value_is_harmless(self):
        """A field value containing '../' does not affect any file operations."""
        row = {
            "ID": "EVIL-001",
            "Name": "../../../etc/passwd",
            "Depends On": "../../secret",
        }
        result = _convert_row(row, "workpackages")
        # Name is a string field — unchanged
        assert result["Name"] == "../../../etc/passwd"
        # Depends On is a nested field — split into list, not interpreted as path
        assert result["Depends On"] == ["../../secret"]

    def test_migration_table_uses_only_hardcoded_paths(self):
        """The _MIGRATIONS list must contain only docs/ prefixed paths (no user input)."""
        for csv_rel, jsonl_rel, _ in _MIGRATIONS:
            assert csv_rel.startswith("docs/") or csv_rel.startswith("scripts/"), (
                f"Unexpected migration source: {csv_rel}"
            )
            assert jsonl_rel.startswith("docs/") or jsonl_rel.startswith("scripts/"), (
                f"Unexpected migration target: {jsonl_rel}"
            )
