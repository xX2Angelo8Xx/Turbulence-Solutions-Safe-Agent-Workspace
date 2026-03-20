"""Shared CSV utilities with file locking for parallel agent execution.

Provides atomic CSV operations that prevent race conditions when multiple
agents modify the same CSV file simultaneously. All functions are
non-interactive and safe for autonomous agent use.
"""

import csv
import os
import re
import sys
import time
from io import StringIO
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent


class FileLock:
    """Cross-platform file lock using atomic lock file creation.

    Uses os.O_CREAT | os.O_EXCL which is atomic on all major filesystems
    (NTFS, ext4, APFS). Safe for parallel agent execution.
    """

    def __init__(self, path: Path, timeout: float = 30.0, poll: float = 0.1):
        self.lock_path = Path(str(path) + ".lock")
        self.timeout = timeout
        self.poll = poll

    _STALE_THRESHOLD = 300.0  # seconds (5 minutes)

    def __enter__(self):
        start = time.monotonic()
        stale_cleaned = False
        while True:
            try:
                fd = os.open(
                    str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY
                )
                os.write(fd, f"{os.getpid()}".encode())
                os.close(fd)
                return self
            except FileExistsError:
                # Stale lock detection: if lock file is older than threshold,
                # assume the owner crashed and remove it automatically.
                if not stale_cleaned and self.lock_path.exists():
                    try:
                        age = time.time() - self.lock_path.stat().st_mtime
                        if age > self._STALE_THRESHOLD:
                            self.lock_path.unlink()
                            stale_cleaned = True
                            print(
                                f"WARNING: Stale lock file detected "
                                f"({age:.0f}s old), removed automatically: "
                                f"{self.lock_path}",
                                file=sys.stderr,
                            )
                            continue  # retry immediately
                    except OSError:
                        pass  # another process may have removed it
                elapsed = time.monotonic() - start
                if elapsed > self.timeout:
                    raise TimeoutError(
                        f"Could not acquire lock on {self.lock_path} "
                        f"within {self.timeout}s. If no other agent is "
                        f"running, delete {self.lock_path} manually."
                    )
                time.sleep(self.poll)

    def __exit__(self, *args):
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def read_csv(
    path: Path,
    expected_columns: Optional[list[str]] = None,
    strict: bool = True,
) -> tuple[list[str], list[dict]]:
    """Read a CSV file and return (fieldnames, rows as dicts).

    Args:
        path: Path to the CSV file.
        expected_columns: If provided, raise ValueError when the CSV header
            is missing any of the listed columns.
        strict: If True (default), raise ValueError when a row has more
            columns than the header. If False, merge overflow columns into
            the last field (legacy behavior).
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252")
    reader = csv.DictReader(StringIO(text))
    fieldnames = list(reader.fieldnames or [])

    if expected_columns is not None:
        missing = set(expected_columns) - set(fieldnames)
        if missing:
            raise ValueError(
                f"{path.name}: missing expected columns: {sorted(missing)}. "
                f"Found: {fieldnames}"
            )

    rows = []
    for row_idx, row in enumerate(reader, start=1):
        # DictReader puts extra columns under None key
        if None in row:
            if strict:
                overflow = row[None]
                row_id = row.get(fieldnames[0], "<unknown>") if fieldnames else "<unknown>"
                raise ValueError(
                    f"{path.name} row {row_idx} (ID={row_id}): "
                    f"overflow columns detected — row has "
                    f"{len(fieldnames) + len(overflow)} fields but header "
                    f"has {len(fieldnames)}. Overflow values: {overflow}"
                )
            else:
                overflow = row.pop(None)
                last_field = fieldnames[-1]
                row[last_field] = row.get(last_field, "") + "," + ",".join(overflow)
        rows.append(row)
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Write rows to a CSV file using QUOTE_ALL with atomic write-verify-rename.

    All CSVs in this project use csv.QUOTE_ALL to eliminate field-escaping
    edge cases. This is a project-wide standard — do not change.

    Steps:
        1. Sanitize all field values — reject bare \\r or \\n characters.
        2. Write to a temporary file in the same directory.
        3. Re-read the temp file with strict parsing and verify row count.
        4. Atomic-rename temp file over target (os.replace).
        5. On failure, delete temp file and raise ValueError.
    """
    # Field-level sanitization: reject bare \r or \n (not \r\n which csv handles)
    for row_idx, row in enumerate(rows):
        row_id = row.get(fieldnames[0], "<unknown>") if fieldnames else "<unknown>"
        for field_name, value in row.items():
            if not isinstance(value, str):
                continue
            if "\r\n" in value:
                # csv module handles \r\n inside quoted fields — skip those
                cleaned = value.replace("\r\n", "")
            else:
                cleaned = value
            if "\r" in cleaned or "\n" in cleaned:
                raise ValueError(
                    f"write_csv: row {row_idx} (ID={row_id}), "
                    f"field '{field_name}' contains bare newline character. "
                    f"Value: {value!r}"
                )

    buf = StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=fieldnames, quoting=csv.QUOTE_ALL, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    content = buf.getvalue()

    # Write to temp file in same directory
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")

        # Re-read and verify with strict parsing
        verify_fields, verify_rows = read_csv(tmp_path, strict=True)
        if len(verify_rows) != len(rows):
            raise ValueError(
                f"write_csv verification failed: wrote {len(rows)} rows "
                f"but re-read {len(verify_rows)} rows"
            )

        # Atomic rename
        os.replace(str(tmp_path), str(path))
    except Exception:
        # Clean up temp file on any failure
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def next_id(
    path: Path,
    prefix: str,
    id_column: str = "ID",
    zero_pad: int = 0,
) -> str:
    """Determine the next sequential ID for a given prefix.

    WARNING: This function does NOT hold a lock. For atomic ID assignment
    and row insertion, use locked_next_id_and_append() instead.

    Args:
        path: Path to the CSV file.
        prefix: ID prefix (e.g., "TST", "BUG", "GUI").
        id_column: Column name containing IDs.
        zero_pad: Digits to zero-pad (0 = no padding).

    Returns:
        Next ID string, e.g., "TST-1888" or "BUG-086".
    """
    _, rows = read_csv(path)
    return _compute_next_id(rows, prefix, id_column, zero_pad)


def _compute_next_id(
    rows: list[dict], prefix: str, id_column: str, zero_pad: int
) -> str:
    """Compute next ID from an already-loaded row list."""
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    max_num = 0
    for row in rows:
        m = pattern.match(row.get(id_column, ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    if zero_pad > 0:
        return f"{prefix}-{next_num:0{zero_pad}d}"
    return f"{prefix}-{next_num}"


def append_row(
    path: Path,
    row_dict: dict,
    id_column: str = "ID",
) -> str:
    """Append a row to a CSV file with duplicate-ID prevention.

    Uses file locking for parallel safety.

    Returns:
        The ID of the appended row.

    Raises:
        ValueError: If the row's ID already exists.
    """
    with FileLock(path):
        fieldnames, rows = read_csv(path)
        new_id = row_dict.get(id_column, "")
        existing_ids = {r.get(id_column, "") for r in rows}
        if new_id in existing_ids:
            raise ValueError(f"Duplicate ID: {new_id} already exists in {path}")
        for fn in fieldnames:
            if fn not in row_dict:
                row_dict[fn] = ""
        rows.append(row_dict)
        write_csv(path, fieldnames, rows)
    return new_id


def update_cell(
    path: Path,
    id_column: str,
    id_value: str,
    target_column: str,
    new_value: str,
) -> None:
    """Update a single cell in a CSV file, identified by row ID.

    Uses file locking for parallel safety.
    """
    with FileLock(path):
        fieldnames, rows = read_csv(path)
        found = False
        for row in rows:
            if row.get(id_column) == id_value:
                if target_column not in fieldnames:
                    raise KeyError(
                        f"Column '{target_column}' not in {path}"
                    )
                row[target_column] = new_value
                found = True
                break
        if not found:
            raise KeyError(f"No row with {id_column}={id_value} in {path}")
        write_csv(path, fieldnames, rows)


def locked_next_id_and_append(
    path: Path,
    prefix: str,
    row_template: dict,
    id_column: str = "ID",
    zero_pad: int = 0,
) -> str:
    """Atomically assign the next sequential ID and append the row.

    Holds a single lock for the entire read-compute-write cycle, preventing
    race conditions when multiple agents add rows simultaneously.

    Args:
        path: CSV file path.
        prefix: ID prefix (e.g., "TST", "BUG").
        row_template: Row dict — the ID field will be filled automatically.
        id_column: Column containing IDs.
        zero_pad: Zero-padding width.

    Returns:
        The assigned ID string.
    """
    with FileLock(path):
        fieldnames, rows = read_csv(path)
        new_id = _compute_next_id(rows, prefix, id_column, zero_pad)

        # Check for collision (should not happen, but defense in depth)
        existing_ids = {r.get(id_column, "") for r in rows}
        if new_id in existing_ids:
            raise ValueError(
                f"Computed ID {new_id} already exists — CSV may be corrupt"
            )

        row_template[id_column] = new_id
        for fn in fieldnames:
            if fn not in row_template:
                row_template[fn] = ""
        rows.append(row_template)
        write_csv(path, fieldnames, rows)
    return new_id
