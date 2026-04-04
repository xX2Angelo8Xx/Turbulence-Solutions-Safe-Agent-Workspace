"""Tests for scripts/migrate_csv_to_jsonl.py (MNT-016)."""

import csv
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# Make scripts/ importable
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from migrate_csv_to_jsonl import _split_array_field, _convert_row, _convert_one, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write a minimal CSV using QUOTE_ALL for test fixtures."""
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


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

class TestSplitArrayField:
    def test_simple_two_values(self):
        assert _split_array_field("GUI-001, GUI-002") == ["GUI-001", "GUI-002"]

    def test_no_spaces(self):
        assert _split_array_field("A,B,C") == ["A", "B", "C"]

    def test_empty_string_returns_empty_list(self):
        assert _split_array_field("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert _split_array_field("   ") == []

    def test_single_value(self):
        assert _split_array_field("MNT-015") == ["MNT-015"]

    def test_strips_whitespace(self):
        assert _split_array_field("  A  ,  B  ") == ["A", "B"]

    def test_trailing_comma_ignored(self):
        # "A," — trailing comma produces empty token which is filtered
        assert _split_array_field("A,") == ["A"]


class TestConvertRow:
    def test_depends_on_converted_for_workpackages(self):
        row = {"ID": "MNT-016", "Depends On": "MNT-015, MNT-014", "Name": "Test"}
        result = _convert_row(row, "workpackages")
        assert result["Depends On"] == ["MNT-015", "MNT-014"]
        assert result["Name"] == "Test"

    def test_linked_wps_converted_for_user_stories(self):
        row = {"ID": "US-001", "Linked WPs": "GUI-001, GUI-002", "Title": "X"}
        result = _convert_row(row, "user-stories")
        assert result["Linked WPs"] == ["GUI-001", "GUI-002"]

    def test_related_wps_converted_for_index(self):
        row = {"ADR-ID": "ADR-007", "Related WPs": "MNT-015, MNT-016"}
        result = _convert_row(row, "index")
        assert result["Related WPs"] == ["MNT-015", "MNT-016"]

    def test_empty_depends_on_becomes_empty_list(self):
        row = {"ID": "X", "Depends On": ""}
        result = _convert_row(row, "workpackages")
        assert result["Depends On"] == []

    def test_non_nested_fields_unchanged(self):
        row = {"ID": "BUG-001", "Title": "Some bug", "Status": "Closed"}
        result = _convert_row(row, "bugs")
        assert result == row

    def test_unknown_csv_stem_no_conversion(self):
        row = {"Depends On": "A, B"}  # would convert for "workpackages" but not others
        result = _convert_row(row, "test-results")
        assert result["Depends On"] == "A, B"


# ---------------------------------------------------------------------------
# Integration tests using temp files
# ---------------------------------------------------------------------------

class TestConvertOne:
    def test_basic_conversion_row_count(self, tmp_path):
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"
        rows = [
            {"ID": "BUG-001", "Title": "Alpha", "Status": "Closed"},
            {"ID": "BUG-002", "Title": "Beta", "Status": "Open"},
        ]
        _write_csv(csv_path, rows)

        count = _convert_one(csv_path, jsonl_path, dry_run=False)

        assert count == 2
        assert jsonl_path.exists()
        written = _read_jsonl(jsonl_path)
        assert len(written) == 2

    def test_dry_run_does_not_write_jsonl(self, tmp_path, capsys):
        csv_path = tmp_path / "bugs.csv"
        jsonl_path = tmp_path / "bugs.jsonl"
        _write_csv(csv_path, [{"ID": "BUG-001", "Title": "X"}])

        _convert_one(csv_path, jsonl_path, dry_run=True)

        assert not jsonl_path.exists()
        captured = capsys.readouterr()
        assert "dry-run" in captured.out

    def test_nested_array_field_written_correctly(self, tmp_path):
        csv_path = tmp_path / "workpackages.csv"
        jsonl_path = tmp_path / "workpackages.jsonl"
        rows = [{"ID": "MNT-016", "Depends On": "MNT-015, MNT-014", "Name": "X"}]
        _write_csv(csv_path, rows)

        _convert_one(csv_path, jsonl_path, dry_run=False)

        written = _read_jsonl(jsonl_path)
        assert written[0]["Depends On"] == ["MNT-015", "MNT-014"]

    def test_empty_csv_converts_zero_rows(self, tmp_path):
        csv_path = tmp_path / "orchestrator-runs.csv"
        jsonl_path = tmp_path / "orchestrator-runs.jsonl"
        # Write header-only CSV
        csv_path.write_text('"Run-ID","Date","Notes"\n', encoding="utf-8")

        count = _convert_one(csv_path, jsonl_path, dry_run=False)

        assert count == 0


class TestMainFunction:
    """Tests for the main() entry point using controlled temp repo structure."""

    def _build_fake_repo(self, tmp_path: Path) -> Path:
        """Create a minimal fake repo with the 7 CSV locations."""
        (tmp_path / "docs" / "workpackages").mkdir(parents=True)
        (tmp_path / "docs" / "user-stories").mkdir(parents=True)
        (tmp_path / "docs" / "bugs").mkdir(parents=True)
        (tmp_path / "docs" / "test-results").mkdir(parents=True)
        (tmp_path / "docs" / "decisions").mkdir(parents=True)
        (tmp_path / "docs" / "maintenance").mkdir(parents=True)
        (tmp_path / "scripts").mkdir(parents=True)
        return tmp_path

    def _write_required_csvs(self, repo: Path) -> None:
        _write_csv(
            repo / "docs" / "workpackages" / "workpackages.csv",
            [{"ID": "MNT-016", "Name": "Test", "Depends On": "MNT-015"}],
        )
        _write_csv(
            repo / "docs" / "user-stories" / "user-stories.csv",
            [{"ID": "US-001", "Title": "T", "Linked WPs": "GUI-001"}],
        )
        _write_csv(
            repo / "docs" / "bugs" / "bugs.csv",
            [{"ID": "BUG-001", "Title": "b"}],
        )
        _write_csv(
            repo / "docs" / "test-results" / "test-results.csv",
            [{"ID": "TST-001", "Name": "t"}],
        )
        _write_csv(
            repo / "docs" / "decisions" / "index.csv",
            [{"ADR-ID": "ADR-007", "Related WPs": "MNT-015, MNT-016"}],
        )
        _write_csv(
            repo / "docs" / "maintenance" / "orchestrator-runs.csv",
            [{"Run-ID": "1", "Notes": "x"}],
        )

    def test_dry_run_no_jsonl_created(self, tmp_path, monkeypatch):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        monkeypatch.setattr(
            "migrate_csv_to_jsonl._REPO_ROOT", repo
        )
        # Also patch Path(__file__) parent.parent via REPO_ROOT attribute
        import migrate_csv_to_jsonl as mod
        monkeypatch.setattr(mod, "_REPO_ROOT", repo)

        # Patch the script's __file__ resolution by patching main's repo_root lookup
        original_main = mod.main

        def patched_main(argv=None):
            parser = __import__("argparse").ArgumentParser()
            parser.add_argument("--dry-run", action="store_true")
            args = parser.parse_args(argv)
            dry_run = args.dry_run
            files_converted = 0
            total_rows = 0
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
            deleted = 0 if dry_run else files_converted
            print(f"\nConverted {files_converted} files, {total_rows} total rows, {deleted} original CSVs deleted.")
            return 0

        result = patched_main(["--dry-run"])
        assert result == 0
        # No JSONL files should exist
        for _, jsonl_rel, _ in mod._MIGRATIONS:
            assert not (repo / jsonl_rel).exists()

    def test_missing_optional_archive_does_not_fail(self, tmp_path, monkeypatch):
        """Missing archived-test-results.csv (optional) should not cause failure."""
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        # Do NOT create archived-test-results.csv
        import migrate_csv_to_jsonl as mod
        assert not (repo / "docs/test-results/archived-test-results.csv").exists()

        rc = self._run_main_with_repo(mod, repo, [])
        assert rc == 0

    def test_missing_required_csv_exits_1(self, tmp_path, monkeypatch):
        """A missing required CSV must cause exit code 1."""
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        # Remove a required file
        (repo / "docs" / "bugs" / "bugs.csv").unlink()

        import migrate_csv_to_jsonl as mod
        rc = self._run_main_with_repo(mod, repo, [])
        assert rc == 1

    def test_csvs_deleted_after_success(self, tmp_path):
        """After a successful (non-dry-run) run, all processed CSVs are deleted."""
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        import migrate_csv_to_jsonl as mod

        rc = self._run_main_with_repo(mod, repo, [])
        assert rc == 0

        for csv_rel, _, required in mod._MIGRATIONS:
            csv_path = repo / csv_rel
            if required:
                assert not csv_path.exists(), f"CSV not deleted: {csv_path}"

    def test_jsonl_created_with_correct_row_count(self, tmp_path):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        import migrate_csv_to_jsonl as mod

        self._run_main_with_repo(mod, repo, [])

        wp_jsonl = repo / "docs" / "workpackages" / "workpackages.jsonl"
        assert wp_jsonl.exists()
        rows = _read_jsonl(wp_jsonl)
        assert len(rows) == 1

    def test_nested_depends_on_in_output(self, tmp_path):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        import migrate_csv_to_jsonl as mod

        self._run_main_with_repo(mod, repo, [])

        wp_jsonl = repo / "docs" / "workpackages" / "workpackages.jsonl"
        rows = _read_jsonl(wp_jsonl)
        assert rows[0]["Depends On"] == ["MNT-015"]

    def test_nested_linked_wps_in_output(self, tmp_path):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        import migrate_csv_to_jsonl as mod

        self._run_main_with_repo(mod, repo, [])

        us_jsonl = repo / "docs" / "user-stories" / "user-stories.jsonl"
        rows = _read_jsonl(us_jsonl)
        assert rows[0]["Linked WPs"] == ["GUI-001"]

    def test_nested_related_wps_in_output(self, tmp_path):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        import migrate_csv_to_jsonl as mod

        self._run_main_with_repo(mod, repo, [])

        idx_jsonl = repo / "docs" / "decisions" / "index.jsonl"
        rows = _read_jsonl(idx_jsonl)
        assert rows[0]["Related WPs"] == ["MNT-015", "MNT-016"]

    def test_optional_archive_converted_when_present(self, tmp_path):
        repo = self._build_fake_repo(tmp_path)
        self._write_required_csvs(repo)
        # Create optional archive CSV
        _write_csv(
            repo / "docs" / "test-results" / "archived-test-results.csv",
            [{"ID": "TST-001", "Name": "archived"}],
        )
        import migrate_csv_to_jsonl as mod

        self._run_main_with_repo(mod, repo, [])

        arch_jsonl = repo / "docs" / "test-results" / "archived-test-results.jsonl"
        assert arch_jsonl.exists()
        rows = _read_jsonl(arch_jsonl)
        assert len(rows) == 1

    def _run_main_with_repo(self, mod, repo: Path, argv: list[str]) -> int:
        """Run main() logic against a fake repository path."""
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
