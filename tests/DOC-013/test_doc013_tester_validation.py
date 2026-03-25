"""
Tester validation tests for DOC-013: Multi-Agent Counter Coordination Research Report

Additional edge-case and quality tests beyond the Developer's structural checks.
These validate content depth, cross-references, acceptance criteria coverage,
and report completeness.
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

DEVLOG_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-013"
    / "dev-log.md"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _devlog_text() -> str:
    return DEVLOG_PATH.read_text(encoding="utf-8")


# --- Acceptance Criteria Coverage (US-034 criterion 6) ---

class TestAcceptanceCriteriaCoverage:
    """US-034 AC6: The design is backed by documented handling for session
    identification, multi-agent coordination, and audit logging decisions."""

    def test_session_identification_documented(self):
        """Report must document how session identification works (AC6 - session)."""
        content = _report_text()
        assert re.search(r"(?i)_get_session_id|session.*resolution|session.*identif", content)

    def test_multi_agent_coordination_documented(self):
        """Report must document multi-agent coordination approach (AC6 - coordination)."""
        content = _report_text()
        assert re.search(r"(?i)multi.agent|subagent.*counter|counter.*coordination", content)

    def test_otel_session_mechanism_explained(self):
        """Report must explain the OTel-based session identification mechanism."""
        content = _report_text()
        assert re.search(r"(?i)otel.*jsonl|copilot.otel|opentelemetry", content), (
            "Report must explain the OTel JSONL session identification"
        )

    def test_fallback_uuid_mechanism_explained(self):
        """Report must document the UUID4 fallback session ID path."""
        content = _report_text()
        assert re.search(r"(?i)uuid4|uuid.*fallback|fallback.*uuid|_fallback_session_id", content), (
            "Report must document the UUID4 fallback session ID mechanism"
        )


# --- Report Quality and Depth ---

class TestReportQuality:
    """Validate the report has sufficient depth and structure."""

    def test_report_has_executive_summary(self):
        """Research report should have an executive summary."""
        content = _report_text()
        assert re.search(r"(?i)executive summary|## summary", content), (
            "Report should have an executive summary or summary section"
        )

    def test_report_minimum_word_count(self):
        """Research report must be substantial (>800 words)."""
        content = _report_text()
        word_count = len(content.split())
        assert word_count > 800, (
            f"Report has only {word_count} words; expected >800 for a thorough analysis"
        )

    def test_report_has_pros_and_cons(self):
        """Each option should have pros and cons listed."""
        content = _report_text()
        assert re.search(r"(?i)\*\*pros", content), "Report must list pros for options"
        assert re.search(r"(?i)\*\*cons", content), "Report must list cons for options"

    def test_report_has_summary_table(self):
        """Report should have a findings summary (table or list)."""
        content = _report_text()
        assert re.search(r"(?i)summary.*finding|finding.*summary|summary of finding", content), (
            "Report should have a summary of findings"
        )

    def test_report_has_references_section(self):
        """Report must have a references section citing source files."""
        content = _report_text()
        assert re.search(r"(?i)## references|## sources", content), (
            "Report must have a references section"
        )


# --- Cross-Reference Accuracy ---

class TestCrossReferences:
    """Validate cross-references to other workpackages and files are accurate."""

    def test_references_saf036(self):
        """Report must reference SAF-036 (counter configuration)."""
        content = _report_text()
        assert re.search(r"SAF-036|SAF.036", content), (
            "Report must reference SAF-036 (counter configuration)"
        )

    def test_references_counter_config_json(self):
        """Report must reference counter_config.json."""
        content = _report_text()
        assert re.search(r"counter_config\.json", content), (
            "Report must reference counter_config.json"
        )

    def test_references_security_gate_py(self):
        """Report must reference security_gate.py."""
        content = _report_text()
        assert re.search(r"security_gate\.py", content), (
            "Report must reference security_gate.py"
        )

    def test_references_user_story(self):
        """Report must reference its linked user story US-034."""
        content = _report_text()
        assert re.search(r"US-034|US.034", content), (
            "Report must reference linked user story US-034"
        )


# --- Security Analysis Depth ---

class TestSecurityAnalysisDepth:
    """Validate the security analysis is thorough enough."""

    def test_threat_model_present(self):
        """Report must include a threat model or attack scenario."""
        content = _report_text()
        assert re.search(r"(?i)threat model|threat actor|attack.*vector|attack.*scenario", content), (
            "Report must document a threat model or attack scenario"
        )

    def test_owasp_reference(self):
        """Report must reference OWASP for the bypass risk framing."""
        content = _report_text()
        assert re.search(r"(?i)owasp", content), (
            "Report must reference OWASP for authoritative security framing"
        )

    def test_all_three_options_security_assessed(self):
        """Bypass analysis table must cover all three options."""
        content = _report_text()
        # Check that the bypass analysis mentions feasibility for each option
        assert re.search(r"(?i)option a.*not feasible|shared.*not feasible", content), (
            "Option A must be assessed as not exploitable"
        )
        assert re.search(r"(?i)option b.*feasible|independent.*feasible|option b.*bypass", content), (
            "Option B must be assessed for exploit feasibility"
        )
        assert re.search(r"(?i)option c.*feasible|no counter.*feasible|trivial", content), (
            "Option C must be assessed for exploit feasibility"
        )

    def test_residual_risk_documented(self):
        """Report should address residual risks with the recommended approach."""
        content = _report_text()
        assert re.search(r"(?i)residual risk|remaining risk|mitigation|mitigat", content), (
            "Report should document residual risks and mitigations"
        )


# --- WP Description Questions Answered ---

class TestWPQuestionsAnswered:
    """Verify each question from the WP description is explicitly addressed."""

    def test_q1_subagent_distinction(self):
        """WP Q1: Does VS Code distinguish main agents from subagents in payloads?"""
        content = _report_text()
        # Must contain an explicit negative answer
        assert re.search(
            r"(?i)does not.*distinguish|no.*distinguish|not.*distinguis|identical.*schema",
            content,
        ), "Must explicitly state VS Code does not distinguish agent types in payloads"

    def test_q2_shared_vs_independent_evaluated(self):
        """WP Q2: Shared vs independent vs no-counter options all evaluated."""
        content = _report_text()
        assert "Option A" in content or "shared counter" in content.lower()
        assert "Option B" in content or "independent counter" in content.lower()
        assert "Option C" in content or "no counter" in content.lower()

    def test_q3_bypass_risk_assessed(self):
        """WP Q3: Can a rogue agent spawn subagents to bypass the counter?"""
        content = _report_text()
        assert re.search(
            r"(?i)rogue.*agent.*spawn|spawn.*subagent.*bypass|bypass.*subagent.*spawn",
            content,
        ), "Must address whether a rogue agent can spawn subagents to bypass"

    def test_q4_recommendation_balances_security_and_workflow(self):
        """WP Q4: Recommendation balances security with development workflow."""
        content = _report_text()
        assert re.search(r"(?i)workflow", content), (
            "Recommendation must address workflow impact"
        )
        assert re.search(r"(?i)secur", content), (
            "Recommendation must address security"
        )


# --- Dev-Log Consistency ---

class TestDevLogConsistency:
    """Verify dev-log.md is consistent with the research report."""

    def test_devlog_exists(self):
        """Dev-log must exist."""
        assert DEVLOG_PATH.exists()

    def test_devlog_is_not_empty(self):
        """Dev-log must have content."""
        content = _devlog_text()
        assert len(content.strip()) > 100

    def test_devlog_references_report(self):
        """Dev-log must reference the research report."""
        content = _devlog_text()
        assert re.search(r"research.report\.md|research report", content, re.IGNORECASE)

    def test_devlog_mentions_key_findings(self):
        """Dev-log summary should align with report conclusions."""
        content = _devlog_text()
        # Dev-log should mention the shared counter recommendation
        assert re.search(r"(?i)shared counter|option a", content), (
            "Dev-log must summarize the shared counter recommendation"
        )

    def test_no_tmp_files_in_wp_folder(self):
        """No temporary files should remain in the WP folder."""
        wp_dir = REPORT_PATH.parent
        for f in wp_dir.iterdir():
            assert not f.name.startswith("tmp_"), (
                f"Temporary file {f.name} found in WP folder"
            )

    def test_no_tmp_files_in_test_folder(self):
        """No temporary files should remain in the test folder."""
        test_dir = pathlib.Path(__file__).parent
        for f in test_dir.iterdir():
            if f.is_file():
                assert not f.name.startswith("tmp_"), (
                    f"Temporary file {f.name} found in test folder"
                )
