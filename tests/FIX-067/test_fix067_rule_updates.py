"""Tests for FIX-067: Verify bug-closure and TST-ID rules were added to rule files."""

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestBugTrackingRules:
    """Verify bug-tracking-rules.md has the Bug Closure at Finalization section."""

    def setup_method(self):
        self.content = (REPO_ROOT / "docs" / "work-rules" / "bug-tracking-rules.md").read_text(encoding="utf-8")

    def test_section_heading_exists(self):
        assert "## Bug Closure at Finalization" in self.content

    def test_fixed_in_wp_rule(self):
        assert "`Fixed In WP`" in self.content
        assert "populated with the WP-ID" in self.content

    def test_status_closed_rule(self):
        assert "`Status`" in self.content
        assert "set to `Closed`" in self.content

    def test_finalization_script_reference(self):
        assert "scripts/finalize_wp.py" in self.content
        assert "cascades closures" in self.content

    def test_developer_verification_requirement(self):
        assert "Developers must verify bug linkage before handoff" in self.content


class TestAgentWorkflowChecklist:
    """Verify agent-workflow.md checklist includes bug linkage step."""

    def setup_method(self):
        self.content = (REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md").read_text(encoding="utf-8")

    def test_bug_linkage_checklist_item(self):
        assert "All bugs referenced in `dev-log.md` have `Fixed In WP` populated with this WP-ID" in self.content

    def test_checklist_item_numbering(self):
        # Item 7 should be the bug linkage step
        assert "7. All bugs referenced in `dev-log.md`" in self.content

    def test_checklist_item_in_pre_handoff_section(self):
        # The bug linkage item must appear between the checklist header and Git Operations
        idx_checklist = self.content.index("### Developer Pre-Handoff Checklist")
        idx_git_ops = self.content.index("### Git Operations for Handoff")
        idx_bug_item = self.content.index("All bugs referenced in `dev-log.md` have `Fixed In WP`")
        assert idx_checklist < idx_bug_item < idx_git_ops


class TestTestingProtocolTstId:
    """Verify testing-protocol.md has the TST-ID Uniqueness section."""

    def setup_method(self):
        self.content = (REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md").read_text(encoding="utf-8")

    def test_section_heading_exists(self):
        assert "## TST-ID Uniqueness" in self.content

    def test_no_manual_rows_rule(self):
        assert "Never manually add" in self.content
        assert "test-results.jsonl" in self.content

    def test_script_usage_rule(self):
        assert "scripts/add_test_result.py" in self.content
        assert "scripts/run_tests.py" in self.content

    def test_atomic_id_assignment_mention(self):
        assert "locked_next_id_and_append()" in self.content

    def test_dedup_script_reference(self):
        assert "scripts/dedup_test_ids.py --dry-run" in self.content

    def test_section_after_csv_table(self):
        # TST-ID Uniqueness must appear after the Test Result JSONL table
        idx_csv_table = self.content.index("## Test Result JSONL")
        idx_tst_id = self.content.index("## TST-ID Uniqueness")
        idx_report_format = self.content.index("## Test Report Format")
        assert idx_csv_table < idx_tst_id < idx_report_format
