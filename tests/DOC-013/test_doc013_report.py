"""
Tests for DOC-013: Multi-Agent Counter Coordination Research Report

Validates that the research report exists and contains all required sections
as specified in the DOC-013 acceptance criteria (US-034).
"""
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-013"
    / "research-report.md"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_file_exists():
    """The research report file must exist at the expected path."""
    assert REPORT_PATH.exists(), f"research-report.md not found at {REPORT_PATH}"


def test_report_is_not_empty():
    """The research report must have substantial content."""
    content = _report_text()
    assert len(content.strip()) > 200, "research-report.md is unexpectedly short"


def test_report_section_1_payload_analysis():
    """Section 1 must address VS Code hook payload and session ID behaviour."""
    content = _report_text()
    # Must discuss the hook payload schema
    assert re.search(r"(?i)hook payload|payload schema|tool_name", content), (
        "Section 1 must discuss hook payload schema"
    )
    # Must discuss session ID resolution
    assert re.search(r"(?i)session.id|session id|otel|otel_sid", content), (
        "Section 1 must discuss session ID resolution"
    )
    # Must conclude that subagents are not distinguished in payload
    assert re.search(r"(?i)no.*agent.*identifier|not.*distinguish|identical.*schema|schema.*identical", content), (
        "Section 1 must document that main agents and subagents are indistinguishable in the payload"
    )


def test_report_section_2_counter_options():
    """Section 2 must evaluate the three counter strategy options."""
    content = _report_text()
    # All three options must be present
    assert re.search(r"(?i)shared counter|option a", content), (
        "Option A (shared counter) must be evaluated"
    )
    assert re.search(r"(?i)independent counter|option b", content), (
        "Option B (independent counters) must be evaluated"
    )
    assert re.search(r"(?i)no counter.*subagent|exempt.*subagent|option c", content), (
        "Option C (no counter for subagents) must be evaluated"
    )


def test_report_section_3_security_implications():
    """Section 3 must assess security implications and bypass risks."""
    content = _report_text()
    assert re.search(r"(?i)security implication|bypass|rogue agent", content), (
        "Section 3 must cover security implications and bypass analysis"
    )
    # Must address the subagent spawning attack vector
    assert re.search(r"(?i)spawn.*subagent|subagent.*spawn|subagent.*bypass", content), (
        "Report must address the subagent spawning bypass attack"
    )


def test_report_section_4_recommendation():
    """Section 4 must contain a clear recommendation."""
    content = _report_text()
    assert re.search(r"(?i)recommendation|recommend", content), (
        "Section 4 must contain a recommendation"
    )
    # The recommendation must be for the shared counter
    assert re.search(r"(?i)shared counter|option a.*recommend|recommend.*option a|retain.*shared", content), (
        "Recommendation must identify shared counter (Option A) as the approach"
    )


def test_report_documents_limitation():
    """Report must explicitly document that separate counters are not feasible today."""
    content = _report_text()
    assert re.search(
        r"(?i)not feasible|limitation|no.*agent.*id.*payload|payload.*no.*agent",
        content,
    ), (
        "Report must document the platform limitation (separate counters not feasible)"
    )


def test_report_mentions_shared_counter():
    """Shared counter behaviour must be described."""
    content = _report_text()
    assert "shared" in content.lower(), "Report must discuss shared counter behaviour"
    assert "counter" in content.lower(), "Report must mention the counter"


def test_report_mentions_bypass_risk():
    """Bypass risk via subagent spawning must be addressed."""
    content = _report_text()
    assert re.search(r"(?i)bypass", content), (
        "Report must mention bypass risk"
    )
    # Must reference that shared counter closes the bypass
    assert re.search(r"(?i)not feasible.*bypass|bypass.*not.*feasible|shared.*prevent|prevent.*bypass|closes.*attack|no bypass", content), (
        "Report must confirm that the shared counter prevents the subagent bypass"
    )


def test_report_references_existing_implementation():
    """Report must reference the existing SAF-035 implementation."""
    content = _report_text()
    assert re.search(r"SAF-035|SAF.035", content), (
        "Report must reference the SAF-035 counter implementation"
    )
