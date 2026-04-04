"""One-time migration script: convert all 7 CSV data files to JSONL format.

Usage:
    python scripts/migrate_csv_to_jsonl.py [--dry-run]

With --dry-run: prints what would be converted and row counts, but does NOT
write any JSONL files and does NOT delete any CSV files.

Without --dry-run: converts each CSV to JSONL, verifies row count parity,
then deletes the original CSV. Exits with code 1 on any failure, leaving
all files untouched.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Allow running from repository root or from scripts/ directly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from csv_utils import read_csv
from jsonl_utils import read_jsonl, write_jsonl

# ---------------------------------------------------------------------------
# Config: one entry per CSV file
# ---------------------------------------------------------------------------

# Fields that contain comma-separated values and must become JSON arrays.
# Key: (csv stem, column name).  Value is irrelevant; we use a set for O(1).
_ARRAY_FIELDS: dict[tuple[str, str], None] = {
    ("workpackages", "Depends On"): None,
    ("user-stories", "Linked WPs"): None,
    ("index", "Related WPs"): None,
}

# Ordered list of (csv_path_relative_to_repo, jsonl_path_relative_to_repo, required)
_MIGRATIONS: list[tuple[str, str, bool]] = [
    (
        "docs/workpackages/workpackages.csv",
        "docs/workpackages/workpackages.jsonl",
        True,
    ),
    (
        "docs/user-stories/user-stories.csv",
        "docs/user-stories/user-stories.jsonl",
        True,
    ),
    (
        "docs/bugs/bugs.csv",
        "docs/bugs/bugs.jsonl",
        True,
    ),
    (
        "docs/test-results/test-results.csv",
        "docs/test-results/test-results.jsonl",
        True,
    ),
    (
        "docs/decisions/index.csv",
        "docs/decisions/index.jsonl",
        True,
    ),
    (
        "docs/maintenance/orchestrator-runs.csv",
        "docs/maintenance/orchestrator-runs.jsonl",
        True,
    ),
    (
        "docs/test-results/archived-test-results.csv",
        "docs/test-results/archived-test-results.jsonl",
        False,  # optional — only exists after archival
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_array_field(value: str) -> list[str]:
    """Convert a comma-separated string to a list of stripped, non-empty strings.

    An empty or whitespace-only value returns an empty list.
    """
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _convert_row(row: dict, csv_stem: str) -> dict:
    """Return a new row dict with nested fields converted to lists."""
    converted: dict = {}
    for key, value in row.items():
        if (csv_stem, key) in _ARRAY_FIELDS:
            converted[key] = _split_array_field(value)
        else:
            converted[key] = value
    return converted


def _convert_one(
    csv_path: Path,
    jsonl_path: Path,
    dry_run: bool,
) -> int:
    """Convert a single CSV file to JSONL.

    Returns:
        Number of rows converted.

    Raises:
        ValueError: On row count mismatch after write.
        FileNotFoundError: If csv_path does not exist (caller guards optional files).
    """
    fieldnames, rows = read_csv(csv_path)
    csv_stem = csv_path.stem  # e.g. "workpackages", "user-stories", "index"

    # Convert nested fields to arrays
    converted_rows = [_convert_row(row, csv_stem) for row in rows]

    row_count = len(converted_rows)

    if dry_run:
        # Just report; do nothing
        print(f"  [dry-run] {csv_path.name} → {jsonl_path.name} ({row_count} rows)")
        return row_count

    # Write JSONL (atomic via write_jsonl)
    write_jsonl(jsonl_path, fieldnames, converted_rows)

    # Verify row count parity by re-reading
    _, verify_rows = read_jsonl(jsonl_path)
    if len(verify_rows) != row_count:
        raise ValueError(
            f"Row count mismatch for {csv_path.name}: "
            f"CSV had {row_count} rows but JSONL has {len(verify_rows)} rows."
        )

    print(f"  OK  {csv_path.name} → {jsonl_path.name} ({row_count} rows)")
    return row_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """Entry point. Returns exit code (0 = success, 1 = failure)."""
    parser = argparse.ArgumentParser(
        description="Migrate all CSV data files to JSONL format."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files or deleting CSVs.",
    )
    args = parser.parse_args(argv)

    dry_run: bool = args.dry_run
    repo_root = Path(__file__).resolve().parent.parent

    if dry_run:
        print("=== DRY RUN — no files will be written or deleted ===")
    else:
        print("=== CSV → JSONL migration ===")

    files_converted = 0
    total_rows = 0
    csvs_to_delete: list[Path] = []

    for csv_rel, jsonl_rel, required in _MIGRATIONS:
        csv_path = repo_root / csv_rel
        jsonl_path = repo_root / jsonl_rel

        if not csv_path.exists():
            if required:
                print(f"ERROR: required CSV not found: {csv_path}", file=sys.stderr)
                return 1
            else:
                print(f"  SKIP {csv_path.name} (not present, optional)")
                continue

        try:
            row_count = _convert_one(csv_path, jsonl_path, dry_run)
        except Exception as exc:
            print(f"ERROR converting {csv_path.name}: {exc}", file=sys.stderr)
            return 1

        files_converted += 1
        total_rows += row_count
        csvs_to_delete.append(csv_path)

    if not dry_run:
        # Delete original CSVs only after all conversions succeeded
        for csv_path in csvs_to_delete:
            csv_path.unlink()
            print(f"  DEL {csv_path.name}")

    deleted_count = 0 if dry_run else len(csvs_to_delete)
    print(
        f"\nConverted {files_converted} files, "
        f"{total_rows} total rows, "
        f"{deleted_count} original CSVs deleted."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
