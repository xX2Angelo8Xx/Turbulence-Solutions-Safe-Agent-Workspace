"""Shared CSV utilities with file locking for parallel agent execution.

Provides atomic CSV operations that prevent race conditions when multiple
agents modify the same CSV file simultaneously. All functions are
non-interactive and safe for autonomous agent use.
"""

import csv
import os
import re
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

    def __enter__(self):
        start = time.monotonic()
        while True:
            try:
                fd = os.open(
                    str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY
                )
                os.write(fd, f"{os.getpid()}".encode())
                os.close(fd)
                return self
            except FileExistsError:
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


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV file and return (fieldnames, rows as dicts)."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252")
    reader = csv.DictReader(StringIO(text))
    fieldnames = list(reader.fieldnames or [])
    rows = []
    for row in reader:
        # DictReader puts extra columns under None key — merge them back
        if None in row:
            overflow = row.pop(None)
            last_field = fieldnames[-1]
            row[last_field] = row.get(last_field, "") + "," + ",".join(overflow)
        rows.append(row)
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Write rows to a CSV file, preserving the project's quoting style."""
    try:
        original = path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError:
        original = path.read_text(encoding="cp1252") if path.exists() else ""
    use_quote_all = original.startswith('"')

    buf = StringIO()
    quoting = csv.QUOTE_ALL if use_quote_all else csv.QUOTE_MINIMAL
    writer = csv.DictWriter(
        buf, fieldnames=fieldnames, quoting=quoting, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


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
