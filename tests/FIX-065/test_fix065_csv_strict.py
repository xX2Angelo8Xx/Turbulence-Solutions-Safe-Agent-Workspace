"""Tests for FIX-065: CSV strict parsing and write-time integrity.

Tests cover:
  1. read_csv(strict=True) raises ValueError on overflow columns
  2. read_csv(strict=False) merges overflow (backward compat)
  3. write_csv() atomic write works for valid data
  4. write_csv() rejects data with bare newlines in field values
  5. _check_jsonl_structural() catches invalid enum values
"""

import os
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from csv_utils import read_csv, write_csv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_raw(path: Path, content: str) -> None:
    """Write raw text to a file (bypassing write_csv to create test fixtures)."""
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: read_csv strict=True raises on overflow
# ---------------------------------------------------------------------------

class TestReadCsvStrict:
    def test_overflow_raises_valueerror(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "overflow.csv"
        # 3-column header but row has 4 fields (unquoted extra comma)
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open","EXTRA"
        ''')
        with pytest.raises(ValueError, match="overflow columns detected"):
            read_csv(csv_file, strict=True)

    def test_overflow_error_mentions_row_id(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "overflow2.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "XYZ","Bob","Open","EXTRA"
        ''')
        with pytest.raises(ValueError, match="ID=XYZ"):
            read_csv(csv_file, strict=True)

    def test_strict_default_is_true(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "overflow3.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open","EXTRA"
        ''')
        # No explicit strict arg — should still raise
        with pytest.raises(ValueError, match="overflow"):
            read_csv(csv_file)

    def test_clean_csv_passes_strict(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "clean.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open"
            "002","Bob","Done"
        ''')
        fields, rows = read_csv(csv_file, strict=True)
        assert len(rows) == 2
        assert rows[0]["ID"] == "001"


# ---------------------------------------------------------------------------
# Test 2: read_csv strict=False merges overflow (backward compat)
# ---------------------------------------------------------------------------

class TestReadCsvNonStrict:
    def test_overflow_merged_into_last_field(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "overflow.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open","EXTRA"
        ''')
        fields, rows = read_csv(csv_file, strict=False)
        assert len(rows) == 1
        # EXTRA should be merged into Status
        assert "EXTRA" in rows[0]["Status"]

    def test_multiple_overflow_merged(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "overflow2.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open","EX1","EX2"
        ''')
        fields, rows = read_csv(csv_file, strict=False)
        assert "EX1" in rows[0]["Status"]
        assert "EX2" in rows[0]["Status"]


# ---------------------------------------------------------------------------
# Test 3: write_csv atomic write works for valid data
# ---------------------------------------------------------------------------

class TestWriteCsvAtomic:
    def test_valid_write_creates_file(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "out.csv"
        fields = ["ID", "Name", "Status"]
        rows = [
            {"ID": "001", "Name": "Alice", "Status": "Open"},
            {"ID": "002", "Name": "Bob", "Status": "Done"},
        ]
        write_csv(csv_file, fields, rows)
        assert csv_file.exists()
        # Re-read and verify
        f, r = read_csv(csv_file, strict=True)
        assert len(r) == 2
        assert r[0]["Name"] == "Alice"

    def test_no_temp_file_left_on_success(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "out.csv"
        fields = ["ID", "Name"]
        rows = [{"ID": "001", "Name": "Test"}]
        write_csv(csv_file, fields, rows)
        tmp_file = csv_file.with_suffix(csv_file.suffix + ".tmp")
        assert not tmp_file.exists()

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "out.csv"
        fields = ["ID", "Name"]
        write_csv(csv_file, fields, [{"ID": "001", "Name": "Old"}])
        write_csv(csv_file, fields, [{"ID": "002", "Name": "New"}])
        _, rows = read_csv(csv_file, strict=True)
        assert len(rows) == 1
        assert rows[0]["ID"] == "002"


# ---------------------------------------------------------------------------
# Test 4: write_csv rejects bare newlines in field values
# ---------------------------------------------------------------------------

class TestWriteCsvSanitization:
    def test_bare_newline_raises_valueerror(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "bad.csv"
        fields = ["ID", "Desc"]
        rows = [{"ID": "001", "Desc": "line1\nline2"}]
        with pytest.raises(ValueError, match="bare newline"):
            write_csv(csv_file, fields, rows)

    def test_bare_cr_raises_valueerror(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "bad_cr.csv"
        fields = ["ID", "Desc"]
        rows = [{"ID": "001", "Desc": "line1\rline2"}]
        with pytest.raises(ValueError, match="bare newline"):
            write_csv(csv_file, fields, rows)

    def test_no_temp_file_left_on_sanitization_failure(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "bad2.csv"
        fields = ["ID", "Desc"]
        rows = [{"ID": "001", "Desc": "bad\nvalue"}]
        with pytest.raises(ValueError):
            write_csv(csv_file, fields, rows)
        tmp_file = csv_file.with_suffix(csv_file.suffix + ".tmp")
        assert not tmp_file.exists()

    def test_error_identifies_field_and_row(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "bad3.csv"
        fields = ["ID", "Comment"]
        rows = [
            {"ID": "AAA", "Comment": "ok"},
            {"ID": "BBB", "Comment": "has\nnewline"},
        ]
        with pytest.raises(ValueError, match=r"ID=BBB.*field 'Comment'"):
            write_csv(csv_file, fields, rows)


# ---------------------------------------------------------------------------
# Test 5: _check_jsonl_structural catches invalid enum values
# ---------------------------------------------------------------------------

class TestCheckJsonlStructural:
    def _make_jsonl(self, tmp_path: Path, name: str, rows: list) -> Path:
        import json as _json
        p = tmp_path / name
        p.write_text("\n".join(_json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return p

    def test_valid_enums_no_errors(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        wp = self._make_jsonl(tmp_path, "workpackages.jsonl",
            [{"ID": "WP-001", "Category": "FIX", "Name": "Test", "Status": "Open"}])
        us = self._make_jsonl(tmp_path, "user-stories.jsonl",
            [{"ID": "US-001", "Title": "Story", "Status": "Open"}])
        bug = self._make_jsonl(tmp_path, "bugs.jsonl",
            [{"ID": "BUG-001", "Title": "Bug", "Status": "Open"}])
        tst = self._make_jsonl(tmp_path, "test-results.jsonl",
            [{"ID": "TST-001", "Test Name": "test", "Status": "Pass", "WP Reference": "WP-001"}])

        monkeypatch.setattr(vw, "WP_JSONL", wp)
        monkeypatch.setattr(vw, "US_JSONL", us)
        monkeypatch.setattr(vw, "BUG_JSONL", bug)
        monkeypatch.setattr(vw, "TST_JSONL", tst)

        result = vw.ValidationResult()
        vw._check_jsonl_structural(result)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_invalid_wp_status_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        wp = self._make_jsonl(tmp_path, "workpackages.jsonl",
            [{"ID": "WP-001", "Status": "INVALID"}])
        us = self._make_jsonl(tmp_path, "user-stories.jsonl",
            [{"ID": "US-001", "Status": "Open"}])
        bug = self._make_jsonl(tmp_path, "bugs.jsonl",
            [{"ID": "BUG-001", "Status": "Open"}])
        tst = self._make_jsonl(tmp_path, "test-results.jsonl",
            [{"ID": "TST-001", "Status": "Pass", "WP Reference": "WP-001"}])

        monkeypatch.setattr(vw, "WP_JSONL", wp)
        monkeypatch.setattr(vw, "US_JSONL", us)
        monkeypatch.setattr(vw, "BUG_JSONL", bug)
        monkeypatch.setattr(vw, "TST_JSONL", tst)

        result = vw.ValidationResult()
        vw._check_jsonl_structural(result)
        assert result.ok  # enum issues are warnings, not errors
        assert any("INVALID" in w and "WP-001" in w for w in result.warnings)

    def test_invalid_bug_status_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        wp = self._make_jsonl(tmp_path, "workpackages.jsonl",
            [{"ID": "WP-001", "Status": "Open"}])
        us = self._make_jsonl(tmp_path, "user-stories.jsonl",
            [{"ID": "US-001", "Status": "Open"}])
        bug = self._make_jsonl(tmp_path, "bugs.jsonl",
            [{"ID": "BUG-001", "Status": "BadStatus"}])
        tst = self._make_jsonl(tmp_path, "test-results.jsonl",
            [{"ID": "TST-001", "Status": "Pass", "WP Reference": "WP-001"}])

        monkeypatch.setattr(vw, "WP_JSONL", wp)
        monkeypatch.setattr(vw, "US_JSONL", us)
        monkeypatch.setattr(vw, "BUG_JSONL", bug)
        monkeypatch.setattr(vw, "TST_JSONL", tst)

        result = vw.ValidationResult()
        vw._check_jsonl_structural(result)
        assert result.ok  # enum issues are warnings, not errors
        assert any("BadStatus" in w and "BUG-001" in w for w in result.warnings)

    def test_invalid_json_line_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        # WP JSONL with an invalid JSON line (structural error)
        wp = tmp_path / "workpackages.jsonl"
        wp.write_text(
            '{"ID": "WP-001", "Status": "Open"}\n'
            'NOT_VALID_JSON\n',
            encoding="utf-8",
        )
        us = self._make_jsonl(tmp_path, "user-stories.jsonl",
            [{"ID": "US-001", "Status": "Open"}])
        bug = self._make_jsonl(tmp_path, "bugs.jsonl",
            [{"ID": "BUG-001", "Status": "Open"}])
        tst = self._make_jsonl(tmp_path, "test-results.jsonl",
            [{"ID": "TST-001", "Status": "Pass", "WP Reference": "WP-001"}])

        monkeypatch.setattr(vw, "WP_JSONL", wp)
        monkeypatch.setattr(vw, "US_JSONL", us)
        monkeypatch.setattr(vw, "BUG_JSONL", bug)
        monkeypatch.setattr(vw, "TST_JSONL", tst)

        result = vw.ValidationResult()
        vw._check_jsonl_structural(result)
        assert not result.ok
        assert any("structural error" in e for e in result.errors)
