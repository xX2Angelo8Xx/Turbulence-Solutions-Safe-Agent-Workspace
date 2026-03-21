"""
Tests for DOC-010 — Research VS Code PreToolUse session ID.

These tests verify that the research deliverable (dev-log.md) exists and
contains all required sections and key findings.

TST IDs reserved for DOC-010: assigned by add_test_result.py at log time.
"""
from __future__ import annotations

import os

import pytest

# ---------------------------------------------------------------------------
# Path to the research report
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_REPORT_PATH = os.path.join(
    _REPO_ROOT, "docs", "workpackages", "DOC-010", "dev-log.md"
)

# ---------------------------------------------------------------------------
# Required sections (H2/H3 headings that must appear in the report)
# ---------------------------------------------------------------------------
_REQUIRED_SECTIONS = [
    "## Research Report",
    "### 1. VS Code PreToolUse Hook — Full Payload Structure",
    "### 2. VS Code Hook API — Architectural Rationale",
    "### 3. Alternative Session-Tracking Strategies",
    "### 4. Recommendation for SAF-035",
    "### 5. Implementation Notes for SAF-035",
]

# ---------------------------------------------------------------------------
# Key finding strings that must be present in the report
# ---------------------------------------------------------------------------
_KEY_FINDINGS = [
    # Confirms no session ID was found in the payload
    "does NOT include",
    # Confirms the known payload fields are documented
    "tool_name",
    "tool_input",
    # Confirms alternatives were evaluated
    "Time-Window",
    "VSCODE_PID",
    # Confirms a recommendation is made
    "Strategy A",
]


# ===========================================================================
# TST-DOC010-001: report file exists
# ===========================================================================
def test_report_file_exists():
    """DOC-010: dev-log.md research report must exist on disk."""
    assert os.path.isfile(_REPORT_PATH), (
        f"Research report not found at {_REPORT_PATH}"
    )


# ===========================================================================
# TST-DOC010-002: report is non-empty
# ===========================================================================
def test_report_is_non_empty():
    """DOC-010: dev-log.md must be non-empty."""
    assert os.path.isfile(_REPORT_PATH)
    assert os.path.getsize(_REPORT_PATH) > 0, "Research report is empty"


# ===========================================================================
# TST-DOC010-003: report contains all required sections
# ===========================================================================
@pytest.mark.parametrize("section", _REQUIRED_SECTIONS)
def test_report_has_required_sections(section):
    """DOC-010: research report must contain each required section heading."""
    with open(_REPORT_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert section in content, (
        f"Required section missing from research report: {section!r}"
    )


# ===========================================================================
# TST-DOC010-004: report contains key findings
# ===========================================================================
@pytest.mark.parametrize("finding", _KEY_FINDINGS)
def test_report_contains_key_findings(finding):
    """DOC-010: research report must document each key finding."""
    with open(_REPORT_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert finding in content, (
        f"Key finding string missing from research report: {finding!r}"
    )


# ===========================================================================
# TST-DOC010-005: report documents payload schema evidence
# ===========================================================================
def test_report_contains_payload_schema():
    """DOC-010: report must include the documented hook payload JSON structure."""
    with open(_REPORT_PATH, encoding="utf-8") as fh:
        content = fh.read()
    # Must show the JSON payload schema with both required keys
    assert '"tool_name"' in content
    assert '"tool_input"' in content


# ===========================================================================
# TST-DOC010-006: report states the recommendation
# ===========================================================================
def test_report_contains_recommendation():
    """DOC-010: report must explicitly name the recommended strategy for SAF-035."""
    with open(_REPORT_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert "Time-Window Based" in content, (
        "Report must state the recommended session-tracking approach"
    )
    assert "SAF-035" in content, (
        "Report must reference SAF-035 as the consuming workpackage"
    )


# ===========================================================================
# TST-DOC010-007: report includes implementation state-file schema
# ===========================================================================
def test_report_contains_implementation_notes():
    """DOC-010: report must contain implementation notes with state-file schema."""
    with open(_REPORT_PATH, encoding="utf-8") as fh:
        content = fh.read()
    assert ".hook_state.json" in content, (
        "Report must reference the .hook_state.json state file"
    )
    assert "deny_count" in content, (
        "Report must document the deny_count field in state schema"
    )
    assert "locked" in content, (
        "Report must document the locked field in state schema"
    )
