"""Tests for DOC-016: Windows code signing research report."""
import os
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "docs" / "plans" / "windows-code-signing.md"


def _read_report() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_file_exists():
    assert REPORT_PATH.exists(), f"Report not found at {REPORT_PATH}"


def test_report_is_nonempty():
    content = _read_report()
    assert len(content) >= 500, "Report is too short — expected at least 500 characters"


def test_report_has_setup_section():
    content = _read_report()
    assert "Setup" in content or "setup" in content, "Report must contain setup information"


def test_report_has_ci_integration_section():
    content = _read_report()
    assert "CI" in content or "ci" in content.lower(), "Report must contain CI integration content"
    assert "github-action" in content.lower() or "workflow" in content.lower() or "actions" in content.lower(), \
        "Report must describe GitHub Actions / workflow integration"


def test_report_has_recommendation_section():
    content = _read_report()
    assert "Recommendation" in content or "recommendation" in content, \
        "Report must contain a recommendation section"
    assert "SignPath" in content, "Recommendation must reference the recommended service (SignPath)"


def test_report_has_comparison_matrix():
    content = _read_report()
    # A markdown table has rows with pipe characters
    table_rows = [line for line in content.splitlines() if "|" in line]
    assert len(table_rows) >= 5, "Report must contain a comparison table (at least 5 table rows)"


def test_report_has_signpath_coverage():
    content = _read_report()
    assert "SignPath" in content, "Report must evaluate SignPath.io"
    assert "signpath.io" in content.lower() or "signpath" in content.lower()


def test_report_has_azure_coverage():
    content = _read_report()
    assert "Azure" in content, "Report must evaluate Azure Trusted Signing"


def test_report_has_sslcom_coverage():
    content = _read_report()
    assert "SSL.com" in content or "ssl.com" in content.lower(), "Report must evaluate SSL.com"


def test_report_has_certificate_management():
    content = _read_report()
    assert "certificate" in content.lower() or "Certificate" in content, \
        "Report must address certificate management"


def test_report_has_references():
    content = _read_report()
    assert "Reference" in content or "reference" in content or "http" in content, \
        "Report must include references or URLs"
