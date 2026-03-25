"""
Tests for DOC-012: MCP Tools Extensibility Research Report

Validates that the research report exists and contains all required sections
as specified in the DOC-012 acceptance criteria.
"""
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-012"
    / "research-report.md"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_file_exists():
    """The research report file must exist at the expected path."""
    assert REPORT_PATH.exists(), f"research-report.md not found at {REPORT_PATH}"


def test_report_is_not_empty():
    """The research report must not be empty."""
    content = _report_text()
    assert len(content.strip()) > 200, "research-report.md is unexpectedly short"


def test_report_section_1_mcp_inventory():
    """Section 1 must inventory common MCP servers."""
    content = _report_text()
    assert re.search(r"(?i)inventory|common mcp server", content), (
        "Section 1 MCP server inventory is missing"
    )
    # At least a few server categories should be mentioned
    for keyword in ("filesystem", "github", "database", "docker"):
        assert keyword.lower() in content.lower(), (
            f"Expected MCP category '{keyword}' in inventory section"
        )


def test_report_section_2_security_implications():
    """Section 2 must assess security implications of mcp_* tool calls."""
    content = _report_text()
    assert re.search(r"(?i)security implication", content), (
        "Security implications section is missing"
    )
    # Key threat vectors must be mentioned
    for concept in ("filesystem", "network", "arbitrary"):
        assert concept.lower() in content.lower(), (
            f"Expected security concept '{concept}' in security section"
        )


def test_report_section_3_zone_checking():
    """Section 3 must evaluate zone-checking feasibility."""
    content = _report_text()
    assert re.search(r"(?i)zone.check", content), (
        "Zone-checking feasibility section is missing"
    )
    # Must address both feasible and non-feasible cases
    assert re.search(r"(?i)not.{0,20}zone.check|non.zone.check|cannot be.{0,20}path", content), (
        "Report must discuss tools that cannot be zone-checked"
    )


def test_report_section_4_framework():
    """Section 4 must propose an allowlisting framework."""
    content = _report_text()
    assert re.search(r"(?i)framework|allowlist", content), (
        "Allowlisting framework section is missing"
    )
    # Must include some configuration concept
    assert re.search(r"(?i)configur|schema|settings\.json|mcp_policy", content), (
        "Framework section must include workspace configuration guidance"
    )


def test_report_section_5_recommendation():
    """Section 5 must contain a clear recommendation."""
    content = _report_text()
    assert re.search(r"(?i)recommendation|verdict|decision", content), (
        "Recommendation section is missing"
    )
    # Must take a stance on the default policy
    assert re.search(r"(?i)block.*default|default.*block", content), (
        "Recommendation must address the default blocking policy"
    )


def test_report_appendix_checklist():
    """Report must include the acceptance criteria checklist."""
    content = _report_text()
    assert re.search(r"(?i)checklist|required section", content), (
        "Report must include a checklist confirming all required sections"
    )
    # All 5 ACs must appear in the checklist
    for i in range(1, 6):
        assert re.search(rf"(?i)Section {i}|\[x\].*section {i}|\- \[x\]", content), (
            f"Checklist item for Section {i} not found in report"
        )
