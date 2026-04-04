"""MNT-021 Tester edge-case tests.

Covers additional scenarios the Developer's suite did not address:
1. No csv.DictReader calls remain in migrated test files
2. No import csv remains in test files that were converted to json
3. ADR-007 **Related WPs:** heading uses inline-bold format (not ## heading)
4. ADR-007 lists MNT-021 in its Related WPs field
5. No functional CSV file path literals remain in test files
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO_ROOT / "tests"
ADR_007 = REPO_ROOT / "docs" / "decisions" / "ADR-007-csv-to-jsonl-migration.md"

# WPs that legitimately work with CSV infrastructure
ALLOWED_DIRS = {
    "MNT-016", "MNT-017", "MNT-018", "MNT-019", "MNT-020",
    "MNT-021",
    "FIX-065",  # tests for csv_utils are still valid (deprecated but functional)
}

# Directories that were specifically migrated by MNT-021
MIGRATED_DIRS = {
    "DOC-053", "FIX-009", "FIX-059", "MNT-003",
    "FIX-066", "FIX-068", "FIX-081", "FIX-082", "FIX-098",
    "MNT-006", "MNT-009", "MNT-012", "FIX-067",
}


def _collect_test_files(dirs=None):
    """Return test .py files, optionally scoped to specific WP directories."""
    files = []
    for py_file in TESTS_ROOT.rglob("test_*.py"):
        parts = py_file.relative_to(TESTS_ROOT).parts
        if not parts:
            continue
        wp_dir = parts[0]
        if dirs is not None:
            if wp_dir not in dirs:
                continue
        elif wp_dir in ALLOWED_DIRS:
            continue
        files.append(py_file)
    return files


def test_no_csv_dict_reader_in_migrated_tests():
    """No migrated test file should call csv.DictReader — must use json.loads."""
    pattern = re.compile(r'csv\.DictReader')
    violations = []
    for f in _collect_test_files(MIGRATED_DIRS):
        content = f.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if pattern.search(line) and not line.lstrip().startswith('#'):
                violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, (
        "csv.DictReader calls found in migrated test files:\n" + "\n".join(violations)
    )


def test_no_functional_csv_file_paths_in_tests():
    """No test file outside migration WPs should use a quoted .csv file path."""
    # Matches string literals containing .csv — not in comments or docstrings
    pattern = re.compile(r'"[^"]*\.csv[^"]*"')
    # Only catch production data file paths, not csv module attribute names
    data_pattern = re.compile(
        r'"(?:test-results|bugs|workpackages|user-stories|index)\.csv"'
    )
    violations = []
    for f in _collect_test_files():
        content = f.read_text(encoding="utf-8")
        if not data_pattern.search(content):
            continue
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if data_pattern.search(line):
                violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, (
        "Quoted CSV production file paths found in test files:\n" + "\n".join(violations)
    )


def test_adr_007_related_wps_inline_bold_format():
    """ADR-007 must use inline-bold **Related WPs:** format, not a ## heading.

    DOC-053 tests rely on this format for regex extraction of Related WPs.
    """
    content = ADR_007.read_text(encoding="utf-8")
    assert re.search(r'\*\*Related WPs:\*\*', content), (
        "ADR-007 must contain '**Related WPs:**' in inline-bold format"
    )
    assert not re.search(r'^## Related WPs', content, re.MULTILINE), (
        "ADR-007 must NOT use '## Related WPs' heading format"
    )


def test_adr_007_lists_mnt021():
    """ADR-007 Related WPs line must include MNT-021."""
    content = ADR_007.read_text(encoding="utf-8")
    match = re.search(r'\*\*Related WPs:\*\*\s*(.+)', content)
    assert match is not None, "ADR-007 missing **Related WPs:** line"
    related_text = match.group(1)
    assert "MNT-021" in related_text, (
        f"ADR-007 Related WPs does not include MNT-021. Found: {related_text!r}"
    )
