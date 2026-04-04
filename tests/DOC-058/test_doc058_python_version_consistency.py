"""
Tests for DOC-058: Standardize Python Version in Examples.

Verifies that docs/work-rules/testing-protocol.md:
  - Contains a "Supported Python Versions" note explaining both 3.11 and 3.13.
  - Uses "Python 3.11" consistently in all run_tests.py and add_test_result.py
    example commands.
  - Does NOT reference "Python 3.13" outside the approved version note.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
PROTOCOL_FILE = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"

APPROVED_313_LINE = (
    '> **Supported Python Versions:** This project supports Python 3.11+ '
    '(tested on 3.11 and 3.13). Examples in this document use Python 3.11 '
    'but work identically on 3.13.'
)


def _lines():
    return PROTOCOL_FILE.read_text(encoding="utf-8").splitlines()


def test_protocol_file_exists():
    assert PROTOCOL_FILE.exists(), f"testing-protocol.md not found at {PROTOCOL_FILE}"


def test_supported_versions_note_present():
    """The file must contain the canonical 'Supported Python Versions' note."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "Supported Python Versions" in content, (
        "testing-protocol.md is missing the 'Supported Python Versions' note"
    )


def test_version_note_mentions_311_and_313():
    """The version note must explicitly state both 3.11 and 3.13 are supported."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert "3.11 and 3.13" in content, (
        "Version note must mention both Python 3.11 and 3.13 as supported versions"
    )


def test_no_python_313_outside_approved_note():
    """No line other than the approved version note should contain 'Python 3.13'."""
    unapproved = [
        line for line in _lines()
        if "Python 3.13" in line and line.strip() != APPROVED_313_LINE.strip()
    ]
    assert unapproved == [], (
        "Unexpected 'Python 3.13' references found outside the version note:\n"
        + "\n".join(f"  {line!r}" for line in unapproved)
    )


def test_run_tests_developer_example_uses_311():
    """The developer run_tests.py example must use Python 3.11."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    pattern = r'run_tests\.py --wp <WP-ID> --type Unit --env "Windows 11 \+ Python 3\.11"'
    assert re.search(pattern, content), (
        "Developer run_tests.py example command does not use Python 3.11"
    )


def test_run_tests_tester_example_uses_311():
    """The tester run_tests.py example must use Python 3.11."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    pattern = r'run_tests\.py --wp <WP-ID> --type Regression --env "Windows 11 \+ Python 3\.11" --full-suite'
    assert re.search(pattern, content), (
        "Tester run_tests.py example command does not use Python 3.11"
    )


def test_tst_id_section_examples_use_311():
    """The TST-ID assignment section examples must use Python 3.11."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    pattern = r'run_tests\.py --wp GUI-001 --type Unit --env "Windows 11 \+ Python 3\.11"'
    assert re.search(pattern, content), (
        "TST-ID section run_tests.py example (WP-specific) does not use Python 3.11"
    )
    pattern2 = r'run_tests\.py --wp GUI-001 --type Regression --env "Windows 11 \+ Python 3\.11" --full-suite'
    assert re.search(pattern2, content), (
        "TST-ID section run_tests.py example (full suite) does not use Python 3.11"
    )


def test_add_test_result_example_uses_311():
    """The add_test_result.py fallback example must use Python 3.11."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    pattern = r'--env "Windows 11 \+ Python 3\.11"'
    matches = list(re.finditer(pattern, content))
    assert len(matches) >= 3, (
        f"Expected at least 3 occurrences of '--env \"Windows 11 + Python 3.11\"', "
        f"found {len(matches)}"
    )


def test_csv_example_uses_311():
    """The CSV column description example must show Python 3.11."""
    content = PROTOCOL_FILE.read_text(encoding="utf-8")
    assert '"Windows 11 + Python 3.11"' in content, (
        "CSV column description example does not show Python 3.11"
    )


def test_acceptance_criterion_no_mixed_versions():
    """
    Acceptance criterion from WP: grep for mixed versions returns 0.
    Specifically, no line (outside the approved note) contains both 3.11 and 3.13
    in the context of a command example.
    """
    lines_with_313 = [
        line for line in _lines()
        if "3.13" in line and line.strip() != APPROVED_313_LINE.strip()
    ]
    assert lines_with_313 == [], (
        "Mixed versions found — lines still referencing 3.13 outside the version note:\n"
        + "\n".join(f"  {line!r}" for line in lines_with_313)
    )
