#!/usr/bin/env python3
"""Validate workspace integrity before committing.

Pre-commit checker that catches common errors: duplicate IDs, missing
artifacts, un-cascaded statuses, and branch naming violations.

Usage:
    .venv/Scripts/python scripts/validate_workspace.py --full
    .venv/Scripts/python scripts/validate_workspace.py --wp GUI-001
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import REPO_ROOT, read_csv

WP_CSV = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"
US_CSV = REPO_ROOT / "docs" / "user-stories" / "user-stories.csv"
BUG_CSV = REPO_ROOT / "docs" / "bugs" / "bugs.csv"
TST_CSV = REPO_ROOT / "docs" / "test-results" / "test-results.csv"

# WPs that are exempt from test-report.md (decomposed or maintenance)
EXEMPT_PREFIXES_TEST_REPORT = {"MNT-"}


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def print_report(self) -> None:
        if self.errors:
            print(f"\n{'='*60}")
            print(f"ERRORS ({len(self.errors)}):")
            print(f"{'='*60}")
            for e in self.errors:
                print(f"  [ERROR] {e}")
        if self.warnings:
            print(f"\n{'='*60}")
            print(f"WARNINGS ({len(self.warnings)}):")
            print(f"{'='*60}")
            for w in self.warnings:
                print(f"  [WARN]  {w}")
        if self.ok and not self.warnings:
            print("\nAll checks passed.")
        elif self.ok:
            print(f"\nPassed with {len(self.warnings)} warning(s).")
        else:
            print(f"\nFailed with {len(self.errors)} error(s) and {len(self.warnings)} warning(s).")


def _check_duplicate_ids(path: Path, id_column: str, result: ValidationResult) -> None:
    """Check for duplicate IDs in a CSV file."""
    _, rows = read_csv(path)
    seen: dict[str, int] = {}
    for row in rows:
        rid = row.get(id_column, "").strip()
        if not rid:
            continue
        seen[rid] = seen.get(rid, 0) + 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    if dupes:
        for rid, count in sorted(dupes.items()):
            result.error(f"Duplicate ID {rid} ({count}x) in {path.name}")


def _check_wp_artifacts(wp_id: str, status: str, comments: str, result: ValidationResult) -> None:
    """Check that a Done WP has required artifacts.

    For Done WPs, missing artifacts are ERRORS (not warnings) because the
    WP should not have reached Done without them.
    """
    if status != "Done":
        return

    # Skip decomposed WPs
    if "decomposed" in comments.lower() or "Decomposed" in comments:
        return

    # Skip exempt prefixes
    if any(wp_id.startswith(p) for p in EXEMPT_PREFIXES_TEST_REPORT):
        is_exempt = True
    else:
        is_exempt = False

    wp_folder = REPO_ROOT / "docs" / "workpackages" / wp_id
    dev_log = wp_folder / "dev-log.md"
    test_report = wp_folder / "test-report.md"
    test_dir = REPO_ROOT / "tests" / wp_id

    if not dev_log.exists():
        result.error(f"{wp_id}: missing docs/workpackages/{wp_id}/dev-log.md")

    if not is_exempt and not test_report.exists():
        result.error(f"{wp_id}: missing docs/workpackages/{wp_id}/test-report.md")

    if not test_dir.exists():
        result.error(f"{wp_id}: missing tests/{wp_id}/ directory")
    elif not any(test_dir.glob("test_*.py")):
        result.error(f"{wp_id}: tests/{wp_id}/ exists but contains no test_*.py files")

    # Check for leftover temporary files
    for folder in (wp_folder, test_dir):
        if folder.exists():
            for tmp in folder.glob("tmp_*"):
                result.error(f"{wp_id}: leftover temporary file: {tmp.relative_to(REPO_ROOT)}")


def _check_bug_cascade(result: ValidationResult) -> None:
    """Check for bugs with Done fix-WP that should be Closed."""
    _, wp_rows = read_csv(WP_CSV)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    _, bug_rows = read_csv(BUG_CSV)
    for bug in bug_rows:
        bug_id = bug.get("ID", "")
        bug_status = bug.get("Status", "")
        fixed_wp = bug.get("Fixed In WP", "").strip()
        if fixed_wp and bug_status == "Open":
            if wp_status.get(fixed_wp) == "Done":
                result.error(
                    f"{bug_id} is Open but {fixed_wp} is Done — "
                    f"bug should be Closed"
                )


def _check_us_cascade(result: ValidationResult) -> None:
    """Check for User Stories where all linked WPs are Done."""
    _, wp_rows = read_csv(WP_CSV)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    _, us_rows = read_csv(US_CSV)
    for us in us_rows:
        us_id = us.get("ID", "")
        us_status = us.get("Status", "")
        linked_raw = us.get("Linked WPs", "").strip()
        if not linked_raw or us_status in ("Done", "Closed"):
            continue
        linked_wps = [w.strip() for w in linked_raw.split(",") if w.strip()]
        if not linked_wps:
            continue
        if all(wp_status.get(wp) == "Done" for wp in linked_wps):
            result.warning(
                f"{us_id} has all linked WPs Done but status is "
                f"'{us_status}' — should be 'Done'"
            )


def _check_branch_naming(result: ValidationResult) -> None:
    """Check current branch follows <WP-ID>/<short-description> convention."""
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        ).stdout.strip()
    except FileNotFoundError:
        return

    if branch in ("main", "master", "HEAD"):
        return

    pattern = r"^[A-Z]+-\d{3}/.+"
    if not re.match(pattern, branch):
        result.warning(
            f"Branch '{branch}' does not follow <WP-ID>/<short-description> convention"
        )


def _check_tst_coverage(result: ValidationResult) -> None:
    """Check that every Done WP with code changes has passing test results."""
    _, wp_rows = read_csv(WP_CSV)
    _, tst_rows = read_csv(TST_CSV)

    # Build set of WP IDs that have at least one passing TST entry
    wp_with_pass = set()
    for tst in tst_rows:
        if tst.get("Status", "").strip().lower() == "pass":
            wp_ref = tst.get("WP Reference", "").strip()
            if wp_ref:
                wp_with_pass.add(wp_ref)

    for wp in wp_rows:
        wp_id = wp["ID"]
        status = wp.get("Status", "")
        comments = wp.get("Comments", "")

        if status != "Done":
            continue
        # Skip decomposed WPs
        if "decomposed" in comments.lower():
            continue
        # Skip exempt prefixes
        if any(wp_id.startswith(p) for p in EXEMPT_PREFIXES_TEST_REPORT):
            continue

        if wp_id not in wp_with_pass:
            result.error(
                f"{wp_id}: Done WP has no passing test entry in test-results.csv"
            )


def _check_csv_structural(result: ValidationResult) -> None:
    """Verify all 4 CSVs parse cleanly in strict mode with valid enum values."""
    # Enum definitions for status fields
    VALID_WP_STATUS = {"Open", "In Progress", "Review", "Done"}
    VALID_BUG_STATUS = {"Open", "In Progress", "Fixed", "Verified", "Closed"}
    VALID_TST_STATUS = {"Pass", "Fail", "Blocked", "Skipped"}
    VALID_US_STATUS = {"Open", "In Progress", "Done", "Closed"}

    csv_configs = [
        (WP_CSV, "Status", VALID_WP_STATUS, "WP"),
        (BUG_CSV, "Status", VALID_BUG_STATUS, "Bug"),
        (TST_CSV, "Status", VALID_TST_STATUS, "Test"),
        (US_CSV, "Status", VALID_US_STATUS, "US"),
    ]

    for csv_path, status_col, valid_values, label in csv_configs:
        if not csv_path.exists():
            result.error(f"{label} CSV not found: {csv_path.name}")
            continue

        # Strict parse check
        try:
            _, rows = read_csv(csv_path, strict=True)
        except ValueError as e:
            result.error(f"{label} CSV structural error: {e}")
            continue

        # Enum validation (warnings — pre-existing data may have non-standard values)
        for row in rows:
            row_id = row.get("ID", "<no ID>")
            status = row.get(status_col, "").strip()
            if status and status not in valid_values:
                result.warning(
                    f"{row_id}: invalid {label} Status '{status}' — "
                    f"expected one of {sorted(valid_values)}"
                )


def validate_full(result: ValidationResult) -> None:
    """Run all validation checks."""
    # Duplicate ID checks
    _check_duplicate_ids(TST_CSV, "ID", result)
    _check_duplicate_ids(WP_CSV, "ID", result)
    _check_duplicate_ids(BUG_CSV, "ID", result)
    _check_duplicate_ids(US_CSV, "ID", result)

    # WP artifact checks for all Done WPs
    _, wp_rows = read_csv(WP_CSV)
    for wp in wp_rows:
        if wp.get("Status") == "Done":
            _check_wp_artifacts(
                wp["ID"], wp["Status"], wp.get("Comments", ""), result
            )

    # TST coverage cross-validation
    _check_tst_coverage(result)

    # Status cascade checks
    _check_bug_cascade(result)
    _check_us_cascade(result)

    # Branch naming
    _check_branch_naming(result)

    # CSV structural integrity
    _check_csv_structural(result)


def validate_wp(wp_id: str, result: ValidationResult) -> None:
    """Run validation checks scoped to a single workpackage."""
    # Duplicate IDs (always check — other WPs may have caused collisions)
    _check_duplicate_ids(TST_CSV, "ID", result)

    # WP artifacts
    _, wp_rows = read_csv(WP_CSV)
    for wp in wp_rows:
        if wp["ID"] == wp_id:
            _check_wp_artifacts(
                wp["ID"], wp["Status"], wp.get("Comments", ""), result
            )
            break
    else:
        result.error(f"Workpackage {wp_id} not found in workpackages.csv")
        return

    # Bug cascade (only for this WP)
    _, bug_rows = read_csv(BUG_CSV)
    wp = next(r for r in wp_rows if r["ID"] == wp_id)
    for bug in bug_rows:
        if bug.get("Fixed In WP", "").strip() == wp_id and bug.get("Status") == "Open":
            if wp.get("Status") == "Done":
                result.error(
                    f"{bug['ID']} is Open but {wp_id} is Done — "
                    f"bug should be Closed"
                )

    # Branch naming
    _check_branch_naming(result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate workspace integrity before committing."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true", help="Run all checks")
    group.add_argument("--wp", help="Validate a single workpackage (e.g. GUI-001)")

    args = parser.parse_args()
    result = ValidationResult()

    if args.full:
        validate_full(result)
    else:
        validate_wp(args.wp, result)

    result.print_report()
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
