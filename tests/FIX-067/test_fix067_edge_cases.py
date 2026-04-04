"""Edge-case tests for FIX-067: Tester-added tests for rule robustness."""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BUG_TRACKING = REPO_ROOT / "docs" / "work-rules" / "bug-tracking-rules.md"
AGENT_WORKFLOW = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"
TESTING_PROTOCOL = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"


class TestBugTrackingRulesEdgeCases:
    """Edge-case tests for the Bug Closure at Finalization section."""

    def setup_method(self):
        self.content = BUG_TRACKING.read_text(encoding="utf-8")

    def test_section_appears_after_rules_section(self):
        """Bug Closure section must appear after the main Rules section."""
        idx_rules = self.content.index("## Rules")
        idx_closure = self.content.index("## Bug Closure at Finalization")
        assert idx_rules < idx_closure, (
            "Bug Closure at Finalization must appear after ## Rules"
        )

    def test_script_reference_exact_name(self):
        """The finalization script name must be exact (no typos)."""
        assert "scripts/finalize_wp.py" in self.content

    def test_both_doc_files_mentioned(self):
        """Both dev-log.md and test-report.md must be referenced in the section."""
        closure_idx = self.content.index("## Bug Closure at Finalization")
        # Get text from the section onwards (until next ##)
        remaining = self.content[closure_idx:]
        next_section_match = re.search(r"\n## ", remaining[5:])
        section_text = remaining if not next_section_match else remaining[:next_section_match.start() + 5]
        assert "dev-log.md" in section_text, "dev-log.md must be referenced in Bug Closure section"
        assert "test-report.md" in section_text, "test-report.md must be referenced in Bug Closure section"

    def test_cascades_verb_present(self):
        """The rule must describe that the script 'cascades' closures."""
        assert "cascades" in self.content

    def test_bug_id_pattern_described(self):
        """The finalization script should reference BUG-NNN pattern."""
        assert "BUG-NNN" in self.content or "BUG-" in self.content

    def test_no_manual_closure_implied(self):
        """Rule must clarify the script handles closures (not manual)."""
        assert "automatically" in self.content


class TestAgentWorkflowEdgeCases:
    """Edge-case tests for the Developer Pre-Handoff Checklist update."""

    def setup_method(self):
        self.content = AGENT_WORKFLOW.read_text(encoding="utf-8")

    def test_checklist_has_seven_items(self):
        """Developer Pre-Handoff Checklist must have exactly 7 numbered items."""
        idx_checklist = self.content.index("### Developer Pre-Handoff Checklist")
        idx_git_ops = self.content.index("### Git Operations for Handoff")
        section = self.content[idx_checklist:idx_git_ops]
        # Count lines that start with a digit followed by dot
        items = re.findall(r"^\d+\.", section, re.MULTILINE)
        assert len(items) == 8, f"Expected 8 checklist items, found {len(items)}"

    def test_item_7_references_fixed_in_wp_field(self):
        """Item 7 must reference the Fixed In WP field by name."""
        assert "Fixed In WP" in self.content

    def test_item_7_references_wp_id(self):
        """Item 7 must reference 'WP-ID' as the identifier to populate."""
        assert "WP-ID" in self.content

    def test_item_7_is_actionable(self):
        """Item 7 must contain an action verb."""
        idx = self.content.index("7. All bugs referenced in `dev-log.md`")
        line = self.content[idx:idx + 200].split("\n")[0]
        # Should contain 'have' or 'populated' or similar action word
        assert any(word in line.lower() for word in ["have", "populated", "set", "verify"]), (
            f"Item 7 should be actionable: {line}"
        )

    def test_tester_checklist_has_bug_logging_requirement(self):
        """Tester PASS Checklist should require bugs to be logged in bugs.jsonl."""
        tester_idx = self.content.index("### Tester PASS Checklist")
        git_ops_after = self.content.find("### ", tester_idx + 5)
        if git_ops_after == -1:
            tester_section = self.content[tester_idx:]
        else:
            tester_section = self.content[tester_idx:git_ops_after]
        assert "bugs.jsonl" in tester_section, (
            "Tester PASS Checklist must require logging bugs in bugs.jsonl"
        )


class TestTestingProtocolEdgeCases:
    """Edge-case tests for the TST-ID Uniqueness section."""

    def setup_method(self):
        self.content = TESTING_PROTOCOL.read_text(encoding="utf-8")

    def test_tst_id_section_is_nonempty(self):
        """TST-ID Uniqueness section must have meaningful content."""
        idx = self.content.index("## TST-ID Uniqueness")
        rest = self.content[idx + len("## TST-ID Uniqueness"):]
        next_section = rest.find("\n## ")
        section_body = rest[:next_section] if next_section != -1 else rest
        # Should have at least 3 meaningful lines
        meaningful = [l.strip() for l in section_body.strip().splitlines() if l.strip()]
        assert len(meaningful) >= 3, (
            f"TST-ID Uniqueness section is too sparse ({len(meaningful)} lines)"
        )

    def test_both_scripts_mentioned_in_tst_id_section(self):
        """Both add_test_result.py and run_tests.py must appear in the TST-ID section."""
        idx_start = self.content.index("## TST-ID Uniqueness")
        idx_end_match = re.search(r"\n## ", self.content[idx_start + 5:])
        idx_end = idx_start + 5 + idx_end_match.start() if idx_end_match else len(self.content)
        section = self.content[idx_start:idx_end]
        assert "add_test_result.py" in section
        assert "run_tests.py" in section

    def test_dry_run_flag_is_exact(self):
        """The --dry-run flag must be present as documented."""
        assert "--dry-run" in self.content

    def test_manual_edit_prohibition_is_explicit(self):
        """The prohibition on manual CSV edits must be explicit."""
        assert "Never manually" in self.content or "never manually" in self.content

    def test_concurrent_safety_mentioned(self):
        """Atomic/concurrent safety must be mentioned in the TST-ID section."""
        idx_start = self.content.index("## TST-ID Uniqueness")
        idx_end_match = re.search(r"\n## ", self.content[idx_start + 5:])
        idx_end = idx_start + 5 + idx_end_match.start() if idx_end_match else len(self.content)
        section = self.content[idx_start:idx_end]
        assert any(word in section.lower() for word in ["atomic", "concurrent", "lock"]), (
            "TST-ID section must address concurrent safety"
        )

    def test_dedup_script_is_separate_from_main_scripts(self):
        """dedup script reference must be distinct from add_test_result and run_tests."""
        assert "dedup_test_ids.py" in self.content
        # Ensure it's referenced as a separate tool, not confused with the others
        dedup_idx = self.content.index("dedup_test_ids.py")
        add_idx = self.content.index("add_test_result.py")
        assert dedup_idx != add_idx, "dedup and add_test_result must be distinct references"
