"""MNT-021 — No stale CSV references in test files.

Verifies that test files outside of the migration workpackages
(MNT-016 through MNT-020) do not reference stale CSV production
paths or csv_utils mock targets.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO_ROOT / "tests"

# WPs that dealt with the CSV infrastructure itself — allowed to contain CSV refs
ALLOWED_DIRS = {
    "MNT-016", "MNT-017", "MNT-018", "MNT-019", "MNT-020",
    "MNT-021",  # This test file itself references CSV names as patterns
}

# Patterns that indicate stale CSV usage in test files
STALE_PATTERNS = [
    r'test-results\.csv',
    r'bugs\.csv',
    r'"finalize_wp\.BUG_CSV"',
    r'"validate_workspace\.BUG_CSV"',
    r'"validate_workspace\.WP_CSV"',
    r'"validate_workspace\.US_CSV"',
    r'"validate_workspace\.TST_CSV"',
    r'patch\.object\([a-z_]+,\s*"read_csv"',
    r'"update_bug_status\.CSV_PATH"',
]


def _collect_test_files():
    """Return all test .py files outside of allowed CSV migration WPs."""
    files = []
    for py_file in TESTS_ROOT.rglob("test_*.py"):
        parts = py_file.relative_to(TESTS_ROOT).parts
        if parts and parts[0] in ALLOWED_DIRS:
            continue
        files.append(py_file)
    return files


def test_no_stale_test_results_csv():
    """No test file outside migration WPs should reference test-results.csv."""
    pattern = re.compile(r'test-results\.csv')
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if pattern.search(content):
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Stale test-results.csv references found:\n" + "\n".join(violations)


def test_no_stale_bugs_csv():
    """No test file outside migration WPs should reference bugs.csv (in code)."""
    # Allow in string literals that describe old behaviour (comments/docstrings)
    # but catch actual path strings like "bugs.csv" and production patches
    pattern = re.compile(r'"bugs\.csv"|patch.*BUG_CSV|_make_bug_csv\(')
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if pattern.search(content):
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Stale bugs.csv references found:\n" + "\n".join(violations)


def test_no_stale_read_csv_mocks():
    """No test file outside migration WPs should mock read_csv on production scripts."""
    pattern = re.compile(r'patch\.object\([a-z_]+,\s*"read_csv"')
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if pattern.search(content):
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Stale read_csv mock references found:\n" + "\n".join(violations)


def test_no_stale_wp_csv_patches():
    """No test file outside migration WPs should patch WP_CSV/BUG_CSV/US_CSV/TST_CSV."""
    pattern = re.compile(r'"(?:validate_workspace|finalize_wp)\.(?:WP|BUG|US|TST)_CSV"')
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if pattern.search(content):
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Stale WP/BUG/US/TST _CSV patch references found:\n" + "\n".join(violations)


def test_no_stale_csv_path_patches():
    """No test file should patch update_bug_status.CSV_PATH (must use JSONL_PATH)."""
    pattern = re.compile(r'"update_bug_status\.CSV_PATH"')
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if pattern.search(content):
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Stale CSV_PATH patch references found:\n" + "\n".join(violations)
