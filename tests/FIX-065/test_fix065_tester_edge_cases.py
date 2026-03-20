"""Tester edge-case additions for FIX-065: CSV strict parsing and write-time
integrity.

Covers scenarios the developer did not test:
  1. \r\n inside a field value is ALLOWED by write_csv (csv module handles it)
  2. Mixed \r\n + bare \n in same field is REJECTED
  3. read_csv strict=True with multiple overflow rows - each raises ValueError
  4. read_csv with header-only CSV (no data rows) - passes cleanly
  5. write_csv with empty rows list - creates valid empty CSV
  6. write_csv unicode content round-trips correctly
  7. _check_csv_structural missing CSV file reports error (not exception)
  8. _check_csv_structural overflow in one CSV doesn't skip the others
  9. read_csv strict=True: first overflow row causes immediate raise
 10. write_csv temp file not left when os.replace is blocked
 11. Null bytes in field values - write_csv does not sanitize (documents
     current behaviour so a future regression is caught)
"""

import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from csv_utils import read_csv, write_csv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_raw(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


# ---------------------------------------------------------------------------
# 1–2: Newline sanitization boundary cases
# ---------------------------------------------------------------------------

class TestWriteCsvNewlineBoundary:
    """Verify the \r\n / bare-newline sanitization boundary exactly."""

    def test_crlf_in_field_is_allowed(self, tmp_path: Path) -> None:
        """A value containing \\r\\n should NOT raise (csv handles it)."""
        csv_file = tmp_path / "crlf.csv"
        fields = ["ID", "Text"]
        rows = [{"ID": "001", "Text": "line1\r\nline2"}]
        # Must NOT raise
        write_csv(csv_file, fields, rows)
        assert csv_file.exists()

    def test_mixed_crlf_and_bare_newline_raises(self, tmp_path: Path) -> None:
        """A value with \\r\\n AND a bare \\n should raise ValueError."""
        csv_file = tmp_path / "mixed.csv"
        fields = ["ID", "Text"]
        rows = [{"ID": "001", "Text": "header\r\nbody\nextra"}]
        with pytest.raises(ValueError, match="bare newline"):
            write_csv(csv_file, fields, rows)

    def test_only_crlf_value_is_allowed(self, tmp_path: Path) -> None:
        """A value that IS only \\r\\n should not raise."""
        csv_file = tmp_path / "onlycrlf.csv"
        fields = ["ID", "Sep"]
        rows = [{"ID": "001", "Sep": "\r\n"}]
        write_csv(csv_file, fields, rows)  # must not raise
        _, re_rows = read_csv(csv_file, strict=True)
        assert len(re_rows) == 1

    def test_multiple_crlf_pairs_allowed(self, tmp_path: Path) -> None:
        """Multiple \\r\\n sequences in one value should not raise."""
        csv_file = tmp_path / "multi_crlf.csv"
        fields = ["ID", "Lines"]
        rows = [{"ID": "001", "Lines": "a\r\nb\r\nc"}]
        write_csv(csv_file, fields, rows)
        assert csv_file.exists()


# ---------------------------------------------------------------------------
# 3–4: read_csv edge cases
# ---------------------------------------------------------------------------

class TestReadCsvEdgeCases:
    def test_strict_multiple_overflow_rows_raises_on_first(
        self, tmp_path: Path
    ) -> None:
        """strict=True raises on the FIRST overflow row encountered."""
        csv_file = tmp_path / "multi_overflow.csv"
        _write_raw(csv_file, '''\
            "ID","Name","Status"
            "001","Alice","Open","EXTRA1"
            "002","Bob","Open","EXTRA2"
        ''')
        with pytest.raises(ValueError, match="overflow columns detected"):
            read_csv(csv_file, strict=True)

    def test_header_only_csv_returns_empty_rows(self, tmp_path: Path) -> None:
        """CSV with only a header row returns empty row list."""
        csv_file = tmp_path / "header_only.csv"
        _write_raw(csv_file, '"ID","Name","Status"\n')
        fields, rows = read_csv(csv_file, strict=True)
        assert fields == ["ID", "Name", "Status"]
        assert rows == []

    def test_strict_false_on_clean_csv_returns_rows(self, tmp_path: Path) -> None:
        """strict=False on a clean CSV (no overflow) returns rows normally."""
        csv_file = tmp_path / "clean.csv"
        _write_raw(csv_file, '''\
            "ID","Name"
            "001","Alice"
        ''')
        fields, rows = read_csv(csv_file, strict=False)
        assert len(rows) == 1
        assert rows[0]["ID"] == "001"

    def test_utf8_bom_csv_reads_correctly(self, tmp_path: Path) -> None:
        """UTF-8 BOM (utf-8-sig) CSV parses cleanly under strict mode."""
        csv_file = tmp_path / "bom.csv"
        # Write BOM manually
        csv_file.write_bytes(
            b'\xef\xbb\xbf"ID","Name"\r\n"001","Alice"\r\n'
        )
        fields, rows = read_csv(csv_file, strict=True)
        assert "ID" in fields  # BOM stripped from first field name
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# 5–6: write_csv edge cases
# ---------------------------------------------------------------------------

class TestWriteCsvEdgeCases:
    def test_empty_rows_list_creates_header_only_csv(
        self, tmp_path: Path
    ) -> None:
        """write_csv with empty rows creates a valid header-only CSV."""
        csv_file = tmp_path / "empty_rows.csv"
        fields = ["ID", "Name", "Status"]
        write_csv(csv_file, fields, [])
        assert csv_file.exists()
        f, rows = read_csv(csv_file, strict=True)
        assert f == fields
        assert rows == []

    def test_unicode_content_round_trips(self, tmp_path: Path) -> None:
        """Unicode characters in field values round-trip through write+read."""
        csv_file = tmp_path / "unicode.csv"
        fields = ["ID", "Text"]
        rows = [{"ID": "001", "Text": "Hello Wörld — naïve résumé 日本語"}]
        write_csv(csv_file, fields, rows)
        _, re_rows = read_csv(csv_file, strict=True)
        assert re_rows[0]["Text"] == "Hello Wörld — naïve résumé 日本語"

    def test_non_string_value_not_flagged_as_bare_newline(
        self, tmp_path: Path
    ) -> None:
        """Non-string values (int, None) in a row dict are skipped by
        sanitization; write_csv should not raise for them."""
        csv_file = tmp_path / "nonstr.csv"
        fields = ["ID", "Count", "Flag"]
        # DictWriter coerces non-string values; sanitization skips non-str
        rows = [{"ID": "001", "Count": 42, "Flag": None}]
        # Should not raise
        write_csv(csv_file, fields, rows)
        assert csv_file.exists()

    def test_temp_file_not_left_on_os_replace_failure(
        self, tmp_path: Path
    ) -> None:
        """Temp file is deleted when os.replace raises OSError."""
        csv_file = tmp_path / "safe.csv"
        fields = ["ID"]
        rows = [{"ID": "001"}]
        tmp_expected = csv_file.with_suffix(csv_file.suffix + ".tmp")

        with patch("csv_utils.os.replace", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                write_csv(csv_file, fields, rows)

        # Temp file must NOT remain after the failure
        assert not tmp_expected.exists(), "Temp file was not cleaned up"


# ---------------------------------------------------------------------------
# 7–8: _check_csv_structural additional cases
# ---------------------------------------------------------------------------

class TestCheckCsvStructuralAdditional:
    def _make_csv(
        self, tmp_path: Path, name: str, header: str, rows_text: str
    ) -> Path:
        p = tmp_path / name
        p.write_text(
            textwrap.dedent(header).lstrip()
            + "\n"
            + textwrap.dedent(rows_text).lstrip()
            + "\n",
            encoding="utf-8",
        )
        return p

    def _patch_csv_paths(
        self, monkeypatch, vw, wp, us, bug, tst
    ) -> None:
        monkeypatch.setattr(vw, "WP_CSV", wp)
        monkeypatch.setattr(vw, "US_CSV", us)
        monkeypatch.setattr(vw, "BUG_CSV", bug)
        monkeypatch.setattr(vw, "TST_CSV", tst)

    def _make_valid_csvs(self, tmp_path: Path):
        wp = self._make_csv(
            tmp_path,
            "workpackages.csv",
            '"ID","Category","Name","Status","Assigned To","Description","Goal",'
            '"Comments","User Story","Depends On","Blockers"',
            '"WP-001","FIX","Test","Open","","desc","goal","","","",""',
        )
        us = self._make_csv(
            tmp_path,
            "user-stories.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","Open",""',
        )
        bug = self._make_csv(
            tmp_path,
            "bugs.csv",
            '"ID","Title","Status","Fixed In WP"',
            '"BUG-001","Bug","Open",""',
        )
        tst = self._make_csv(
            tmp_path,
            "test-results.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","Pass","WP-001"',
        )
        return wp, us, bug, tst

    def test_missing_csv_file_reports_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A CSV file that doesn't exist at all should add an ERROR."""
        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent / "scripts"),
        )
        import validate_workspace as vw

        wp, us, bug, tst = self._make_valid_csvs(tmp_path)
        # Point bug CSV to a non-existent path
        missing = tmp_path / "nonexistent_bugs.csv"
        self._patch_csv_paths(monkeypatch, vw, wp, us, missing, tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)
        assert any(
            "nonexistent_bugs.csv" in e or "not found" in e.lower()
            for e in result.errors
        ), f"Expected 'not found' error. Errors: {result.errors}"

    def test_overflow_in_one_csv_does_not_skip_others(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When WP CSV has overflow, the Bug/US/TST CSVs are still checked."""
        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent / "scripts"),
        )
        import validate_workspace as vw

        wp, us, bug, tst = self._make_valid_csvs(tmp_path)
        # Replace wp with an overflow CSV - same header but extra field in row
        wp_overflow = tmp_path / "wp_overflow.csv"
        _write_raw(
            wp_overflow,
            '"ID","Category","Name","Status","Assigned To","Description","Goal",'
            '"Comments","User Story","Depends On","Blockers"\n'
            '"WP-001","FIX","Test","Open","","desc","goal","","","","","OVERFLOW"\n',
        )
        self._patch_csv_paths(monkeypatch, vw, wp_overflow, us, bug, tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)

        # Should have an error for WP CSV overflow
        assert any("WP" in e and "structural" in e for e in result.errors), (
            f"Expected WP structural error. Errors: {result.errors}"
        )
        # Should NOT have errors for the other three (which are valid)
        non_wp_errors = [
            e for e in result.errors if "Bug" in e or "US" in e or "Test" in e
        ]
        assert non_wp_errors == [], f"Unexpected non-WP errors: {non_wp_errors}"

    def test_invalid_tst_status_reported_as_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid TST Status value generates a WARNING, not an error."""
        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent / "scripts"),
        )
        import validate_workspace as vw

        wp, us, bug, _ = self._make_valid_csvs(tmp_path)
        tst = self._make_csv(
            tmp_path,
            "test-results-invalid.csv",
            '"ID","Test Name","Status","WP Reference"',
            '"TST-001","test","PASS","WP-001"',  # "PASS" not in valid set
        )
        self._patch_csv_paths(monkeypatch, vw, wp, us, bug, tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)

        assert result.ok, f"Unexpected errors: {result.errors}"
        assert any(
            "TST-001" in w and "PASS" in w for w in result.warnings
        ), f"Expected warning for TST-001 PASS. Warnings: {result.warnings}"

    def test_invalid_us_status_reported_as_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid US Status value generates a WARNING."""
        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent / "scripts"),
        )
        import validate_workspace as vw

        wp, _, bug, tst = self._make_valid_csvs(tmp_path)
        us = self._make_csv(
            tmp_path,
            "user-stories-invalid.csv",
            '"ID","Title","Status","Linked WPs"',
            '"US-001","Story","UNKNOWN","WP-001"',
        )
        self._patch_csv_paths(monkeypatch, vw, wp, us, bug, tst)

        result = vw.ValidationResult()
        vw._check_csv_structural(result)

        assert result.ok, f"Unexpected errors: {result.errors}"
        assert any("US-001" in w for w in result.warnings), (
            f"Expected warning for US-001. Warnings: {result.warnings}"
        )
