#!/usr/bin/env python3
"""Update the Status field of a bug in bugs.jsonl.

Usage:
    .venv\\Scripts\\python scripts/update_bug_status.py BUG-111 --status Closed
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, read_jsonl, update_cell

JSONL_PATH = REPO_ROOT / "docs" / "bugs" / "bugs.jsonl"

VALID_STATUSES = {"Open", "In Progress", "Fixed", "Verified", "Closed"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update the status of a bug in bugs.jsonl."
    )
    parser.add_argument("bug_id", help="Bug ID to update (e.g. BUG-111)")
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(VALID_STATUSES),
        help="New status for the bug",
    )

    args = parser.parse_args()
    bug_id = args.bug_id.strip()
    new_status = args.status.strip()

    _, rows = read_jsonl(JSONL_PATH)
    bug = next((r for r in rows if r.get("ID", "").strip() == bug_id), None)
    if bug is None:
        print(f"ERROR: Bug ID '{bug_id}' not found in bugs.jsonl", file=sys.stderr)
        return 1

    old_status = bug.get("Status", "").strip()
    update_cell(JSONL_PATH, "ID", bug_id, "Status", new_status)
    print(f"{bug_id}: {old_status} → {new_status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
