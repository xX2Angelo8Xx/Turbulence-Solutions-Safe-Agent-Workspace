#!/usr/bin/env python3
"""Add a bug row to bugs.jsonl with auto-assigned BUG-ID.

Usage:
    .venv/Scripts/python scripts/add_bug.py \
        --title "Short description" \
        --severity High \
        --reported-by "Tester Agent" \
        --description "Detailed explanation" \
        --steps "1. Do X  2. Do Y" \
        --expected "What should happen" \
        --actual "What actually happens" \
        [--fixed-in-wp FIX-001] \
        [--comments "Optional"]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, locked_next_id_and_append

JSONL_PATH = REPO_ROOT / "docs" / "bugs" / "bugs.jsonl"

VALID_SEVERITIES = {"Critical", "High", "Medium", "Low"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add a bug row with auto-assigned BUG-ID."
    )
    parser.add_argument("--title", required=True, help="Short descriptive summary")
    parser.add_argument(
        "--severity", required=True, choices=sorted(VALID_SEVERITIES),
        help="Bug severity"
    )
    parser.add_argument("--reported-by", required=True, help="Who discovered the bug")
    parser.add_argument("--description", required=True, help="Detailed explanation")
    parser.add_argument("--steps", required=True, help="Steps to reproduce")
    parser.add_argument("--expected", required=True, help="Expected behaviour")
    parser.add_argument("--actual", required=True, help="Actual behaviour")
    parser.add_argument("--fixed-in-wp", default="", help="Workpackage ID with fix")
    parser.add_argument("--comments", default="", help="Additional context")

    args = parser.parse_args()

    row = {
        "Title": args.title,
        "Status": "Open",
        "Severity": args.severity,
        "Reported By": args.reported_by,
        "Description": args.description,
        "Steps to Reproduce": args.steps,
        "Expected Behaviour": args.expected,
        "Actual Behaviour": args.actual,
        "Fixed In WP": args.fixed_in_wp,
        "Comments": args.comments,
    }

    assigned_id = locked_next_id_and_append(
        path=JSONL_PATH,
        prefix="BUG",
        row_template=row,
        id_column="ID",
        zero_pad=3,
    )
    print(f"Added {assigned_id}: {args.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
