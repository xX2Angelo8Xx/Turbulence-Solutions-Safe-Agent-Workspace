"""
Edge-case tests for DOC-012: MCP Tools Extensibility Research Report

Tester-added tests covering boundary conditions and quality requirements
beyond the Developer's structural checks.
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

DEV_LOG_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-012"
    / "dev-log.md"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _devlog_text() -> str:
    return DEV_LOG_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Report quality and depth tests
# ---------------------------------------------------------------------------

def test_report_mentions_ssrf():
    """Security section must discuss SSRF as it is a key MCP attack vector."""
    content = _report_text()
    assert re.search(r"(?i)ssrf|server.side request forgery", content), (
        "Report must cover SSRF risk from mcp_fetch_* tools"
    )


def test_report_permanently_blocked_list_present():
    """Report must define a set of permanently blocked tool categories."""
    content = _report_text()
    assert re.search(r"(?i)permanently blocked|remain permanently blocked|never allowlist", content), (
        "Report must identify permanently blocked tool categories"
    )
    # Docker, database-write, and cloud tools are the usual permanent blocks
    for blocked in ("mcp_docker", "mcp_fetch", "mcp_postgres"):
        assert blocked.lower() in content.lower(), (
            f"Expected permanently blocked tool '{blocked}' to be listed"
        )


def test_report_safe_phase2_candidates_named():
    """Report must name specific safe first-candidate tools for Phase 2 allowlisting."""
    content = _report_text()
    # Phase 2 candidates are named in Section 5.3
    assert "mcp_filesystem_read_file" in content, (
        "mcp_filesystem_read_file must be named as a Phase 2 safe candidate"
    )
    assert "mcp_filesystem_list_directory" in content, (
        "mcp_filesystem_list_directory must be named as a Phase 2 safe candidate"
    )


def test_report_references_security_gate():
    """Report must reference the existing security_gate.py to stay grounded in the codebase."""
    content = _report_text()
    assert re.search(r"security_gate\.py", content), (
        "Report must reference security_gate.py in its analysis"
    )


def test_report_contains_wp_id():
    """Report must reference its own WP ID for traceability."""
    content = _report_text()
    assert "DOC-012" in content, (
        "research-report.md must contain the WP ID DOC-012"
    )


def test_report_zone_check_limitations_documented():
    """Section 3 must discuss symlink bypass as a limitation of zone-checking."""
    content = _report_text()
    assert re.search(r"(?i)symlink|canonicalis|path.traversal", content), (
        "Zone-checking limitations must address symlink / path canonicalisation risks"
    )


def test_report_allowlist_configuration_field_names_present():
    """Configuration schema in Section 4 must include the required field names."""
    content = _report_text()
    for field in ("allowed_tools", "zone_check_required"):
        assert field in content, (
            f"Configuration schema must include '{field}' field"
        )


def test_report_tier_classification_has_four_tiers():
    """Section 4.4 must define at least four tiers."""
    content = _report_text()
    # Tier 1 through Tier 4 should appear
    for tier in ("Tier 1", "Tier 2", "Tier 3", "Tier 4"):
        assert tier in content, (
            f"Tier classification must include '{tier}'"
        )


# ---------------------------------------------------------------------------
# Dev-log integrity tests
# ---------------------------------------------------------------------------

def test_devlog_exists():
    """dev-log.md must exist for DOC-012."""
    assert DEV_LOG_PATH.exists(), "dev-log.md not found for DOC-012"


def test_devlog_references_wp_id():
    """dev-log.md must reference DOC-012 for traceability."""
    content = _devlog_text()
    assert "DOC-012" in content, "dev-log.md must contain the WP ID DOC-012"


def test_devlog_lists_files_changed():
    """dev-log.md must include a files-changed table."""
    content = _devlog_text()
    assert re.search(r"(?i)files.changed|file.*change", content), (
        "dev-log.md must contain a files-changed section"
    )
