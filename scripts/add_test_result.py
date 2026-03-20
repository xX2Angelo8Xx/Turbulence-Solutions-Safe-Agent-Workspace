#!/usr/bin/env python3
"""Add a test result row to test-results.csv with auto-assigned TST-ID.

Usage:
    .venv/Scripts/python scripts/add_test_result.py \
        --name "test_foo_bar" \
        --type Unit \
        --wp GUI-001 \
        --status Pass \
        --env "Windows 11 + Python 3.13" \
        --result "5 passed / 0 failed" \
        [--notes "Optional notes"]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Allow running from repo root or scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import REPO_ROOT, locked_next_id_and_append

CSV_PATH = REPO_ROOT / "docs" / "test-results" / "test-results.csv"

VALID_TYPES = {"Unit", "Integration", "Security", "Regression", "Cross-platform"}
VALID_STATUSES = {"Pass", "Fail", "Blocked", "Skipped"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add a test result row with auto-assigned TST-ID."
    )
    parser.add_argument("--name", required=True, help="Test name")
    parser.add_argument(
        "--type", required=True, choices=sorted(VALID_TYPES), help="Test type"
    )
    parser.add_argument("--wp", required=True, help="Workpackage reference (e.g. GUI-001)")
    parser.add_argument(
        "--status", required=True, choices=sorted(VALID_STATUSES), help="Test status"
    )
    parser.add_argument("--env", required=True, help='Environment (e.g. "Windows 11 + Python 3.13")')
    parser.add_argument("--result", required=True, help="Brief result description")
    parser.add_argument("--notes", default="", help="Additional notes (optional)")
    parser.add_argument("--date", default=str(date.today()), help="Run date (default: today)")

    args = parser.parse_args()

    row = {
        "Test Name": args.name,
        "Test Type": args.type,
        "WP Reference": args.wp,
        "Status": args.status,
        "Run Date": args.date,
        "Environment": args.env,
        "Result": args.result,
        "Notes": args.notes,
    }

    assigned_id = locked_next_id_and_append(
        path=CSV_PATH,
        prefix="TST",
        row_template=row,
        id_column="ID",
        zero_pad=0,
    )
    print(f"Added {assigned_id}: {args.name} ({args.status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
