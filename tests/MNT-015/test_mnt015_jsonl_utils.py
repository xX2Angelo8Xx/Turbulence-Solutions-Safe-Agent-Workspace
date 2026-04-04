"""Unit tests for scripts/jsonl_utils.py — MNT-015."""

import json
import os
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from jsonl_utils import (
    FileLock,
    append_row,
    locked_next_id_and_append,
    next_id,
    read_jsonl,
    update_cell,
    write_jsonl,
    REPO_ROOT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_raw(path: Path, lines: list[str]) -> None:
    """Write raw lines to a file for test setup."""
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _make_jsonl(path: Path, rows: list[dict]) -> None:
    content = "\n".join(json.dumps(r) for r in rows) + "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# REPO_ROOT
# ---------------------------------------------------------------------------

def test_repo_root_is_path():
    assert isinstance(REPO_ROOT, Path)
    assert REPO_ROOT.exists()


# ---------------------------------------------------------------------------
# read_jsonl
# ---------------------------------------------------------------------------

def test_read_empty_file(tmp_path):
    f = tmp_path / "empty.jsonl"
    f.write_text("", encoding="utf-8")
    fieldnames, rows = read_jsonl(f)
    assert fieldnames == []
    assert rows == []


def test_read_single_row(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Name": "Alpha"}])
    fieldnames, rows = read_jsonl(f)
    assert fieldnames == ["ID", "Name"]
    assert len(rows) == 1
    assert rows[0]["ID"] == "X-001"
    assert rows[0]["Name"] == "Alpha"


def test_read_multiple_rows(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"ID": "X-001", "Name": "Alpha"},
        {"ID": "X-002", "Name": "Beta"},
        {"ID": "X-003", "Name": "Gamma"},
    ])
    fieldnames, rows = read_jsonl(f)
    assert fieldnames == ["ID", "Name"]
    assert len(rows) == 3
    assert rows[2]["Name"] == "Gamma"


def test_read_skips_blank_lines(tmp_path):
    f = tmp_path / "data.jsonl"
    _write_raw(f, [
        '{"ID": "X-001", "Name": "Alpha"}',
        "",
        '{"ID": "X-002", "Name": "Beta"}',
        "",
    ])
    _, rows = read_jsonl(f)
    assert len(rows) == 2


def test_read_expected_fields_valid(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Status": "Done"}])
    fieldnames, rows = read_jsonl(f, expected_fields=["ID", "Status"])
    assert len(rows) == 1


def test_read_expected_fields_missing_raises(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001"}])
    with pytest.raises(ValueError, match="missing expected fields"):
        read_jsonl(f, expected_fields=["ID", "Status"])


def test_read_invalid_json_raises(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"ID": "X-001"}\nNOT_JSON\n', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        read_jsonl(f)


def test_read_non_object_json_raises(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('["a", "b"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="expected a JSON object"):
        read_jsonl(f)


# ---------------------------------------------------------------------------
# write_jsonl
# ---------------------------------------------------------------------------

def test_write_creates_file(tmp_path):
    f = tmp_path / "out.jsonl"
    rows = [{"ID": "X-001", "Name": "Alpha"}, {"ID": "X-002", "Name": "Beta"}]
    write_jsonl(f, ["ID", "Name"], rows)
    assert f.exists()
    _, read_rows = read_jsonl(f)
    assert len(read_rows) == 2
    assert read_rows[0]["ID"] == "X-001"
    assert read_rows[1]["Name"] == "Beta"


def test_write_empty_rows(tmp_path):
    f = tmp_path / "out.jsonl"
    write_jsonl(f, ["ID", "Name"], [])
    assert f.exists()
    _, rows = read_jsonl(f)
    assert rows == []


def test_write_field_order_follows_fieldnames(tmp_path):
    f = tmp_path / "out.jsonl"
    rows = [{"Name": "Alpha", "ID": "X-001", "Status": "Open"}]
    write_jsonl(f, ["ID", "Name", "Status"], rows)
    first_line = f.read_text(encoding="utf-8").splitlines()[0]
    obj = json.loads(first_line)
    keys = list(obj.keys())
    assert keys == ["ID", "Name", "Status"]


def test_write_no_temp_file_on_success(tmp_path):
    f = tmp_path / "out.jsonl"
    write_jsonl(f, ["ID"], [{"ID": "X-001"}])
    tmp = f.with_suffix(".jsonl.tmp")
    assert not tmp.exists()


def test_write_unicode_content(tmp_path):
    f = tmp_path / "out.jsonl"
    rows = [{"ID": "X-001", "Name": "Ångström — ñ — 中文"}]
    write_jsonl(f, ["ID", "Name"], rows)
    _, read_rows = read_jsonl(f)
    assert read_rows[0]["Name"] == "Ångström — ñ — 中文"


# ---------------------------------------------------------------------------
# append_row
# ---------------------------------------------------------------------------

def test_append_row_to_existing(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Name": "Alpha"}])
    append_row(f, ["ID", "Name"], {"ID": "X-002", "Name": "Beta"})
    _, rows = read_jsonl(f)
    assert len(rows) == 2
    assert rows[1]["ID"] == "X-002"


def test_append_row_to_empty_file(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    append_row(f, ["ID", "Name"], {"ID": "X-001", "Name": "Alpha"})
    _, rows = read_jsonl(f)
    assert len(rows) == 1
    assert rows[0]["ID"] == "X-001"


def test_append_row_duplicate_id_raises(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Name": "Alpha"}])
    with pytest.raises(ValueError, match="Duplicate ID"):
        append_row(f, ["ID", "Name"], {"ID": "X-001", "Name": "Duplicate"})


def test_append_row_fills_missing_fields(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Name": "Alpha", "Status": "Open"}])
    append_row(f, ["ID", "Name", "Status"], {"ID": "X-002", "Name": "Beta"})
    _, rows = read_jsonl(f)
    assert rows[1].get("Status") == ""


def test_append_row_returns_id(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    result = append_row(f, ["ID", "Name"], {"ID": "X-042", "Name": "Test"})
    assert result == "X-042"


# ---------------------------------------------------------------------------
# update_cell
# ---------------------------------------------------------------------------

def test_update_cell_existing_row(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"ID": "X-001", "Status": "Open"},
        {"ID": "X-002", "Status": "Open"},
    ])
    update_cell(f, "ID", "X-001", "Status", "Done")
    _, rows = read_jsonl(f)
    status_map = {r["ID"]: r["Status"] for r in rows}
    assert status_map["X-001"] == "Done"
    assert status_map["X-002"] == "Open"


def test_update_cell_missing_id_raises(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Status": "Open"}])
    with pytest.raises(KeyError, match="No row with"):
        update_cell(f, "ID", "X-999", "Status", "Done")


def test_update_cell_missing_column_raises(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "X-001", "Status": "Open"}])
    with pytest.raises(KeyError, match="not in"):
        update_cell(f, "ID", "X-001", "NonExistentColumn", "value")


# ---------------------------------------------------------------------------
# next_id
# ---------------------------------------------------------------------------

def test_next_id_empty_file(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    result = next_id(f, "TST")
    assert result == "TST-001"


def test_next_id_with_existing_rows(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [
        {"ID": "TST-001", "Name": "A"},
        {"ID": "TST-002", "Name": "B"},
        {"ID": "TST-005", "Name": "C"},
    ])
    result = next_id(f, "TST")
    assert result == "TST-006"


def test_next_id_different_prefix_ignored(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "BUG-010", "Name": "A"}])
    result = next_id(f, "TST")
    assert result == "TST-001"


def test_next_id_zero_pad_zero(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    result = next_id(f, "X", zero_pad=0)
    assert result == "X-1"


# ---------------------------------------------------------------------------
# locked_next_id_and_append
# ---------------------------------------------------------------------------

def test_locked_next_id_and_append_empty_file(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    new_id = locked_next_id_and_append(f, "TST", {"Name": "First"})
    assert new_id == "TST-001"
    _, rows = read_jsonl(f)
    assert len(rows) == 1
    assert rows[0]["ID"] == "TST-001"
    assert rows[0]["Name"] == "First"


def test_locked_next_id_and_append_sequential(tmp_path):
    f = tmp_path / "data.jsonl"
    _make_jsonl(f, [{"ID": "TST-003", "Name": "Existing"}])
    new_id = locked_next_id_and_append(f, "TST", {"Name": "New"})
    assert new_id == "TST-004"
    _, rows = read_jsonl(f)
    assert len(rows) == 2


def test_locked_next_id_returns_id_string(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    result = locked_next_id_and_append(f, "BUG", {"Name": "Bug A"})
    assert result == "BUG-001"


# ---------------------------------------------------------------------------
# FileLock
# ---------------------------------------------------------------------------

def test_filelock_acquires_and_releases(tmp_path):
    f = tmp_path / "data.jsonl"
    lock = FileLock(f)
    with lock:
        assert lock.lock_path.exists()
    assert not lock.lock_path.exists()


def test_filelock_timeout(tmp_path):
    f = tmp_path / "data.jsonl"
    lock_path = Path(str(f) + ".lock")
    # Manually create the lock file to simulate a competing process
    lock_path.write_text("99999", encoding="utf-8")
    try:
        with pytest.raises(TimeoutError, match="Could not acquire lock"):
            with FileLock(f, timeout=0.2, poll=0.05):
                pass
    finally:
        lock_path.unlink(missing_ok=True)


def test_filelock_stale_removal(tmp_path):
    f = tmp_path / "data.jsonl"
    f.write_text("", encoding="utf-8")
    lock_path = Path(str(f) + ".lock")
    lock_path.write_text("99999", encoding="utf-8")

    # Backdate the lock file modification time to simulate a stale lock
    stale_time = time.time() - 400  # 400 seconds ago (> 300s threshold)
    os.utime(str(lock_path), (stale_time, stale_time))

    acquired = False
    with FileLock(f, timeout=5.0):
        acquired = True
    assert acquired
    assert not lock_path.exists()
