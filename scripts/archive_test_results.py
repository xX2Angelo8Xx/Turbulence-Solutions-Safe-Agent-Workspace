#!/usr/bin/env python3
"""Archive old test results to keep the active JSONL small.

Moves TST entries for Done workpackages into an archived file. The active
test-results.jsonl stays lean for faster locking and ID computation.

Usage:
    .venv/Scripts/python scripts/archive_test_results.py
    .venv/Scripts/python scripts/archive_test_results.py --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, FileLock, read_jsonl, write_jsonl

TST_JSONL = REPO_ROOT / "docs" / "test-results" / "test-results.jsonl"
ARCHIVE_JSONL = REPO_ROOT / "docs" / "test-results" / "archived-test-results.jsonl"
WP_JSONL = REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl"


def archive(dry_run: bool) -> int:
    # Get all Done WP IDs
    _, wp_rows = read_jsonl(WP_JSONL)
    done_wps = {r["ID"] for r in wp_rows if r.get("Status") == "Done"}

    with FileLock(TST_JSONL):
        fieldnames, rows = read_jsonl(TST_JSONL)

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
        if ARCHIVE_JSONL.exists():
            archive_fields, archive_rows = read_jsonl(ARCHIVE_JSONL)
        else:
            archive_fields = fieldnames
            archive_rows = []

        archive_rows.extend(to_archive)
        write_jsonl(ARCHIVE_JSONL, archive_fields, archive_rows)

        # Rewrite active file with only non-archived rows
        write_jsonl(TST_JSONL, fieldnames, keep)

    print(f"Archived {len(to_archive)} rows to {ARCHIVE_JSONL.name}")
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
