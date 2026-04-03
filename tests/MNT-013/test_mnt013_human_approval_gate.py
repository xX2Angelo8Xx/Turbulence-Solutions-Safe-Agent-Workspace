"""Tests for MNT-013 — Pre-Release Draft Workflow.

Verifies that orchestrator.agent.md contains an explicit Human Approval Gate
in the CI/CD Pipeline Trigger section with unambiguous state transitions:
  Step 1 — Create Draft Release
  Step 2 — Human Approval Gate (MANDATORY STOP)
  Step 3a — On Approval
  Step 3b — On Rejection
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ORCHESTRATOR = REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md"


def _read() -> str:
    return ORCHESTRATOR.read_text(encoding="utf-8")


def _cicd_section(content: str) -> str:
    """Extract the CI/CD Pipeline Trigger section from file content."""
    match = re.search(
        r"(## CI/CD Pipeline Trigger.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "CI/CD Pipeline Trigger section not found in orchestrator.agent.md"
    return match.group(1)


def test_human_approval_gate_heading_exists():
    """The CI/CD section must contain a Human Approval Gate heading."""
    section = _cicd_section(_read())
    assert "Human Approval Gate" in section, (
        "orchestrator.agent.md CI/CD section is missing 'Human Approval Gate' heading"
    )


def test_mandatory_stop_language_present():
    """MANDATORY STOP language must be present to make the gate unambiguous."""
    section = _cicd_section(_read())
    assert "MANDATORY STOP" in section, (
        "orchestrator.agent.md CI/CD section is missing 'MANDATORY STOP' language — "
        "the human gate must be explicitly marked as a stop point"
    )


def test_step1_create_draft_release_present():
    """Step 1 (Create Draft Release) must be named explicitly in the CI/CD section."""
    section = _cicd_section(_read())
    assert "Step 1" in section, (
        "orchestrator.agent.md CI/CD section is missing 'Step 1' — "
        "draft release creation must be an explicit numbered step"
    )
    assert "Draft Release" in section or "draft release" in section.lower(), (
        "orchestrator.agent.md CI/CD section does not mention draft release creation in Step 1"
    )


def test_step2_human_approval_gate_present():
    """Step 2 (Human Approval Gate) must be a named step in the CI/CD section."""
    section = _cicd_section(_read())
    assert "Step 2" in section, (
        "orchestrator.agent.md CI/CD section is missing 'Step 2' — "
        "the human approval gate must be an explicit numbered step"
    )


def test_step3a_on_approval_present():
    """Step 3a (On Approval) must describe the approval path."""
    section = _cicd_section(_read())
    assert "Step 3a" in section, (
        "orchestrator.agent.md CI/CD section is missing 'Step 3a' — "
        "the approval path must be an explicit numbered sub-step"
    )
    assert "approved" in section.lower(), (
        "orchestrator.agent.md CI/CD section does not describe what happens on user approval"
    )


def test_step3b_on_rejection_present():
    """Step 3b (On Rejection) must describe the rejection path."""
    section = _cicd_section(_read())
    assert "Step 3b" in section, (
        "orchestrator.agent.md CI/CD section is missing 'Step 3b' — "
        "the rejection path must be an explicit numbered sub-step"
    )
    assert "rejected" in section.lower(), (
        "orchestrator.agent.md CI/CD section does not describe what happens on user rejection"
    )


def test_rejection_path_creates_fix_workpackages():
    """On rejection, the Orchestrator must create FIX workpackages from feedback."""
    section = _cicd_section(_read())
    assert "FIX" in section, (
        "orchestrator.agent.md CI/CD rejection path does not mention FIX workpackages"
    )
    assert "add_workpackage.py" in section, (
        "orchestrator.agent.md CI/CD rejection path does not reference add_workpackage.py "
        "for creating FIX workpackages"
    )


def test_rc_flag_clarified_as_cosmetic():
    """The --rc flag must be explicitly clarified as cosmetic in the CI/CD section."""
    section = _cicd_section(_read())
    assert "--rc" in section, (
        "orchestrator.agent.md CI/CD section does not mention --rc flag"
    )
    assert "cosmetic" in section.lower(), (
        "orchestrator.agent.md CI/CD section does not clarify that --rc is cosmetic"
    )


def test_no_automatic_publish():
    """The CI/CD section must explicitly forbid automatic publication."""
    section = _cicd_section(_read())
    assert "Do NOT publish the release automatically" in section or \
           "not publish" in section.lower() or \
           "do not publish" in section.lower(), (
        "orchestrator.agent.md CI/CD section does not forbid automatic release publication"
    )


def test_user_verdict_required_before_proceeding():
    """The CI/CD section must require an explicit user verdict before proceeding."""
    section = _cicd_section(_read())
    verdict_terms = ["verdict", "approved", "rejected", "user replies"]
    assert any(t in section.lower() for t in verdict_terms), (
        "orchestrator.agent.md CI/CD section does not require an explicit user verdict "
        "before proceeding past the approval gate"
    )
    # Must not proceed without explicit confirmation
    assert "without" in section.lower() and ("explicit" in section.lower() or "verdict" in section.lower()), (
        "orchestrator.agent.md CI/CD section does not state that proceeding without "
        "user confirmation is forbidden"
    )
