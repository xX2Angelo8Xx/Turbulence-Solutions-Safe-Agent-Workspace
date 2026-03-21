"""
Tester edge-case tests for DOC-010: Research VS Code PreToolUse session ID.

These supplement the developer tests with boundary conditions, encoding checks,
and deeper content-validation scenarios.
"""

import re
from pathlib import Path

REPORT_PATH = Path("docs/workpackages/DOC-010/dev-log.md")


def _content():
    return REPORT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# TestReportEncoding
# ---------------------------------------------------------------------------

class TestReportEncoding:
    def test_report_is_utf8_decodable(self):
        """File must be readable as UTF-8 without errors."""
        raw = REPORT_PATH.read_bytes()
        decoded = raw.decode("utf-8")
        assert len(decoded) > 0

    def test_report_has_no_null_bytes(self):
        """File must not contain null bytes (binary corruption indicator)."""
        raw = REPORT_PATH.read_bytes()
        assert b"\x00" not in raw, "Report file contains null bytes — possible binary corruption"


# ---------------------------------------------------------------------------
# TestReportComprehensiveness
# ---------------------------------------------------------------------------

class TestReportComprehensiveness:
    def test_report_exceeds_minimum_length(self):
        """Research report must be substantial — at least 5 000 characters."""
        content = _content()
        assert len(content) >= 5000, (
            f"Report is only {len(content)} chars — expected at least 5000 for a "
            f"research deliverable"
        )

    def test_report_contains_no_fewer_than_five_strategies(self):
        """Report must evaluate at least 5 alternative strategies (A–E)."""
        content = _content()
        strategy_labels = re.findall(r"Strategy\s+[A-E]\b", content)
        unique = set(strategy_labels)
        assert len(unique) >= 5, (
            f"Found only {len(unique)} Strategy labels (A–E expected) — "
            f"got: {sorted(unique)}"
        )

    def test_report_contains_pros_and_cons_language(self):
        """Each strategy evaluation must discuss trade-offs (pros/cons/advantage/disadvantage)."""
        content = _content()
        tradeoff_words = re.findall(
            r"\b(pros?|cons?|advantage|disadvantage|drawback|downside|upside|trade.off)\b",
            content, re.IGNORECASE
        )
        assert len(tradeoff_words) >= 3, (
            f"Report mentions trade-off language only {len(tradeoff_words)} time(s) — "
            f"strategies must be evaluated with clear pros/cons"
        )

    def test_report_no_placeholder_text(self):
        """Report must not contain lorem ipsum or TODO placeholder text."""
        content = _content()
        placeholders = re.findall(r"\bTODO\b|\blorem ipsum\b|\bfixme\b|\bxxx\b", content, re.IGNORECASE)
        assert not placeholders, f"Report contains placeholder text: {placeholders}"


# ---------------------------------------------------------------------------
# TestPayloadAbsenceFindings
# ---------------------------------------------------------------------------

class TestPayloadAbsenceFindings:
    """Verify the report correctly documents the absence of session ID in payload."""

    def test_no_session_id_finding_explicit(self):
        """Report must explicitly state session/conversation ID is absent."""
        content = _content()
        # Should say "does not" or "no session" or "absent" near "session"
        assert re.search(
            r"(does not|no|not include|not contain|absent|missing).{0,60}session.{0,15}id",
            content, re.IGNORECASE
        ), "Report did not explicitly confirm session ID is absent from payload"

    def test_payload_field_tool_name_documented(self):
        """Payload field 'tool_name' must be documented."""
        content = _content()
        assert "tool_name" in content, "Payload field 'tool_name' not documented"

    def test_payload_field_tool_input_documented(self):
        """Payload field 'tool_input' must be documented."""
        content = _content()
        assert "tool_input" in content, "Payload field 'tool_input' not documented"

    def test_payload_schema_uses_json_or_code_block(self):
        """Payload schema must be shown in a code/JSON block."""
        content = _content()
        json_block = re.search(r"```(json)?\s*\{[^`]+\}", content, re.DOTALL)
        assert json_block, "Payload schema not presented in a code/JSON block"

    def test_vscode_pid_alternative_mentioned(self):
        """VSCODE_PID environment variable strategy must be mentioned."""
        content = _content()
        assert "VSCODE_PID" in content, "VSCODE_PID strategy not mentioned"

    def test_time_window_strategy_detail(self):
        """Time-Window strategy must be described with enough detail (mentions minutes or seconds)."""
        content = _content()
        assert re.search(r"\d+.{0,5}(minute|second|min\b)", content, re.IGNORECASE), (
            "Time-Window strategy must specify a duration (e.g. 30 minutes)"
        )

    def test_report_references_hook_execution_context(self):
        """Report must explain where hooks execute relative to VS Code process."""
        content = _content()
        assert re.search(r"(hook|script).{0,40}(process|execut|spawn|child|subprocess)", content, re.IGNORECASE), (
            "Report should describe the hook execution context (subprocess/process relationship)"
        )


# ---------------------------------------------------------------------------
# TestStateFileLocation
# ---------------------------------------------------------------------------

class TestStateFileLocation:
    def test_state_file_path_mentioned(self):
        """Implementation notes must reference a .hook_state.json state file."""
        content = _content()
        assert ".hook_state.json" in content, (
            "Implementation notes must mention .hook_state.json state file"
        )

    def test_state_file_location_in_hooks_directory(self):
        """State file path should be in the .github/hooks/ directory."""
        content = _content()
        assert re.search(r"\.github.hooks", content, re.IGNORECASE), (
            "State file should be stored under .github/hooks/ per the project layout"
        )


# ---------------------------------------------------------------------------
# TestRejectedStrategiesReasoning
# ---------------------------------------------------------------------------

class TestRejectedStrategiesReasoning:
    @staticmethod
    def strategies_text():
        content = _content()
        m = re.search(
            r"### 3\. Alternative Session.Tracking Strategies(.*?)(?=^###|\Z)",
            content, re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        return m.group(1) if m else ""

    def test_hash_first_message_strategy_evaluated(self):
        """Strategy based on hashing first message must be present."""
        content = _content()
        assert re.search(r"hash.{0,30}(first|message|content)", content, re.IGNORECASE), (
            "Report should evaluate a hash-of-first-message strategy"
        )

    def test_timestamp_strategy_evaluated(self):
        """Timestamp-based window strategy must be explicitly evaluated."""
        content = _content()
        assert re.search(r"timestamp|time.window|time.based", content, re.IGNORECASE), (
            "Timestamp/time-window strategy must be explicitly evaluated"
        )

    def test_uuid_or_generated_id_strategy_evaluated(self):
        """A randomly generated / UUID-based session ID strategy must be evaluated."""
        content = _content()
        assert re.search(r"uuid|random.{0,10}id|generated.{0,10}id|state.file.{0,20}id", content, re.IGNORECASE), (
            "Report should evaluate a randomly generated / UUID-based session ID strategy"
        )

    def test_each_rejected_strategy_has_reason(self):
        """Non-recommended strategies must have documented reasons for rejection/lower ranking."""
        content = _content()
        # There should be multiple strategies explicitly characterised
        ranked_or_rejected = re.findall(
            r"(risk|unreliable|limitation|reject|not recommend|lower.ranked|ranked lower|drawback|concern)",
            content, re.IGNORECASE
        )
        assert len(ranked_or_rejected) >= 2, (
            f"Only {len(ranked_or_rejected)} rejection/ranking rationale(s) found — "
            f"each non-recommended strategy should explain why it was not chosen"
        )


# ---------------------------------------------------------------------------
# TestSourceCodeUnmodified
# ---------------------------------------------------------------------------

class TestSourceCodeUnmodified:
    def test_src_directory_not_modified_by_wp(self):
        """DOC-010 is a research WP — no files in src/ should have been added or modified."""
        import subprocess
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~2", "HEAD", "--", "src/"],
            capture_output=True, text=True
        )
        changed_src = [l for l in r.stdout.splitlines() if l.strip()]
        assert not changed_src, (
            f"Source files were modified by DOC-010 commits (research WP must not touch src/): "
            f"{changed_src}"
        )


# ---------------------------------------------------------------------------
# TestImplementationNotesCompleteness
# ---------------------------------------------------------------------------

class TestImplementationNotesCompleteness:
    def test_impl_notes_mention_deny_count(self):
        """Implementation notes must include deny_count field for SAF-035 state."""
        content = _content()
        assert "deny_count" in content, "Implementation notes must mention deny_count"

    def test_impl_notes_mention_locked_field(self):
        """Implementation notes must include locked field for session lockout."""
        content = _content()
        assert "locked" in content, "Implementation notes must mention locked field"

    def test_impl_notes_mention_timestamp_field(self):
        """Implementation notes must include timestamp for the time-window logic."""
        content = _content()
        assert "timestamp" in content, "Implementation notes must include timestamp field"

    def test_impl_notes_contain_lockout_message(self):
        """Implementation notes must include the lockout message wording."""
        content = _content()
        assert re.search(r"(locked|lock.out).{0,80}(session|chat|new)", content, re.IGNORECASE), (
            "Implementation notes must include lockout message instructing user to start new session"
        )

    def test_impl_notes_address_file_io_safety(self):
        """Implementation notes should address safe file I/O for the state file."""
        content = _content()
        assert re.search(r"(atomic|lock|safe|race|concurrent|write.{0,20}safe)", content, re.IGNORECASE), (
            "Implementation notes should address safe/atomic file I/O for .hook_state.json"
        )
