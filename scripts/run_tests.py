#!/usr/bin/env python3
"""Run pytest for a workpackage and atomically log the result.

Executes the test suite in tests/<WP-ID>/, parses pytest output, and logs
the result to test-results.jsonl via locked_next_id_and_append(). This
closes the "self-reported results" loophole — the script is proof that
tests were actually executed.

Usage:
    .venv/Scripts/python scripts/run_tests.py --wp GUI-001 --type Unit --env "Windows 11 + Python 3.13"
    .venv/Scripts/python scripts/run_tests.py --wp GUI-001 --type Regression --env "Windows 11 + Python 3.13" --full-suite
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT, locked_next_id_and_append

TST_JSONL = REPO_ROOT / "docs" / "test-results" / "test-results.jsonl"
TESTS_DIR = REPO_ROOT / "tests"

VALID_TYPES = {"Unit", "Integration", "Security", "Regression", "Cross-platform"}


def _run_pytest(test_path: str) -> tuple[int, str, str]:
    """Run pytest and return (exit_code, stdout, stderr)."""
    cmd = [
        sys.executable, "-m", "pytest", test_path,
        "--tb=short", "-q",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


def _parse_pytest_summary(stdout: str) -> tuple[str, str]:
    """Parse pytest output to extract pass/fail summary and test name.

    Returns:
        (result_summary, test_name)
    """
    # Look for the summary line like "5 passed" or "3 passed, 2 failed"
    summary_match = re.search(
        r"(\d+ passed(?:, \d+ failed)?(?:, \d+ error)?(?:, \d+ skipped)?(?:, \d+ warning)?.*)",
        stdout,
    )
    if summary_match:
        result_summary = summary_match.group(1).strip()
    else:
        # Fallback: use last non-empty line
        lines = [l.strip() for l in stdout.strip().splitlines() if l.strip()]
        result_summary = lines[-1] if lines else "No output captured"

    return result_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pytest for a WP and log results atomically."
    )
    parser.add_argument("--wp", required=True, help="Workpackage ID (e.g. GUI-001)")
    parser.add_argument(
        "--type", required=True, choices=sorted(VALID_TYPES),
        help="Test type"
    )
    parser.add_argument(
        "--env", required=True,
        help='Environment (e.g. "Windows 11 + Python 3.13")'
    )
    parser.add_argument(
        "--full-suite", action="store_true",
        help="Run the entire test suite instead of just tests/<WP-ID>/"
    )
    parser.add_argument(
        "--notes", default="",
        help="Additional notes (optional)"
    )
    parser.add_argument(
        "--date", default=str(date.today()),
        help="Run date (default: today)"
    )

    args = parser.parse_args()

    # Determine test path
    if args.full_suite:
        test_path = str(TESTS_DIR)
        test_name = f"{args.wp}: full regression suite"
    else:
        wp_test_dir = TESTS_DIR / args.wp
        if not wp_test_dir.exists():
            print(f"Error: tests/{args.wp}/ directory does not exist")
            return 1
        if not any(wp_test_dir.glob("test_*.py")):
            print(f"Error: tests/{args.wp}/ contains no test_*.py files")
            return 1
        test_path = str(wp_test_dir)
        test_name = f"{args.wp}: targeted suite"

    # Run pytest
    print(f"Running pytest on {test_path}...")
    exit_code, stdout, stderr = _run_pytest(test_path)

    # Parse results
    result_summary = _parse_pytest_summary(stdout)
    status = "Pass" if exit_code == 0 else "Fail"

    # Display output
    if stdout.strip():
        print(stdout)
    if stderr.strip():
        print(stderr, file=sys.stderr)

    print(f"\nResult: {status} — {result_summary}")

    # Build notes
    notes_parts = []
    if args.notes:
        notes_parts.append(args.notes)
    if exit_code != 0 and stderr.strip():
        # Include first line of stderr for context
        first_err = stderr.strip().splitlines()[0][:200]
        notes_parts.append(f"stderr: {first_err}")

    # Log result atomically
    row = {
        "Test Name": test_name,
        "Test Type": args.type,
        "WP Reference": args.wp,
        "Status": status,
        "Run Date": args.date,
        "Environment": args.env,
        "Result": result_summary,
        "Notes": "; ".join(notes_parts) if notes_parts else "",
    }

    assigned_id = locked_next_id_and_append(
        path=TST_JSONL,
        prefix="TST",
        row_template=row,
        id_column="ID",
        zero_pad=0,
    )
    print(f"Logged as {assigned_id}: {test_name} ({status})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
