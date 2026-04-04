#!/usr/bin/env python3
"""Add a workpackage row to workpackages.csv with auto-assigned ID.

Automatically updates the parent User Story's Linked WPs column to include
the new WP ID, preventing cross-reference drift.

Usage:
    .venv/Scripts/python scripts/add_workpackage.py \
        --category GUI \
        --name "Button Hover State" \
        --description "Add hover colour change to all buttons" \
        --goal "All buttons change colour on mouse hover" \
        --user-story US-007 \
        [--comments "Optional notes"]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import (
    REPO_ROOT,
    FileLock,
    locked_next_id_and_append,
    read_jsonl,
    write_jsonl,
)

WP_JSONL = REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl"
US_JSONL = REPO_ROOT / "docs" / "user-stories" / "user-stories.jsonl"

VALID_CATEGORIES = {"INS", "SAF", "GUI", "DOC", "FIX", "MNT"}


def _update_us_linked_wps(us_id: str, wp_id: str) -> None:
    """Add wp_id to the User Story's Linked WPs column."""
    if us_id == "Enabler":
        return
    with FileLock(US_JSONL):
        fieldnames, rows = read_jsonl(US_JSONL)
        for row in rows:
            if row.get("ID") == us_id:
                existing = row.get("Linked WPs", [])
                if isinstance(existing, list):
                    wp_list = existing[:]
                else:
                    wp_list = [w.strip() for w in existing.split(",") if w.strip()]
                if wp_id not in wp_list:
                    wp_list.append(wp_id)
                    row["Linked WPs"] = wp_list
                    write_jsonl(US_JSONL, fieldnames, rows)
                return
        raise KeyError(f"User Story {us_id} not found in {US_JSONL}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add a workpackage with auto-assigned ID and US cross-ref."
    )
    parser.add_argument(
        "--category", required=True, choices=sorted(VALID_CATEGORIES),
        help="WP category prefix"
    )
    parser.add_argument("--name", required=True, help="Short descriptive name")
    parser.add_argument("--description", required=True, help="What needs to be done")
    parser.add_argument("--goal", required=True, help="Measurable completion criteria")
    parser.add_argument(
        "--user-story", required=True,
        help='Parent user story ID (e.g. US-007) or "Enabler"'
    )
    parser.add_argument("--comments", default="", help="Optional notes")
    parser.add_argument(
        "--depends-on", default="",
        help="Comma-separated WP IDs this WP depends on (e.g. GUI-001,GUI-002)"
    )
    parser.add_argument(
        "--blockers", default="",
        help="Description of blockers preventing progress"
    )

    args = parser.parse_args()
    category = args.category.upper()

    if args.user_story != "Enabler" and not args.user_story.startswith("US-"):
        print(f"Error: --user-story must be a US-NNN ID or 'Enabler', got '{args.user_story}'")
        return 1

    # Validate US exists (unless Enabler)
    if args.user_story != "Enabler":
        _, us_rows = read_jsonl(US_JSONL)
        if not any(r.get("ID") == args.user_story for r in us_rows):
            print(f"Error: User Story {args.user_story} not found in {US_JSONL}")
            return 1

    row = {
        "Category": category,
        "Name": args.name,
        "Status": "Open",
        "Assigned To": "",
        "Description": args.description,
        "Goal": args.goal,
        "Comments": args.comments,
        "User Story": args.user_story,
        "Depends On": args.depends_on,
        "Blockers": args.blockers,
    }

    assigned_id = locked_next_id_and_append(
        path=WP_JSONL,
        prefix=category,
        row_template=row,
        id_column="ID",
        zero_pad=3,
    )

    # Update parent US cross-reference
    if args.user_story != "Enabler":
        _update_us_linked_wps(args.user_story, assigned_id)
        print(f"Added {assigned_id}: {args.name} (linked to {args.user_story})")
    else:
        print(f"Added {assigned_id}: {args.name} (Enabler)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
