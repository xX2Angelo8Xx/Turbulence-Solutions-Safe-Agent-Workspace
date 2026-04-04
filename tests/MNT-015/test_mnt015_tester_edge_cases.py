"""Tester edge-case tests for scripts/jsonl_utils.py — MNT-015.

Covers attack vectors, boundary conditions, race conditions, and
platform-specific quirks not addressed by the developer's baseline tests.
"""

import json
import os
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from jsonl_utils import (
    FileLock,
    append_row,
    locked_next_id_and_append,
    next_id,
    read_jsonl,
    update_cell,
    write_jsonl,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jsonl(path: Path, rows: list[dict]) -> None:
    content = "\n".join(json.dumps(r) for r in rows) + "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# read_jsonl — edge cases
# ---------------------------------------------------------------------------

def test_read_crlf_line_endings(tmp_path):
    """read_jsonl handles Windows CRLF line endings transparently."""
    f = tmp_path / "data.jsonl"
    content = '{"ID": "X-001", "Name": "Alpha"}\r\n{"ID": "X-002", "Name": "Beta"}\r\n'
    f.write_bytes(content.encode("utf-8"))
    _, rows = read_jsonl(f)
    assert len(rows) == 2
    assert rows[0]["Name"] == "Alpha"
    assert rows[1]["Name"] == "Beta"


def test_read_bom_raises_value_error(tmp_path):
    """read_jsonl raises ValueError on a UTF-8 BOM (spec requires no BOM).

    csv_utils uses 'utf-8-sig' to strip BOM; jsonl_utils uses plain 'utf-8'
    intentionally, because JSONL files must be written without BOM.
    A BOM-prefixed file indicates a provenance error — fail loudly.
    """
    f = tmp_path / "data.jsonl"
    # \ufeff is the Unicode BOM; encode to utf-8 produces the 3-byte BOM sequence
    content = "\ufeff" + '{"ID": "X-001"}\n'
    f.write_bytes(content.encode("utf-8"))
    with pytest.raises(ValueError, match="invalid JSON"):
        read_jsonl(f)


def test_read_whitespace_only_lines_skipped(tmp_path):
    """Lines containing only spaces and tabs are treated as blank and skipped."""
    f = tmp_path / "data.jsonl"
    content = '{"ID": "X-001"}\n   \n\t\n{"ID": "X-002"}\n'
    f.write_text(content, encoding="utf-8")
    _, rows = read_jsonl(f)
    assert len(rows) == 2
    assert rows[0]["ID"] == "X-001"
    assert rows[1]["ID"] == "X-002"


def test_read_expected_fields_checks_first_row_schema(tmp_path):
    """expected_fields validation is based on the first row's keys only.

    A field present in later rows but absent from the first row will still
    trigger a ValueError — fieldnames derive from the first non-empty line.
    """
    f = tmp_path / "data.jsonl"
    content = '{"ID": "X-001"}\n{"ID": "X-002", "Status": "Open"}\n'
    f.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="missing expected fields"):
        read_jsonl(f, expected_fields=["Status"])


def test_read_special_characters_in_value(tmp_path):
    """Values containing HTML/JSON special characters survive a round-trip."""
    f = tmp_path / "data.jsonl"
    special = '<script>alert("xss")</script> & "quote" \\ backslash'
    _make_jsonl(f, [{"ID": "X-001", "Payload": special}])
    _, rows = read_jsonl(f)
    assert rows[0]["Payload"] == special


# ---------------------------------------------------------------------------
# write_jsonl — edge cases
# ---------------------------------------------------------------------------

def test_write_no_bom(tmp_path):
    """write_jsonl produces UTF-8 without BOM (spec requirement)."""
    f = tmp_path / "out.jsonl"
    write_jsonl(f, ["ID", "Name"], [{"ID": "X-001", "Name": "Alpha"}])
    raw = f.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "output must not have a UTF-8 BOM"


def test_write_cleans_tmp_on_replace_failure(tmp_path):
    """write_jsonl removes the .tmp file when os.replace raises."""
    f = tmp_path / "out.jsonl"
    with patch("os.replace", side_effect=OSError("simulated disk full")):
        with pytest.raises(OSError, match="simulated disk full"):
            write_jsonl(f, ["ID"], [{"ID": "X-001"}])
    tmp = f.with_suffix(".jsonl.tmp")
    assert not tmp.exists(), ".tmp file must be cleaned up on failure"


def test_write_embedded_newline_in_value(tmp_path):
    """Values with embedded newlines are JSON-escaped, not raw line breaks.

    The resulting JSONL file must have exactly one data line per row,
    and the value must survive the round-trip intact.
    """
    f = tmp_path / "out.jsonl"
    rows = [{"ID": "X-001", "Notes": "line1\nline2\nline3"}]
    write_jsonl(f, ["ID", "Notes"], rows)

    # The file must contain exactly one non-empty line (one JSON object)
    non_empty = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(non_empty) == 1, "embedded newline must not produce extra lines"

    # Value must survive the round-trip
    _, read_rows = read_jsonl(f)
    assert read_rows[0]["Notes"] == "line1\nline2\nline3"


def test_write_extra_keys_appended_after_fieldnames(tmp_path):
    """Keys not in fieldnames are appended to the JSON object after declared fields."""
    f = tmp_path / "out.jsonl"
    rows = [{"ID": "X-001", "Name": "Alpha", "Extra": "bonus"}]
    write_jsonl(f, ["ID", "Name"], rows)  # "Extra" not in fieldnames
    line = f.read_text(encoding="utf-8").strip()
    obj = json.loads(line)
    keys = list(obj.keys())
    assert keys[:2] == ["ID", "Name"], "fieldnames order must come first"
    assert "Extra" in keys, "extra keys must still be written"


# ---------------------------------------------------------------------------
# append_row — edge cases
# ---------------------------------------------------------------------------

def test_append_row_nonexistent_file_raises(tmp_path):
    """append_row raises FileNotFoundError when the target file does not exist."""
    f = tmp_path / "nonexistent.jsonl"
    with pytest.raises(FileNotFoundError):
        append_row(f, ["ID", "Name"], {"ID": "X-001", "Name": "Alpha"})


def test_append_row_empty_id_first_row_allowed(tmp_path):
    """append_row allows a row with empty-string ID when file is empty."""
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    result = append_row(f, ["ID", "Name"], {"ID": "", "Name": "NoId"})
    assert result == ""
    _, rows = read_jsonl(f)
    assert len(rows) == 1


def test_append_row_empty_id_duplicate_raises(tmp_path):
    """append_row rejects a second row with empty-string ID (duplicate key check)."""
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "", "Name": "First"}])
    with pytest.raises(ValueError, match="Duplicate ID"):
        append_row(f, ["ID", "Name"], {"ID": "", "Name": "Second"})


# ---------------------------------------------------------------------------
# update_cell — edge cases
# ---------------------------------------------------------------------------

def test_update_cell_updates_first_match_only(tmp_path):
    """update_cell stops at the first matching row when duplicate IDs exist.

    Duplicate IDs are a data integrity problem, but the function must not
    corrupt adjacent rows or raise unexpectedly in that case.
    """
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"ID": "X-001", "Status": "Open"},
        {"ID": "X-001", "Status": "Pending"},  # intentional duplicate
    ])
    update_cell(f, "ID", "X-001", "Status", "Done")
    _, rows = read_jsonl(f)
    assert rows[0]["Status"] == "Done"
    assert rows[1]["Status"] == "Pending"  # second row must be untouched


# ---------------------------------------------------------------------------
# next_id — edge cases
# ---------------------------------------------------------------------------

def test_next_id_ignores_malformed_ids(tmp_path):
    """next_id skips rows where the ID does not match the PREFIX-NNN pattern."""
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"ID": "TST-abc", "Name": "Non-numeric suffix"},
        {"ID": "TST-", "Name": "Missing number"},
        {"ID": "TST", "Name": "No separator"},
        {"ID": "TST-005", "Name": "Valid"},
    ])
    result = next_id(f, "TST")
    assert result == "TST-006"


def test_next_id_custom_id_column(tmp_path):
    """next_id works with a non-default id_column parameter."""
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"Ref": "BUG-001", "Title": "First bug"},
        {"Ref": "BUG-007", "Title": "Seventh bug"},
    ])
    result = next_id(f, "BUG", id_column="Ref")
    assert result == "BUG-008"


def test_next_id_large_number_no_overflow(tmp_path):
    """next_id handles IDs with numbers larger than the zero_pad width."""
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "TST-9999", "Name": "Large"}])
    result = next_id(f, "TST", zero_pad=3)
    assert result == "TST-10000"  # must not truncate/overflow zero-pad


# ---------------------------------------------------------------------------
# locked_next_id_and_append — edge cases
# ---------------------------------------------------------------------------

def test_locked_next_id_mutates_template(tmp_path):
    """locked_next_id_and_append sets the ID field directly in row_template.

    Callers must be aware that their dict is mutated in-place.
    """
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    template = {"Name": "Test"}
    new_id = locked_next_id_and_append(f, "TST", template)
    assert template["ID"] == new_id == "TST-001"


def test_locked_next_id_nonexistent_file_raises(tmp_path):
    """locked_next_id_and_append raises FileNotFoundError when file is absent."""
    f = tmp_path / "gone.jsonl"
    with pytest.raises(FileNotFoundError):
        locked_next_id_and_append(f, "TST", {"Name": "Test"})


def test_locked_next_id_concurrent_threads(tmp_path):
    """10 concurrent locked_next_id_and_append calls produce 10 unique IDs.

    Validates that FileLock prevents race conditions under real thread
    concurrency on the local filesystem.
    """
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")

    results: list[str] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker():
        try:
            new_id = locked_next_id_and_append(f, "TST", {"Name": "concurrent"})
            with lock:
                results.append(new_id)
        except Exception as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected errors during concurrent writes: {errors}"
    assert len(results) == 10
    assert len(set(results)) == 10, f"Duplicate IDs detected: {sorted(results)}"

    # Verify the file has exactly 10 rows with sequential IDs
    _, rows = read_jsonl(f)
    assert len(rows) == 10
    ids = {r["ID"] for r in rows}
    expected = {f"TST-{n:03d}" for n in range(1, 11)}
    assert ids == expected


# ---------------------------------------------------------------------------
# FileLock — edge cases
# ---------------------------------------------------------------------------

def test_filelock_pid_written_to_lock_file(tmp_path):
    """The lock file contains the owning process's PID as a plain string."""
    f = tmp_path / "data.jsonl"
    lock = FileLock(f)
    with lock:
        pid_str = lock.lock_path.read_text(encoding="utf-8")
        assert pid_str == str(os.getpid())
    assert not lock.lock_path.exists()


def test_filelock_not_stale_below_threshold(tmp_path):
    """A lock file younger than _STALE_THRESHOLD is NOT removed.

    The stale check uses age > _STALE_THRESHOLD. A lock 5 seconds below the
    threshold must still block acquisition and eventually time out.
    """
    f = tmp_path / "data.jsonl"
    lock_path = Path(str(f) + ".lock")
    lock_path.write_text("99999", encoding="utf-8")

    # Set mtime to 5 seconds before the stale threshold so the lock is fresh
    fresh_time = time.time() - (FileLock._STALE_THRESHOLD - 5.0)
    os.utime(str(lock_path), (fresh_time, fresh_time))

    try:
        with pytest.raises(TimeoutError):
            with FileLock(f, timeout=0.3, poll=0.05):
                pass
        # Lock file must still exist — it was not cleaned up as stale
        assert lock_path.exists(), "non-stale lock must not be auto-removed"
    finally:
        lock_path.unlink(missing_ok=True)


def test_filelock_reentrant_deadlock(tmp_path):
    """A single thread cannot re-acquire a FileLock it already holds.

    FileLock is not reentrant — re-entry causes a TimeoutError.
    This is expected behavior that callers must avoid.
    """
    f = tmp_path / "data.jsonl"
    with pytest.raises(TimeoutError):
        with FileLock(f, timeout=0.2, poll=0.05):
            with FileLock(f, timeout=0.2, poll=0.05):  # deadlock
                pass  # pragma: no cover
