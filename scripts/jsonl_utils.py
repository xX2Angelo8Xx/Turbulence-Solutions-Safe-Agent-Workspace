"""Shared JSONL utilities with file locking for parallel agent execution.

Provides atomic JSONL operations that prevent race conditions when multiple
agents modify the same JSONL file simultaneously. All functions are
non-interactive and safe for autonomous agent use.

JSONL format: one JSON object per line, UTF-8, no BOM.
"""

import json
import os
import re
import sys
import time
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


def read_jsonl(
    path: Path,
    expected_fields: Optional[list[str]] = None,
) -> tuple[list[str], list[dict]]:
    """Read a JSONL file and return (fieldnames, rows as dicts).

    fieldnames are extracted from the keys of the first non-empty row.
    Empty lines are skipped.

    Args:
        path: Path to the .jsonl file.
        expected_fields: If provided, raise ValueError when any row is
            missing one of the listed fields.

    Returns:
        Tuple of (fieldnames, rows). fieldnames is [] if file is empty.
    """
    text = path.read_text(encoding="utf-8")
    rows: list[dict] = []
    fieldnames: list[str] = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{path.name} line {line_num}: invalid JSON — {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise ValueError(
                f"{path.name} line {line_num}: expected a JSON object, "
                f"got {type(obj).__name__}"
            )
        if not fieldnames:
            fieldnames = list(obj.keys())
        rows.append(obj)

    if expected_fields is not None and rows:
        all_keys = set(fieldnames)
        missing = set(expected_fields) - all_keys
        if missing:
            raise ValueError(
                f"{path.name}: missing expected fields: {sorted(missing)}. "
                f"Found: {fieldnames}"
            )

    return fieldnames, rows


def write_jsonl(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Write rows to a JSONL file using atomic write-verify-rename.

    Each row is written as a JSON object on its own line. Field order
    follows the fieldnames list.

    Steps:
        1. Serialize all rows to JSONL content in memory.
        2. Write to a temporary file in the same directory.
        3. Re-read the temp file and verify row count matches.
        4. Atomic-rename temp file over target (os.replace).
        5. On failure, delete temp file and re-raise.
    """
    lines = []
    for row in rows:
        # Preserve fieldnames ordering; include any extra keys after
        ordered = {fn: row.get(fn, "") for fn in fieldnames}
        for k, v in row.items():
            if k not in ordered:
                ordered[k] = v
        lines.append(json.dumps(ordered, ensure_ascii=False))

    content = "\n".join(lines)
    if content:
        content += "\n"

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")

        # Re-read and verify row count
        _, verify_rows = read_jsonl(tmp_path)
        if len(verify_rows) != len(rows):
            raise ValueError(
                f"write_jsonl verification failed: wrote {len(rows)} rows "
                f"but re-read {len(verify_rows)} rows"
            )

        # Atomic rename
        os.replace(str(tmp_path), str(path))
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


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


def next_id(
    path: Path,
    prefix: str,
    id_column: str = "ID",
    zero_pad: int = 3,
) -> str:
    """Determine the next sequential ID for a given prefix.

    WARNING: This function does NOT hold a lock. For atomic ID assignment
    and row insertion, use locked_next_id_and_append() instead.

    Args:
        path: Path to the JSONL file.
        prefix: ID prefix (e.g., "TST", "BUG", "GUI").
        id_column: Column name containing IDs.
        zero_pad: Digits to zero-pad (0 = no padding).

    Returns:
        Next ID string, e.g., "TST-1888" or "BUG-086".
    """
    _, rows = read_jsonl(path)
    return _compute_next_id(rows, prefix, id_column, zero_pad)


def append_row(
    path: Path,
    fieldnames: list[str],
    row: dict,
    id_column: str = "ID",
) -> str:
    """Append a row to a JSONL file with duplicate-ID prevention.

    Uses file locking for parallel safety.

    Args:
        path: Path to the JSONL file.
        fieldnames: Ordered list of field names for the file schema.
        row: Row dict to append.
        id_column: Column used for duplicate detection.

    Returns:
        The ID of the appended row.

    Raises:
        ValueError: If the row's ID already exists.
    """
    with FileLock(path):
        existing_fieldnames, rows = read_jsonl(path)
        # Use existing fieldnames if file already has content
        if existing_fieldnames:
            fieldnames = existing_fieldnames
        new_id = row.get(id_column, "")
        existing_ids = {r.get(id_column, "") for r in rows}
        if new_id in existing_ids:
            raise ValueError(f"Duplicate ID: {new_id} already exists in {path}")
        for fn in fieldnames:
            if fn not in row:
                row[fn] = ""
        rows.append(row)
        write_jsonl(path, fieldnames, rows)
    return new_id


def update_cell(
    path: Path,
    id_column: str,
    id_value: str,
    target_column: str,
    new_value: str,
) -> None:
    """Update a single field in a JSONL file, identified by row ID.

    Uses file locking for parallel safety.

    Raises:
        KeyError: If id_value is not found, or target_column is not present.
    """
    with FileLock(path):
        fieldnames, rows = read_jsonl(path)
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
        write_jsonl(path, fieldnames, rows)


def locked_next_id_and_append(
    path: Path,
    prefix: str,
    row_template: dict,
    id_column: str = "ID",
    zero_pad: int = 3,
) -> str:
    """Atomically assign the next sequential ID and append the row.

    Holds a single lock for the entire read-compute-write cycle, preventing
    race conditions when multiple agents add rows simultaneously.

    Args:
        path: JSONL file path.
        prefix: ID prefix (e.g., "TST", "BUG").
        row_template: Row dict — the ID field will be filled automatically.
        id_column: Column containing IDs.
        zero_pad: Zero-padding width.

    Returns:
        The assigned ID string.
    """
    with FileLock(path):
        fieldnames, rows = read_jsonl(path)
        new_id = _compute_next_id(rows, prefix, id_column, zero_pad)

        # Defense in depth: check for collision
        existing_ids = {r.get(id_column, "") for r in rows}
        if new_id in existing_ids:
            raise ValueError(
                f"Computed ID {new_id} already exists — JSONL may be corrupt"
            )

        row_template[id_column] = new_id
        for fn in fieldnames:
            if fn not in row_template:
                row_template[fn] = ""
        rows.append(row_template)
        write_jsonl(path, fieldnames, rows)
    return new_id
