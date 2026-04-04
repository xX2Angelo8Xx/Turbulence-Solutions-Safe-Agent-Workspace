"""MNT-022 — Retire csv_utils.py: final sweep and clean state verification.

Verifies that:
1. Stale CSV data files (workpackages.csv, index.csv) have been deleted.
2. Active operational scripts reference .jsonl, not .csv, in their docstrings.
3. The status-report prompt references .jsonl data sources.
4. No active production script (outside legacy exceptions) imports csv_utils.
5. scripts/README.md documents jsonl_utils as the shared module (not csv_utils).
"""

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Scripts that are allowed to reference or import csv_utils (legacy test infrastructure)
CSV_UTILS_LEGACY_EXEMPT = {"csv_utils.py", "migrate_csv_to_jsonl.py"}


# ---------------------------------------------------------------------------
# 1. Deleted CSV data files
# ---------------------------------------------------------------------------

def test_workpackages_csv_deleted():
    """docs/workpackages/workpackages.csv must not exist (migrated to .jsonl)."""
    path = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"
    assert not path.exists(), (
        f"{path.relative_to(REPO_ROOT)} still exists — must be deleted in MNT-022"
    )


def test_decisions_index_csv_deleted():
    """docs/decisions/index.csv must not exist (migrated to .jsonl)."""
    path = REPO_ROOT / "docs" / "decisions" / "index.csv"
    assert not path.exists(), (
        f"{path.relative_to(REPO_ROOT)} still exists — must be deleted in MNT-022"
    )


# ---------------------------------------------------------------------------
# 2. Status-report prompt uses JSONL paths
# ---------------------------------------------------------------------------

def test_status_report_prompt_no_csv_paths():
    """status-report.prompt.md must not reference .csv data file paths."""
    prompt_path = REPO_ROOT / ".github" / "prompts" / "status-report.prompt.md"
    assert prompt_path.exists(), f"Prompt file not found: {prompt_path}"

    content = prompt_path.read_text(encoding="utf-8")
    # Check for specific data-file CSV path patterns
    pattern = re.compile(
        r"workpackages\.csv|bugs\.csv|test-results\.csv|user-stories\.csv",
        re.IGNORECASE,
    )
    matches = pattern.findall(content)
    assert not matches, (
        f"status-report.prompt.md still references CSV data paths: {matches}"
    )


def test_status_report_prompt_uses_jsonl():
    """status-report.prompt.md must reference .jsonl data sources."""
    prompt_path = REPO_ROOT / ".github" / "prompts" / "status-report.prompt.md"
    content = prompt_path.read_text(encoding="utf-8")
    assert "workpackages.jsonl" in content, (
        "status-report.prompt.md must reference workpackages.jsonl"
    )
    assert "bugs.jsonl" in content, (
        "status-report.prompt.md must reference bugs.jsonl"
    )


# ---------------------------------------------------------------------------
# 3. Active script docstrings reference .jsonl not .csv
# ---------------------------------------------------------------------------

_OPERATIONAL_SCRIPTS = [
    "add_bug.py",
    "add_test_result.py",
    "add_workpackage.py",
    "archive_test_results.py",
    "dedup_test_ids.py",
    "run_tests.py",
    "update_bug_status.py",
]

_STALE_CSV_DOCSTRING_PATTERN = re.compile(
    r"(?:test-results|bugs|workpackages|user-stories|archived-test-results)\.csv"
)


def test_operational_scripts_no_stale_csv_in_docstrings():
    """Operational scripts must not mention .csv data file paths in docstrings."""
    violations = []
    for script_name in _OPERATIONAL_SCRIPTS:
        path = SCRIPTS_DIR / script_name
        assert path.exists(), f"Expected script not found: {path}"
        content = path.read_text(encoding="utf-8")
        # Only scan the module-level docstring (first triple-quoted string at top)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        docstring = ast.get_docstring(tree)
        if docstring and _STALE_CSV_DOCSTRING_PATTERN.search(docstring):
            for line in docstring.splitlines():
                if _STALE_CSV_DOCSTRING_PATTERN.search(line):
                    violations.append(f"{script_name}: {line.strip()}")
    assert not violations, (
        "Stale .csv references in operational script docstrings:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# 4. No non-exempt script imports csv_utils
# ---------------------------------------------------------------------------

_CSV_UTILS_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from\s+csv_utils\s+import|import\s+csv_utils)", re.MULTILINE
)


def test_no_non_exempt_script_imports_csv_utils():
    """No operational script (outside legacy exemptions) should import csv_utils."""
    violations = []
    for py_file in SCRIPTS_DIR.glob("*.py"):
        if py_file.name in CSV_UTILS_LEGACY_EXEMPT:
            continue
        content = py_file.read_text(encoding="utf-8")
        if _CSV_UTILS_IMPORT_PATTERN.search(content):
            violations.append(py_file.name)
    assert not violations, (
        "Non-exempt scripts import csv_utils (should use jsonl_utils):\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# 5. README documents jsonl_utils, not csv_utils, as the active shared module
# ---------------------------------------------------------------------------

def test_readme_documents_jsonl_utils():
    """scripts/README.md must reference jsonl_utils.py as the active shared module."""
    readme = SCRIPTS_DIR / "README.md"
    assert readme.exists(), f"scripts/README.md not found"
    content = readme.read_text(encoding="utf-8")
    assert "jsonl_utils.py" in content, (
        "scripts/README.md must document jsonl_utils.py as the active shared module"
    )


def test_readme_no_csv_utils_active_section():
    """scripts/README.md must not have csv_utils.py as the primary shared module section."""
    readme = SCRIPTS_DIR / "README.md"
    content = readme.read_text(encoding="utf-8")
    # The README should not have a standalone "## Shared Module: csv_utils.py" section
    assert "## Shared Module: csv_utils.py" not in content, (
        "scripts/README.md still has csv_utils.py as the primary shared module section"
    )
