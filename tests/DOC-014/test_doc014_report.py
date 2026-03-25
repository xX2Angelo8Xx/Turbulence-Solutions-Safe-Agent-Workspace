"""
Tests for DOC-014: Audit Logging for Hook Decisions Research Report

Validates that the research report exists and contains all required sections
as specified in the DOC-014 acceptance criteria (US-034).
"""
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-014"
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


def test_report_section_1_log_format():
    """Section 1 must describe the logging format and required fields."""
    content = _report_text()
    # Must mention JSONL or JSON Lines format
    assert re.search(r"(?i)jsonl|json.lines|json lines", content), (
        "Section 1 must describe the JSONL log format"
    )
    # Must list required fields: timestamp, session_id, tool_name, decision, reason
    assert re.search(r"(?i)timestamp", content), "Section 1 must include 'timestamp' field"
    assert re.search(r"(?i)session.id|session_id", content), "Section 1 must include 'session_id' field"
    assert re.search(r"(?i)tool.name|tool_name", content), "Section 1 must include 'tool_name' field"
    assert re.search(r"(?i)\bdecision\b", content), "Section 1 must include 'decision' field"
    assert re.search(r"(?i)\breason\b", content), "Section 1 must include 'reason' field"


def test_report_section_2_io_overhead():
    """Section 2 must evaluate I/O overhead for deny-only logging."""
    content = _report_text()
    assert re.search(r"(?i)i/o overhead|io overhead|overhead|performance", content), (
        "Section 2 must analyse I/O overhead"
    )
    # Must reference the max-20 denials bound
    assert re.search(r"20", content), (
        "Section 2 must reference the maximum 20 denials per session"
    )
    # Must conclude impact is negligible
    assert re.search(r"(?i)negligible|minimal|imperceptible|low.*impact|impact.*low", content), (
        "Section 2 must conclude that the overhead is negligible"
    )


def test_report_section_3_file_location():
    """Section 3 must specify the log file location, rotation, and retention."""
    content = _report_text()
    # Must name the log file location
    assert re.search(r"\.github/hooks/scripts/|hooks.scripts", content), (
        "Section 3 must specify the log file location inside .github/hooks/scripts/"
    )
    assert re.search(r"(?i)audit\.log|audit_log", content), (
        "Section 3 must name the audit log file"
    )
    # Must address rotation
    assert re.search(r"(?i)rotation|rotate", content), (
        "Section 3 must address log rotation"
    )
    # Must address retention
    assert re.search(r"(?i)retention|retain|30.day", content), (
        "Section 3 must address retention policy"
    )


def test_report_section_4_privacy():
    """Section 4 must address privacy and the deny-only decision."""
    content = _report_text()
    assert re.search(r"(?i)privacy|private", content), (
        "Section 4 must discuss privacy considerations"
    )
    # Must confirm that allowed operations are NOT logged
    assert re.search(
        r"(?i)allow.*not.*log|log.*deny.*only|deny.only|denied.*only|only.*den",
        content,
    ), (
        "Section 4 must confirm deny-only logging (allowed operations excluded)"
    )


def test_report_section_5_integration_point():
    """Section 5 must identify the integration point in security_gate.py."""
    content = _report_text()
    assert re.search(r"(?i)security.gate\.py|security_gate", content), (
        "Section 5 must reference security_gate.py"
    )
    assert re.search(r"(?i)integration point|main\(\)|_append_audit_log|deny branch", content), (
        "Section 5 must describe the integration point within security_gate.py"
    )
    assert re.search(r"(?i)_increment_deny_counter", content), (
        "Section 5 must reference _increment_deny_counter as the anchor for integration"
    )


def test_report_section_6_design_document():
    """Section 6 must contain a design document / summary of decisions."""
    content = _report_text()
    assert re.search(r"(?i)design document|recommended approach|summary of decisions", content), (
        "Section 6 must contain a design document or summary"
    )
    # Must summarise at least the key decisions (format, location, rotation)
    assert re.search(r"(?i)jsonl|json", content), (
        "Design document must confirm JSONL as the chosen format"
    )


def test_report_mentions_jsonl():
    """JSONL format must be explicitly mentioned."""
    content = _report_text()
    assert "jsonl" in content.lower() or "json lines" in content.lower(), (
        "Report must mention JSONL format"
    )


def test_report_mentions_rotation():
    """Log rotation policy must be present."""
    content = _report_text()
    assert re.search(r"(?i)rotat", content), "Report must describe rotation policy"
    # Must mention a rotation size trigger
    assert re.search(r"(?i)1\s*mib|1\s*mb|megabyte|size", content), (
        "Rotation must specify a size trigger"
    )


def test_report_mentions_retention():
    """Retention period must be specified."""
    content = _report_text()
    assert re.search(r"(?i)30.day|30 days|retention", content), (
        "Report must specify a retention period"
    )


def test_report_deny_only_decision():
    """Report must confirm that only denied activities are logged."""
    content = _report_text()
    assert re.search(
        r"(?i)denied.*only|deny.only|log.*denied.*activ|denied.*activ.*log",
        content,
    ), (
        "Report must confirm the deny-only logging decision"
    )
    # Must explicitly state that allowed operations are NOT logged
    assert re.search(
        r"(?i)allowed.*not.*log|not.*log.*allow|allow.*excluded|excluded.*allow",
        content,
    ), (
        "Report must explicitly state that allowed operations are not logged"
    )


def test_report_mentions_counter_config_extension():
    """Report must propose extending counter_config.json with audit fields."""
    content = _report_text()
    assert re.search(r"(?i)counter_config|counter.config", content), (
        "Report must reference counter_config.json"
    )
    assert re.search(r"(?i)audit.log.enabled|audit_log_enabled", content), (
        "Report must propose audit_log_enabled config field"
    )


def test_report_mentions_gitignore():
    """Report must recommend excluding audit log from git."""
    content = _report_text()
    assert re.search(r"(?i)\.gitignore|gitignore", content), (
        "Report must recommend adding audit log to .gitignore"
    )
