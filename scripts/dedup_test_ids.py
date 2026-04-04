#!/usr/bin/env python3
"""One-time deduplication of TST-IDs in test-results.csv.

Scans all rows, identifies duplicate TST-IDs, and assigns new unique IDs
to later occurrences of each duplicate. The first occurrence keeps its
original ID.

Usage:
    .venv/Scripts/python scripts/dedup_test_ids.py
    .venv/Scripts/python scripts/dedup_test_ids.py --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, FileLock, read_jsonl, write_jsonl

TST_JSONL = REPO_ROOT / "docs" / "test-results" / "test-results.jsonl"


def dedup(dry_run: bool) -> int:
    with FileLock(TST_JSONL):
        fieldnames, rows = read_jsonl(TST_JSONL)

        # Find max existing numeric ID
        pattern = re.compile(r"^TST-(\d+)$")
        max_num = 0
        for row in rows:
            m = pattern.match(row.get("ID", ""))
            if m:
                max_num = max(max_num, int(m.group(1)))

        # Track seen IDs; renumber later duplicates
        seen: set[str] = set()
        renames: list[tuple[str, str]] = []
        for row in rows:
            rid = row.get("ID", "").strip()
            if not rid:
                continue
            if rid in seen:
                max_num += 1
                new_id = f"TST-{max_num}"
                renames.append((rid, new_id))
                if not dry_run:
                    row["ID"] = new_id
            else:
                seen.add(rid)

        if not renames:
            print("No duplicate TST-IDs found. Nothing to do.")
            return 0

        print(f"{'[DRY RUN] ' if dry_run else ''}Found {len(renames)} duplicate(s):")
        for old, new in renames:
            print(f"  {old} → {new}")

        if not dry_run:
            write_jsonl(TST_JSONL, fieldnames, rows)
            print(f"\nRewrote {TST_JSONL.name} with {len(renames)} ID(s) renumbered.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate TST-IDs in test-results.jsonl."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be renamed without writing"
    )
    args = parser.parse_args()
    return dedup(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
