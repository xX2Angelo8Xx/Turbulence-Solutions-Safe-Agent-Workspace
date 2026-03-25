"""
Tests for DOC-015: Agent Self-Identification Mechanism Research Report

Validates that the research report exists and contains all required sections
as specified in the DOC-015 acceptance criteria.
"""
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-015"
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
    assert len(content.strip()) > 500, "research-report.md is unexpectedly short"


def test_report_section_1_hook_payload():
    """Section 1 must analyse the VS Code Copilot hook payload for agent/model metadata."""
    content = _report_text()
    # Must mention hook payload or PreToolUse
    assert re.search(r"(?i)hook payload|pretooluse|hook.*payload|payload.*hook", content), (
        "Section 1 must discuss the VS Code Copilot hook payload"
    )
    # Must mention tool_name presence in payload
    assert re.search(r"(?i)tool.name|tool_name", content), (
        "Section 1 must confirm tool_name is present in the payload"
    )
    # Must note absence of model identity in payload
    assert re.search(r"(?i)absent|not.*present|does not.*include|no.*model|model.*not.*present", content), (
        "Section 1 must confirm that model identity is absent from the hook payload"
    )


def test_report_section_2_model_identification():
    """Section 2 must examine whether different models include identifying info in tool calls."""
    content = _report_text()
    # Must mention multiple model families
    assert re.search(r"(?i)gpt.4|openai", content), (
        "Section 2 must discuss GPT-4/OpenAI models"
    )
    assert re.search(r"(?i)claude|anthropic", content), (
        "Section 2 must discuss Claude/Anthropic models"
    )
    assert re.search(r"(?i)gemini|google", content), (
        "Section 2 must discuss Gemini/Google models"
    )
    # Must conclude no model injects identity
    assert re.search(r"(?i)normaliz|no model|does not inject|same.*schema|standard.*schema", content), (
        "Section 2 must conclude that no model injects identifying info in tool calls"
    )


def test_report_section_3_feasibility():
    """Section 3 must evaluate feasibility of a mandatory self-identification protocol."""
    content = _report_text()
    # Must discuss feasibility
    assert re.search(r"(?i)feasib", content), (
        "Section 3 must discuss feasibility of the self-identification protocol"
    )
    # Must mention that a session-start hook doesn't exist
    assert re.search(r"(?i)session.start|sessionstart|no.*hook|hook.*not.*exist|does not exist", content), (
        "Section 3 must note the absence of a session-start hook"
    )
    # Must discuss at least one implementation variant
    assert re.search(r"(?i)instruction|first.call|first tool|convention|protocol", content), (
        "Section 3 must discuss a concrete implementation approach"
    )


def test_report_section_4_security_implications():
    """Section 4 must assess security implications and spoofability of agent self-ID."""
    content = _report_text()
    # Must discuss spoofability
    assert re.search(r"(?i)spoof", content), (
        "Section 4 must discuss spoofability of agent self-identification"
    )
    # Must mention trust boundary or verification
    assert re.search(r"(?i)trust.boundary|trust boundary|cannot be verified|no.*verify|unverified|cannot verify", content), (
        "Section 4 must analyse the trust boundary for agent-reported identity"
    )
    # Must mention cryptographic attestation as the sound alternative
    assert re.search(r"(?i)cryptograph|attest|sign", content), (
        "Section 4 must discuss cryptographic attestation as the theoretically sound solution"
    )


def test_report_section_5_benefits():
    """Section 5 must discuss the potential benefits of agent self-identification."""
    content = _report_text()
    # Must mention audit trail benefit
    assert re.search(r"(?i)audit.trail|audit trail|audit log", content), (
        "Section 5 must discuss audit trail improvements"
    )
    # Must mention per-model counter or per-model tracking
    assert re.search(r"(?i)per.model|per model", content), (
        "Section 5 must discuss per-model counter tracking"
    )


def test_report_section_6_recommendations():
    """Section 6 must provide concrete recommendations."""
    content = _report_text()
    # Must include recommendations section
    assert re.search(r"(?i)recommend", content), (
        "Section 6 must include recommendations"
    )
    # Must recommend NOT implementing now (infeasible / not secure)
    assert re.search(
        r"(?i)do not implement|not implement|not.*feasible|not feasible|not currently feasible",
        content,
    ), (
        "Section 6 must recommend not implementing the protocol in current form"
    )
    # Must propose a future/platform path
    assert re.search(r"(?i)feature request|platform.*change|platform.*update|future", content), (
        "Section 6 must propose a future platform-level path"
    )


def test_report_has_executive_summary():
    """The report must contain an executive summary."""
    content = _report_text()
    assert re.search(r"(?i)executive summary", content), (
        "Report must have an Executive Summary section"
    )


def test_report_references_security_gate():
    """The report must reference the security_gate.py file it analysed."""
    content = _report_text()
    assert re.search(r"(?i)security.gate|security_gate", content), (
        "Report must reference security_gate.py as an inspected file"
    )


def test_report_otel_session_id_discussed():
    """The report must discuss the OTel/session ID mechanism."""
    content = _report_text()
    assert re.search(r"(?i)otel|session.id|session_id|copilot-otel", content), (
        "Report must discuss the OTel session ID mechanism"
    )
