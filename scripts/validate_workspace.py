#!/usr/bin/env python3
"""Validate workspace integrity before committing.

Pre-commit checker that catches common errors: duplicate IDs, missing
artifacts, un-cascaded statuses, and branch naming violations.

Usage:
    .venv/Scripts/python scripts/validate_workspace.py --full
    .venv/Scripts/python scripts/validate_workspace.py --wp GUI-001
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, read_jsonl, update_cell

WP_JSONL = REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl"
US_JSONL = REPO_ROOT / "docs" / "user-stories" / "user-stories.jsonl"
BUG_JSONL = REPO_ROOT / "docs" / "bugs" / "bugs.jsonl"
TST_JSONL = REPO_ROOT / "docs" / "test-results" / "test-results.jsonl"
DECISIONS_JSONL = REPO_ROOT / "docs" / "decisions" / "index.jsonl"
MAINT_RUNS_JSONL = REPO_ROOT / "docs" / "maintenance" / "orchestrator-runs.jsonl"
EXCEPTIONS_JSON = REPO_ROOT / "docs" / "workpackages" / "validation-exceptions.json"


def _load_exceptions() -> dict:
    """Load validation exceptions from validation-exceptions.json."""
    if not EXCEPTIONS_JSON.exists():
        return {}
    try:
        data = json.loads(EXCEPTIONS_JSON.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (json.JSONDecodeError, OSError):
        return {}


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
    """Check for duplicate IDs in a JSONL file."""
    if not path.exists():
        result.warning(f"JSONL file not found (pre-MNT-018): {path.name}")
        return
    _, rows = read_jsonl(path)
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


def _check_wp_artifacts(
    wp_id: str,
    status: str,
    comments: str,
    result: ValidationResult,
    exceptions: dict | None = None,
) -> None:
    """Check that Done and Review WPs have required artifacts.

    For Done WPs: dev-log.md, test-report.md (unless excepted), and tests/ are
    required — missing any is an ERROR.
    For Review WPs: dev-log.md and tests/ are required — missing either is an
    ERROR. test-report.md is NOT checked (only the Tester creates it).
    """
    if status not in ("Done", "Review"):
        return

    # Skip decomposed WPs
    if "decomposed" in comments.lower() or "Decomposed" in comments:
        return

    if exceptions is None:
        exceptions = {}
    exc_skip = set(exceptions.get(wp_id, {}).get("skip_checks", []))
    skip_test_report = "test-report" in exc_skip
    skip_test_folder = "test-folder" in exc_skip

    wp_folder = REPO_ROOT / "docs" / "workpackages" / wp_id
    dev_log = wp_folder / "dev-log.md"
    test_report = wp_folder / "test-report.md"
    test_dir = REPO_ROOT / "tests" / wp_id

    if not dev_log.exists():
        result.error(f"{wp_id}: missing docs/workpackages/{wp_id}/dev-log.md")

    # test-report.md is only required for Done WPs; Review WPs have not yet
    # been through the Tester, so the file does not yet exist.
    if status == "Done" and not skip_test_report and not test_report.exists():
        result.error(f"{wp_id}: missing docs/workpackages/{wp_id}/test-report.md")

    if not skip_test_folder:
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
    if not WP_JSONL.exists() or not BUG_JSONL.exists():
        return
    _, wp_rows = read_jsonl(WP_JSONL)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    _, bug_rows = read_jsonl(BUG_JSONL)
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
    if not WP_JSONL.exists() or not US_JSONL.exists():
        return
    _, wp_rows = read_jsonl(WP_JSONL)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    _, us_rows = read_jsonl(US_JSONL)
    for us in us_rows:
        us_id = us.get("ID", "")
        us_status = us.get("Status", "")
        linked_val = us.get("Linked WPs", "")
        if not linked_val or us_status in ("Done", "Closed"):
            continue
        if isinstance(linked_val, list):
            linked_wps = [w.strip() for w in linked_val if w.strip()]
        else:
            linked_wps = [w.strip() for w in str(linked_val).split(",") if w.strip()]
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


def _check_tst_coverage(result: ValidationResult, exceptions: dict | None = None) -> None:
    """Check that every Done WP with code changes has passing test results."""
    if exceptions is None:
        exceptions = {}
    if not WP_JSONL.exists() or not TST_JSONL.exists():
        return
    _, wp_rows = read_jsonl(WP_JSONL)
    _, tst_rows = read_jsonl(TST_JSONL)

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
        # Skip WPs with exceptions covering test-report or test-folder
        exc_skip = set(exceptions.get(wp_id, {}).get("skip_checks", []))
        if "test-report" in exc_skip or "test-folder" in exc_skip:
            continue

        if wp_id not in wp_with_pass:
            result.error(
                f"{wp_id}: Done WP has no passing test entry in test-results.jsonl"
            )


def _check_jsonl_structural(result: ValidationResult) -> None:
    """Verify all 6 JSONL files parse cleanly with required fields and valid enum values."""
    # Enum definitions for status fields
    VALID_WP_STATUS = {"Open", "In Progress", "Review", "Done"}
    VALID_BUG_STATUS = {"Open", "In Progress", "Fixed", "Verified", "Closed"}
    VALID_TST_STATUS = {"Pass", "Fail", "Blocked", "Skipped", "XFail"}
    VALID_US_STATUS = {"Open", "In Progress", "Done", "Closed"}
    VALID_ADR_STATUS = {"Active", "Superseded", "Draft"}

    # (path, id_field, status_field, valid_status_values, label, required_fields)
    jsonl_configs = [
        (WP_JSONL,        "ID",     "Status", VALID_WP_STATUS,  "WP",      ["ID", "Status"]),
        (BUG_JSONL,       "ID",     "Status", VALID_BUG_STATUS, "Bug",     ["ID", "Status"]),
        (TST_JSONL,       "ID",     "Status", VALID_TST_STATUS, "Test",    ["ID", "Status"]),
        (US_JSONL,        "ID",     "Status", VALID_US_STATUS,  "US",      ["ID", "Status"]),
        (DECISIONS_JSONL, "ADR-ID", "Status", VALID_ADR_STATUS, "ADR",     ["ADR-ID", "Status", "Title"]),
        (MAINT_RUNS_JSONL, "ID",   "Status", set(),            "MaintRun", []),
    ]

    for jsonl_path, id_field, status_col, valid_values, label, required_fields in jsonl_configs:
        if not jsonl_path.exists():
            result.warning(f"{label} JSONL not found: {jsonl_path.name}")
            continue

        # Empty-line-in-middle detection — blank lines between records violate JSONL spec
        raw_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        for line_num, raw_line in enumerate(raw_lines, start=1):
            if raw_line.strip() == "":
                # A blank line is only acceptable as the final line (trailing newline)
                if line_num < len(raw_lines):
                    result.error(
                        f"{label} JSONL ({jsonl_path.name}) has an empty line at "
                        f"line {line_num} — empty lines between records are not allowed"
                    )

        # Structural parse check — each line must be valid JSON
        try:
            _, rows = read_jsonl(jsonl_path)
        except ValueError as e:
            result.error(f"{label} JSONL structural error: {e}")
            continue

        for row in rows:
            row_id = row.get(id_field, "<no ID>")

            # Required-field check
            for field in required_fields:
                if field not in row or str(row.get(field, "")).strip() == "":
                    result.error(
                        f"{label} JSONL ({jsonl_path.name}): row {row_id!r} "
                        f"is missing required field '{field}'"
                    )

            # Enum validation (warnings — pre-existing data may have non-standard values)
            if valid_values:
                status = row.get(status_col, "")
                if isinstance(status, str):
                    status = status.strip()
                if status and status not in valid_values:
                    result.warning(
                        f"{row_id}: invalid {label} Status '{status}' — "
                        f"expected one of {sorted(valid_values)}"
                    )


VALID_BUG_STATUSES = {"Open", "In Progress", "Fixed", "Verified", "Closed"}


def _check_bug_status_enum(result: ValidationResult) -> None:
    """Verify all bug statuses are from the allowed set."""
    if not BUG_JSONL.exists():
        return
    _, bug_rows = read_jsonl(BUG_JSONL)
    for bug in bug_rows:
        bug_id = bug.get("ID", "<no ID>")
        status = bug.get("Status", "").strip()
        if status and status not in VALID_BUG_STATUSES:
            result.warning(
                f"{bug_id} has non-standard Status '{status}' — "
                f"valid values: Open, In Progress, Fixed, Verified, Closed"
            )


def _check_bug_linkage(wp_id: str, result: ValidationResult) -> None:
    """Warn if bugs referenced in dev-log/test-report lack Fixed In WP linkage."""
    wp_folder = REPO_ROOT / "docs" / "workpackages" / wp_id
    bug_refs: set[str] = set()
    for filename in ("dev-log.md", "test-report.md"):
        filepath = wp_folder / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8", errors="replace")
            bug_refs.update(re.findall(r"BUG-\d{3}", content))

    if not bug_refs:
        return

    if not BUG_JSONL.exists():
        return
    _, bug_rows = read_jsonl(BUG_JSONL)
    bug_map = {b["ID"]: b for b in bug_rows}
    for bug_id in sorted(bug_refs):
        bug = bug_map.get(bug_id)
        if not bug:
            continue
        fixed_wp = bug.get("Fixed In WP", "").strip()
        if fixed_wp != wp_id and wp_id not in fixed_wp:
            result.warning(
                f"{bug_id} referenced in {wp_id} dev-log/test-report "
                f"but Fixed In WP is empty or doesn't match"
            )


def _check_orphaned_state_files(result: ValidationResult) -> None:
    """Check for orphaned .finalization-state.json files in WP folders."""
    if not WP_JSONL.exists():
        return
    _, wp_rows = read_jsonl(WP_JSONL)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    wp_base = REPO_ROOT / "docs" / "workpackages"
    for state_file in wp_base.glob("*/.finalization-state.json"):
        wp_id = state_file.parent.name
        status = wp_status.get(wp_id, "")
        if status == "Done":
            result.warning(
                f"{wp_id} is Done but has orphaned .finalization-state.json"
            )


def _check_stale_branches(result: ValidationResult) -> None:
    """Check for remote branches already merged into main."""
    try:
        proc = subprocess.run(
            ["git", "branch", "-r", "--merged", "main"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
    except FileNotFoundError:
        return
    if proc.returncode != 0:
        return
    for line in proc.stdout.strip().splitlines():
        branch = line.strip()
        if not branch:
            continue
        if "origin/main" in branch or "origin/HEAD" in branch:
            continue
        result.warning(
            f"Stale merged branch: {branch} — should be deleted after finalization"
        )


def apply_fixes() -> int:
    """Auto-fix detectable issues. Returns the number of fixes applied."""
    fixes = 0

    if not WP_JSONL.exists():
        print("No JSONL data files found — run MNT-018 to convert data files.")
        return 0

    _, wp_rows = read_jsonl(WP_JSONL)
    wp_status = {r["ID"]: r["Status"] for r in wp_rows}

    # Fix 1: Delete orphaned .finalization-state.json for Done WPs
    wp_base = REPO_ROOT / "docs" / "workpackages"
    for state_file in wp_base.glob("*/.finalization-state.json"):
        wp_id = state_file.parent.name
        if wp_status.get(wp_id) == "Done":
            state_file.unlink()
            print(f"FIX: Deleted orphaned .finalization-state.json for {wp_id}")
            fixes += 1

    # Fix 2: Close Fixed bugs whose fix-WP is Done
    _, bug_rows = read_jsonl(BUG_JSONL)
    for bug in bug_rows:
        bug_id = bug.get("ID", "")
        bug_status = bug.get("Status", "").strip()
        fixed_wp = bug.get("Fixed In WP", "").strip()
        if bug_status == "Fixed" and fixed_wp:
            if wp_status.get(fixed_wp) == "Done":
                update_cell(BUG_JSONL, "ID", bug_id, "Status", "Closed")
                print(f"FIX: Closed {bug_id} (fixed by Done WP {fixed_wp})")
                fixes += 1

    return fixes


def _check_dependency_ordering(result: ValidationResult) -> None:
    """Check that WP dependencies are satisfied (dependent WPs are Done before dependents start)."""
    if not WP_JSONL.exists():
        return
    _, rows = read_jsonl(WP_JSONL)
    wp_status = {}
    wp_deps = {}
    for row in rows:
        wp_id = row.get("ID", "").strip()
        status = row.get("Status", "").strip()
        depends_on_val = row.get("Depends On", "")
        if wp_id:
            wp_status[wp_id] = status
            if depends_on_val:
                if isinstance(depends_on_val, list):
                    deps = [d.strip() for d in depends_on_val if d.strip()]
                else:
                    deps = [d.strip() for d in str(depends_on_val).split(",") if d.strip()]
                if deps:
                    wp_deps[wp_id] = deps

    for wp_id, deps in wp_deps.items():
        status = wp_status.get(wp_id, "")
        if status in ("In Progress", "Review", "Done"):
            for dep in deps:
                dep_status = wp_status.get(dep, "")
                if dep_status and dep_status not in ("Done",):
                    result.warning(
                        f"{wp_id} (status={status}) depends on {dep} (status={dep_status}) "
                        f"which is not Done yet"
                    )
                elif not dep_status:
                    result.warning(f"{wp_id} depends on {dep} which does not exist in workpackages.jsonl")

    # Check for circular dependencies
    def _has_cycle(wp_id: str, visited: set, stack: set) -> bool:
        visited.add(wp_id)
        stack.add(wp_id)
        for dep in wp_deps.get(wp_id, []):
            if dep not in visited:
                if _has_cycle(dep, visited, stack):
                    return True
            elif dep in stack:
                result.error(f"Circular dependency detected involving {wp_id} and {dep}")
                return True
        stack.discard(wp_id)
        return False

    visited: set[str] = set()
    for wp_id in wp_deps:
        if wp_id not in visited:
            _has_cycle(wp_id, visited, set())


def _check_adr_consistency(result: ValidationResult) -> None:
    """Check ADR index for superseded decisions referenced by Done WPs."""
    adr_index = REPO_ROOT / "docs" / "decisions" / "index.jsonl"
    if not adr_index.exists():
        return  # ADR system not yet set up

    _, adr_rows = read_jsonl(adr_index)
    superseded_adrs = {}
    for row in adr_rows:
        adr_id = row.get("ADR-ID", "").strip()
        status = row.get("Status", "").strip()
        superseded_by = row.get("Superseded By", "").strip()
        if status == "Superseded" and adr_id:
            superseded_adrs[adr_id] = superseded_by

    if not superseded_adrs:
        return

    if not WP_JSONL.exists():
        return
    _, wp_rows = read_jsonl(WP_JSONL)
    for row in wp_rows:
        wp_id = row.get("ID", "").strip()
        status = row.get("Status", "").strip()
        if status != "Done":
            continue
        comments = row.get("Comments", "")
        description = row.get("Description", "")
        combined = f"{comments} {description}"
        for adr_id, replaced_by in superseded_adrs.items():
            if adr_id in combined:
                result.warning(
                    f"{wp_id} references superseded {adr_id} "
                    f"(superseded by {replaced_by or 'unknown'})"
                )


def validate_full(result: ValidationResult) -> None:
    """Run all validation checks."""
    exceptions = _load_exceptions()

    # Duplicate ID checks
    _check_duplicate_ids(TST_JSONL, "ID", result)
    _check_duplicate_ids(WP_JSONL, "ID", result)
    _check_duplicate_ids(BUG_JSONL, "ID", result)
    _check_duplicate_ids(US_JSONL, "ID", result)
    _check_duplicate_ids(DECISIONS_JSONL, "ADR-ID", result)

    # WP artifact checks for all Done and Review WPs
    if WP_JSONL.exists():
        _, wp_rows = read_jsonl(WP_JSONL)
        for wp in wp_rows:
            if wp.get("Status") in ("Done", "Review"):
                _check_wp_artifacts(
                    wp["ID"], wp["Status"], wp.get("Comments", ""), result, exceptions
                )

    # TST coverage cross-validation
    _check_tst_coverage(result, exceptions)

    # Status cascade checks
    _check_bug_cascade(result)
    _check_us_cascade(result)

    # Bug status enum validation
    _check_bug_status_enum(result)

    # Branch naming
    _check_branch_naming(result)

    # JSONL structural integrity
    _check_jsonl_structural(result)

    # Orphaned finalization state files
    _check_orphaned_state_files(result)

    # Stale merged branches
    _check_stale_branches(result)

    # Dependency ordering and circular dependency detection
    _check_dependency_ordering(result)

    # ADR consistency (superseded decisions referenced by Done WPs)
    _check_adr_consistency(result)


def validate_wp(wp_id: str, result: ValidationResult) -> None:
    """Run validation checks scoped to a single workpackage."""
    exceptions = _load_exceptions()

    # Duplicate IDs (always check — other WPs may have caused collisions)
    _check_duplicate_ids(TST_JSONL, "ID", result)

    # Guard: WP JSONL must exist to run WP artifact and bug cascade checks
    if not WP_JSONL.exists():
        result.warning(
            f"WP JSONL not found (pre-MNT-018): {WP_JSONL.name} — "
            f"run MNT-018 to convert data files to JSONL"
        )
        _check_branch_naming(result)
        return

    # WP artifacts
    _, wp_rows = read_jsonl(WP_JSONL)
    for wp in wp_rows:
        if wp["ID"] == wp_id:
            _check_wp_artifacts(
                wp["ID"], wp["Status"], wp.get("Comments", ""), result, exceptions
            )
            break
    else:
        result.error(f"Workpackage {wp_id} not found in workpackages.jsonl")
        return

    # Bug cascade (only for this WP)
    if not BUG_JSONL.exists():
        result.warning(
            f"Bug JSONL not found (pre-MNT-018): {BUG_JSONL.name} — "
            f"run MNT-018 to convert data files to JSONL"
        )
        _check_branch_naming(result)
        _check_bug_linkage(wp_id, result)
        return

    _, bug_rows = read_jsonl(BUG_JSONL)
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

    # Bug linkage (warn about bugs referenced in docs but not linked)
    _check_bug_linkage(wp_id, result)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate workspace integrity before committing."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true", help="Run all checks")
    group.add_argument("--wp", help="Validate a single workpackage (e.g. GUI-001)")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix detectable issues (full mode only)",
    )

    args = parser.parse_args()

    if args.fix and args.wp:
        print("ERROR: --fix cannot be used with --wp (full mode only)", file=sys.stderr)
        return 1

    if args.fix:
        fixes = apply_fixes()
        print(f"Applied {fixes} fix(es).")

    result = ValidationResult()

    if args.full:
        validate_full(result)
    else:
        validate_wp(args.wp, result)

    result.print_report()
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
