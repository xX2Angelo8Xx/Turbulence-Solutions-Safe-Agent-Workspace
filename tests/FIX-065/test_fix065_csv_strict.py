"""Tests for FIX-065: CSV strict parsing and write-time integrity.

Tests cover:
  1. read_csv(strict=True) raises ValueError on overflow columns
  2. read_csv(strict=False) merges overflow (backward compat)
  3. write_csv() atomic write works for valid data
  4. write_csv() rejects data with bare newlines in field values
  5. _check_csv_structural() catches invalid enum values
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
# Test 5: _check_csv_structural catches invalid enum values
# ---------------------------------------------------------------------------

class TestCheckCsvStructural:
    def _make_csv(self, tmp_path: Path, name: str, header: str, rows_text: str) -> Path:
        p = tmp_path / name
        _write_raw(p, header + "\n" + rows_text + "\n")
        return p

    def test_valid_enums_no_errors(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        # Create minimal valid CSVs
        wp = self._make_csv(tmp_path, "workpackages.csv",
            '"ID","Category","Name","Status","Assigned To","Description","Goal","Comments","User Story","Depends On","Blockers"',
            '"WP-001","FIX","Test","Open","","desc","goal","","","",""')
        us = self._make_csv(tmp_path, "user-stories.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","Open",""')
        bug = self._make_csv(tmp_path, "bugs.csv",
            '"ID","Title","Status","Fixed In WP"',
            '"BUG-001","Bug","Open",""')
        tst = self._make_csv(tmp_path, "test-results.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","Pass","WP-001"')

        monkeypatch.setattr(vw, "WP_CSV", wp)
        monkeypatch.setattr(vw, "US_CSV", us)
        monkeypatch.setattr(vw, "BUG_CSV", bug)
        monkeypatch.setattr(vw, "TST_CSV", tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)
        assert result.ok, f"Unexpected errors: {result.errors}"

    def test_invalid_wp_status_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        wp = self._make_csv(tmp_path, "workpackages.csv",
            '"ID","Category","Name","Status","Assigned To","Description","Goal","Comments","User Story","Depends On","Blockers"',
            '"WP-001","FIX","Test","INVALID","","desc","goal","","","",""')
        us = self._make_csv(tmp_path, "user-stories.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","Open",""')
        bug = self._make_csv(tmp_path, "bugs.csv",
            '"ID","Title","Status","Fixed In WP"',
            '"BUG-001","Bug","Open",""')
        tst = self._make_csv(tmp_path, "test-results.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","Pass","WP-001"')

        monkeypatch.setattr(vw, "WP_CSV", wp)
        monkeypatch.setattr(vw, "US_CSV", us)
        monkeypatch.setattr(vw, "BUG_CSV", bug)
        monkeypatch.setattr(vw, "TST_CSV", tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)
        assert result.ok  # enum issues are warnings, not errors
        assert any("INVALID" in w and "WP-001" in w for w in result.warnings)

    def test_invalid_bug_status_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        wp = self._make_csv(tmp_path, "workpackages.csv",
            '"ID","Category","Name","Status","Assigned To","Description","Goal","Comments","User Story","Depends On","Blockers"',
            '"WP-001","FIX","Test","Open","","desc","goal","","","",""')
        us = self._make_csv(tmp_path, "user-stories.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","Open",""')
        bug = self._make_csv(tmp_path, "bugs.csv",
            '"ID","Title","Status","Fixed In WP"',
            '"BUG-001","Bug","BadStatus",""')
        tst = self._make_csv(tmp_path, "test-results.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","Pass","WP-001"')

        monkeypatch.setattr(vw, "WP_CSV", wp)
        monkeypatch.setattr(vw, "US_CSV", us)
        monkeypatch.setattr(vw, "BUG_CSV", bug)
        monkeypatch.setattr(vw, "TST_CSV", tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)
        assert result.ok  # enum issues are warnings, not errors
        assert any("BadStatus" in w and "BUG-001" in w for w in result.warnings)

    def test_overflow_csv_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
        import validate_workspace as vw

        # WP CSV with overflow column
        wp = tmp_path / "workpackages.csv"
        _write_raw(wp, '''\
            "ID","Category","Name","Status","Assigned To","Description","Goal","Comments","User Story","Depends On","Blockers"
            "WP-001","FIX","Test","Open","","desc","goal","","","","","EXTRA"
        ''')
        us = self._make_csv(tmp_path, "user-stories.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","Open",""')
        bug = self._make_csv(tmp_path, "bugs.csv",
            '"ID","Title","Status","Fixed In WP"',
            '"BUG-001","Bug","Open",""')
        tst = self._make_csv(tmp_path, "test-results.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","Pass","WP-001"')

        monkeypatch.setattr(vw, "WP_CSV", wp)
        monkeypatch.setattr(vw, "US_CSV", us)
        monkeypatch.setattr(vw, "BUG_CSV", bug)
        monkeypatch.setattr(vw, "TST_CSV", tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)
        assert not result.ok
        assert any("structural error" in e for e in result.errors)
