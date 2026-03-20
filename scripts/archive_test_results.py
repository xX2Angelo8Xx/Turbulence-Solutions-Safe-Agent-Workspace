#!/usr/bin/env python3
"""Archive old test results to keep the active CSV small.

Moves TST entries for Done workpackages into an archived file. The active
test-results.csv stays lean for faster locking and ID computation.

Usage:
    .venv/Scripts/python scripts/archive_test_results.py
    .venv/Scripts/python scripts/archive_test_results.py --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import REPO_ROOT, FileLock, read_csv, write_csv

TST_CSV = REPO_ROOT / "docs" / "test-results" / "test-results.csv"
ARCHIVE_CSV = REPO_ROOT / "docs" / "test-results" / "archived-test-results.csv"
WP_CSV = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"


def archive(dry_run: bool) -> int:
    # Get all Done WP IDs
    _, wp_rows = read_csv(WP_CSV)
    done_wps = {r["ID"] for r in wp_rows if r.get("Status") == "Done"}

    with FileLock(TST_CSV):
        fieldnames, rows = read_csv(TST_CSV)

        keep = []
        to_archive = []
        for row in rows:
            wp_ref = row.get("WP Reference", "").strip()
            if wp_ref in done_wps:
                to_archive.append(row)
            else:
                keep.append(row)

        if not to_archive:
            print("No test results to archive. All entries reference active WPs.")
            return 0

        print(f"{'[DRY RUN] ' if dry_run else ''}Archive summary:")
        print(f"  Total rows:    {len(rows)}")
        print(f"  To archive:    {len(to_archive)} (from {len(done_wps)} Done WPs)")
        print(f"  Remaining:     {len(keep)}")

        if dry_run:
            return 0

        # Append to archive file (create if needed)
        if ARCHIVE_CSV.exists():
            archive_fields, archive_rows = read_csv(ARCHIVE_CSV)
        else:
            archive_fields = fieldnames
            archive_rows = []

        archive_rows.extend(to_archive)
        write_csv(ARCHIVE_CSV, archive_fields, archive_rows)

        # Rewrite active file with only non-archived rows
        write_csv(TST_CSV, fieldnames, keep)

    print(f"Archived {len(to_archive)} rows to {ARCHIVE_CSV.name}")
    print(f"Active file now has {len(keep)} rows")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive test results for Done WPs."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be archived without writing"
    )
    args = parser.parse_args()
    return archive(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
