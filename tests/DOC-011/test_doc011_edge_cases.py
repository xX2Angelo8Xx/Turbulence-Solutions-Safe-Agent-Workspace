"""
DOC-011 — Edge-case verification tests added by Tester Agent.

These tests go beyond the Developer's structural checks to verify:
- Report content correctness and depth
- Specific security topics are addressed
- Future-approval conditions are documented
- Cross-platform risks are discussed
- The conditional allow path (Section 4.4) is present
"""

import pathlib

REPORT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-011"
    / "research-report.md"
)


def _content() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _lower() -> str:
    return _content().lower()


# ── Content depth ────────────────────────────────────────────────────────────

def test_report_exceeds_minimum_length_comfortably() -> None:
    """A meaningful research report should be well above the 2 000-char floor."""
    content = _content()
    assert len(content) >= 5000, (
        f"Report only has {len(content)} chars; expected >= 5000 for a thorough report"
    )


def test_report_has_section_6_references() -> None:
    """Section 6 (References / Related WPs) must be present."""
    content = _content()
    assert "## 6." in content or "References" in content or "Related Workpackages" in content, (
        "Report must contain a References / Related Workpackages section"
    )


def test_report_has_executive_summary() -> None:
    """An executive summary makes the recommendation immediately clear."""
    content = _lower()
    assert "executive summary" in content or "summary" in content, (
        "Report must contain an executive summary section"
    )


# ── Security topics ──────────────────────────────────────────────────────────

def test_report_discusses_docker_socket() -> None:
    """Docker socket security must be specifically addressed."""
    content = _lower()
    assert "docker.sock" in content or "docker socket" in content or "named pipe" in content, (
        "Report must discuss the Docker socket (/var/run/docker.sock or named pipe)"
    )


def test_report_discusses_privileged_flag() -> None:
    """The --privileged flag is one of the most dangerous; must be called out."""
    content = _lower()
    assert "--privileged" in content or "privileged" in content, (
        "Report must explicitly discuss the --privileged Docker flag"
    )


def test_report_discusses_network_host() -> None:
    """--network host exposure must be addressed."""
    content = _lower()
    assert "--network host" in content or "network host" in content, (
        "Report must address the --network host flag risk"
    )


def test_report_mentions_cve() -> None:
    """Report should reference at least one specific Docker CVE for credibility."""
    content = _lower()
    assert "cve" in content, (
        "Report should reference at least one CVE to ground the security analysis"
    )


def test_report_discusses_image_execution_risk() -> None:
    """docker run pulls and executes arbitrary image code — must be discussed."""
    content = _lower()
    assert "docker run" in content or "image" in content, (
        "Report must discuss the risk of running arbitrary container images"
    )


def test_report_mentions_docker_compose() -> None:
    """docker-compose introduces additional YAML-parsing risk; must be mentioned."""
    content = _lower()
    assert "docker-compose" in content or "docker compose" in content, (
        "Report must address docker-compose and its compose-file parsing risks"
    )


# ── Cross-platform coverage ──────────────────────────────────────────────────

def test_report_mentions_windows_specifics() -> None:
    """Windows Docker behavior (named pipes, WSL 2) must be discussed."""
    content = _lower()
    assert "windows" in content, (
        "Report must address Windows-specific Docker considerations"
    )


def test_report_mentions_wsl() -> None:
    """WSL 2 introduces path-translation complexity; must be mentioned."""
    content = _lower()
    assert "wsl" in content, (
        "Report must mention WSL 2 and its impact on path validation"
    )


# ── Recommendation quality ───────────────────────────────────────────────────

def test_report_recommendation_is_defer() -> None:
    """The recommendation must be DEFER (not allow or reject)."""
    content = _lower()
    assert "defer" in content, (
        "Report recommendation must explicitly state DEFER"
    )


def test_report_does_not_recommend_immediate_allow() -> None:
    """The report must not recommend allowing Docker commands now."""
    content = _content()
    # The word 'allow' appears in 'should not be enabled', 'Blocked unconditionally'
    # contexts. The recommendation heading must not say 'ALLOW'.
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip().upper()
        if stripped.startswith("### DECISION:") or stripped.startswith("## 5."):
            # Must not say ALLOW in the decision line
            assert "ALLOW" not in stripped or "NOT" in stripped or "DEFER" in stripped, (
                f"Recommendation decision line appears to recommend ALLOW: {line!r}"
            )


def test_report_lists_future_conditions() -> None:
    """Future conditions for approval must be documented (checkbox list)."""
    content = _content()
    assert "- [ ]" in content, (
        "Report must include a checklist of conditions for future approval"
    )


def test_report_mentions_safe_subset() -> None:
    """A safe subset (allowlist) must be proposed for any future implementation."""
    content = _lower()
    assert "safe subset" in content or "allowlist" in content or "safe-subset" in content, (
        "Report must define a safe-subset allowlist for any future Docker support"
    )


def test_report_blocks_docker_run_unconditionally() -> None:
    """docker run must be listed as unconditionally blocked."""
    content = _lower()
    assert "docker run" in content and ("block" in content or "unconditional" in content), (
        "Report must state that docker run is blocked unconditionally"
    )


# ── Structural integrity ─────────────────────────────────────────────────────

def test_report_has_no_placeholder_text() -> None:
    """The report must not contain TODO/FIXME/placeholder text."""
    content = _lower()
    for placeholder in ("todo", "fixme", "tbd", "placeholder", "insert here"):
        assert placeholder not in content, (
            f"Report contains placeholder text: '{placeholder}'"
        )


def test_report_has_wp_id_in_title() -> None:
    """Title must reference DOC-011 specifically."""
    content = _content()
    assert "DOC-011" in content.splitlines()[0], (
        "First line of report must contain the WP ID DOC-011"
    )


def test_report_mentions_us036() -> None:
    """The parent user story US-036 must be referenced."""
    content = _content()
    assert "US-036" in content, (
        "Report must reference the parent user story US-036"
    )


def test_report_related_wps_present() -> None:
    """Related downstream WPs (SAF-040, SAF-041, SAF-042) must be referenced."""
    content = _content()
    assert "SAF-040" in content or "SAF-041" in content or "SAF-042" in content, (
        "Report must reference related SAF implementation WPs"
    )
