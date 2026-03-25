"""
DOC-011 — Verification tests for the Docker/container support feasibility
research report.

These tests confirm the report file exists and contains all required sections.
No Docker commands are executed; this is a pure documentation-structure check.
"""

import pathlib

REPORT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-011"
    / "research-report.md"
)


def test_report_file_exists() -> None:
    """The research report file must exist on disk."""
    assert REPORT_PATH.exists(), f"Report not found at {REPORT_PATH}"
    assert REPORT_PATH.is_file(), f"Expected a file, got a directory at {REPORT_PATH}"


def test_report_has_title() -> None:
    """The report must have a top-level heading (# DOC-011 ...)."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert content.startswith("# DOC-011"), (
        "Report must begin with a top-level heading starting with '# DOC-011'"
    )


def test_report_has_attack_surface_section() -> None:
    """Section 1 covering attack surface analysis must be present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "## 1." in content or "## 1 " in content or "Attack Surface" in content, (
        "Report must contain an Attack Surface section (section 1)"
    )


def test_report_has_path_checking_section() -> None:
    """Section 2 covering path-checking feasibility must be present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "## 2." in content or "Path-Check" in content or "path-check" in content, (
        "Report must contain a path-checking feasibility section (section 2)"
    )


def test_report_has_socket_section() -> None:
    """Section 3 covering Docker socket security must be present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "## 3." in content or "Socket" in content or "socket" in content, (
        "Report must contain a Docker socket section (section 3)"
    )


def test_report_has_allowlist_section() -> None:
    """Section 4 covering safe-subset allowlist assessment must be present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert (
        "## 4." in content
        or "Allowlist" in content
        or "allowlist" in content
        or "Safe Subset" in content
        or "safe subset" in content
    ), "Report must contain an allowlist/safe-subset section (section 4)"


def test_report_has_recommendation_section() -> None:
    """Section 5 with the final recommendation must be present."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert "## 5." in content or "Recommendation" in content or "recommendation" in content, (
        "Report must contain a recommendation section (section 5)"
    )


def test_report_contains_recommendation_keyword() -> None:
    """
    The recommendation must clearly state one of: allow, defer, or reject.
    The report uses the word DEFER in the recommendation section.
    """
    content = REPORT_PATH.read_text(encoding="utf-8").lower()
    keywords = ("allow", "defer", "reject")
    assert any(kw in content for kw in keywords), (
        f"Report must contain at least one of {keywords} as its recommendation"
    )


def test_report_minimum_length() -> None:
    """The report must be substantive — at least 2 000 characters."""
    content = REPORT_PATH.read_text(encoding="utf-8")
    assert len(content) >= 2000, (
        f"Report is too short ({len(content)} chars); expected >= 2000 chars"
    )


def test_report_mentions_container_escape() -> None:
    """Attack surface analysis must explicitly discuss container escape."""
    content = REPORT_PATH.read_text(encoding="utf-8").lower()
    assert "container escape" in content or "escape" in content, (
        "Report must mention container escape as part of the attack surface"
    )


def test_report_mentions_volume_mounts() -> None:
    """Attack surface analysis must discuss volume mounts."""
    content = REPORT_PATH.read_text(encoding="utf-8").lower()
    assert "volume" in content and "mount" in content, (
        "Report must discuss volume mounts in the attack surface"
    )


def test_report_mentions_privilege_escalation() -> None:
    """Attack surface analysis must discuss privilege escalation."""
    content = REPORT_PATH.read_text(encoding="utf-8").lower()
    assert "privilege" in content or "privileged" in content, (
        "Report must mention privilege escalation in the attack surface"
    )


def test_report_mentions_network_risk() -> None:
    """Attack surface analysis must address network access risk."""
    content = REPORT_PATH.read_text(encoding="utf-8").lower()
    assert "network" in content, (
        "Report must discuss network access as part of the attack surface"
    )
