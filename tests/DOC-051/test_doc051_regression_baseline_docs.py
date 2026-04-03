"""
DOC-051 — Tests for regression baseline documentation.

Validates that:
- testing-protocol.md contains the required Regression Baseline section
- agent-workflow.md references tests/regression-baseline.json
- developer.agent.md references tests/regression-baseline.json (bug-fix checklist)
- The regression-baseline.json file itself has the documented schema fields
"""

import json
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

TESTING_PROTOCOL = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"
AGENT_WORKFLOW = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"
DEVELOPER_AGENT = REPO_ROOT / ".github" / "agents" / "developer.agent.md"
TESTER_AGENT = REPO_ROOT / ".github" / "agents" / "tester.agent.md"
ORCHESTRATOR_AGENT = REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md"
REGRESSION_BASELINE = REPO_ROOT / "tests" / "regression-baseline.json"


# ---------------------------------------------------------------------------
# testing-protocol.md — Regression Baseline section
# ---------------------------------------------------------------------------


def test_testing_protocol_has_regression_baseline_heading():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "## Regression Baseline" in content, (
        "testing-protocol.md must contain a '## Regression Baseline' section"
    )


def test_testing_protocol_documents_purpose():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "known-failing" in content or "known failing" in content, (
        "Regression Baseline section must describe known-failing tests"
    )


def test_testing_protocol_documents_schema_comment_field():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "_comment" in content, (
        "Regression Baseline section must document the '_comment' JSON field"
    )


def test_testing_protocol_documents_schema_count_field():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "_count" in content, (
        "Regression Baseline section must document the '_count' JSON field"
    )


def test_testing_protocol_documents_schema_updated_field():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "_updated" in content, (
        "Regression Baseline section must document the '_updated' JSON field"
    )


def test_testing_protocol_documents_schema_known_failures_field():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "known_failures" in content, (
        "Regression Baseline section must document the 'known_failures' JSON field"
    )


def test_testing_protocol_documents_when_to_update():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    # Section must mention update triggers
    assert "bug" in content.lower() and "fix" in content.lower() and "remov" in content.lower(), (
        "Regression Baseline section must explain when to remove entries (after bug fix)"
    )


def test_testing_protocol_documents_developer_role():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    # Must mention the Developer role in the baseline context
    baseline_section_idx = content.index("## Regression Baseline")
    section_text = content[baseline_section_idx:]
    assert "Developer" in section_text, (
        "Regression Baseline section must document the Developer's responsibility"
    )


def test_testing_protocol_documents_tester_role():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_section_idx = content.index("## Regression Baseline")
    section_text = content[baseline_section_idx:]
    assert "Tester" in section_text, (
        "Regression Baseline section must document the Tester's responsibility"
    )


def test_testing_protocol_documents_orchestrator_role():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_section_idx = content.index("## Regression Baseline")
    section_text = content[baseline_section_idx:]
    assert "Orchestrator" in section_text, (
        "Regression Baseline section must document the Orchestrator's responsibility"
    )


def test_testing_protocol_documents_file_path():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    assert "regression-baseline.json" in content, (
        "Regression Baseline section must reference the file path"
    )


def test_testing_protocol_documents_how_to_update():
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_section_idx = content.index("## Regression Baseline")
    section_text = content[baseline_section_idx:]
    assert "How to Update" in section_text or "how to update" in section_text.lower(), (
        "Regression Baseline section must describe how to perform an update"
    )


# ---------------------------------------------------------------------------
# agent-workflow.md — references regression baseline
# ---------------------------------------------------------------------------


def test_agent_workflow_references_regression_baseline_in_checklist():
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert "regression-baseline.json" in content, (
        "agent-workflow.md must reference tests/regression-baseline.json"
    )


def test_agent_workflow_mandatory_table_has_regression_baseline_row():
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert "regression baseline" in content.lower(), (
        "agent-workflow.md Mandatory Script Usage table must mention regression baseline"
    )


# ---------------------------------------------------------------------------
# developer.agent.md — checklist includes regression baseline for bug fixes
# ---------------------------------------------------------------------------


def test_developer_agent_references_regression_baseline():
    content = DEVELOPER_AGENT.read_text(encoding="utf-8")
    assert "regression-baseline.json" in content, (
        "developer.agent.md Pre-Handoff Checklist must reference regression-baseline.json"
    )


def test_developer_agent_mentions_fix_wp_condition():
    content = DEVELOPER_AGENT.read_text(encoding="utf-8")
    assert "FIX-xxx" in content or "bug fix" in content.lower(), (
        "developer.agent.md must condition the regression baseline step on bug-fix WPs"
    )


# ---------------------------------------------------------------------------
# tester.agent.md — already references regression baseline (pre-existing)
# ---------------------------------------------------------------------------


def test_tester_agent_references_regression_baseline():
    content = TESTER_AGENT.read_text(encoding="utf-8")
    assert "regression-baseline.json" in content, (
        "tester.agent.md must reference regression-baseline.json"
    )


# ---------------------------------------------------------------------------
# orchestrator.agent.md — already references regression baseline (pre-existing)
# ---------------------------------------------------------------------------


def test_orchestrator_agent_references_regression_baseline():
    content = ORCHESTRATOR_AGENT.read_text(encoding="utf-8")
    assert "regression-baseline.json" in content, (
        "orchestrator.agent.md must reference regression-baseline.json"
    )


# ---------------------------------------------------------------------------
# regression-baseline.json — schema conformance
# ---------------------------------------------------------------------------


def test_regression_baseline_file_exists():
    assert REGRESSION_BASELINE.exists(), (
        "tests/regression-baseline.json must exist"
    )


def test_regression_baseline_is_valid_json():
    content = REGRESSION_BASELINE.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict)


def test_regression_baseline_has_comment_field():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    assert "_comment" in data, "regression-baseline.json must have a '_comment' field"
    assert isinstance(data["_comment"], str)


def test_regression_baseline_has_count_field():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    assert "_count" in data, "regression-baseline.json must have a '_count' field"
    assert isinstance(data["_count"], int)


def test_regression_baseline_has_updated_field():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    assert "_updated" in data, "regression-baseline.json must have an '_updated' field"
    assert isinstance(data["_updated"], str)


def test_regression_baseline_has_known_failures_field():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    assert "known_failures" in data, (
        "regression-baseline.json must have a 'known_failures' field"
    )
    assert isinstance(data["known_failures"], dict)


def test_regression_baseline_count_matches_entries():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    declared = data["_count"]
    actual = len(data["known_failures"])
    assert declared == actual, (
        f"regression-baseline.json '_count' field ({declared}) does not match "
        f"actual number of entries ({actual})"
    )


def test_regression_baseline_each_entry_has_reason():
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    for key, value in data["known_failures"].items():
        assert isinstance(value, dict), f"Entry '{key}' value must be a dict"
        assert "reason" in value, f"Entry '{key}' must have a 'reason' field"
        assert isinstance(value["reason"], str), (
            f"Entry '{key}' reason must be a string"
        )
        assert value["reason"].strip(), f"Entry '{key}' reason must not be empty"


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester (DOC-051)
# ---------------------------------------------------------------------------


def test_regression_baseline_updated_field_is_iso8601_date():
    """_updated must be a valid ISO 8601 date (YYYY-MM-DD), not an arbitrary string."""
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    updated = data["_updated"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", updated), (
        f"regression-baseline.json '_updated' must be YYYY-MM-DD, got: {updated!r}"
    )


def test_regression_baseline_count_is_non_negative():
    """_count must be a non-negative integer (empty baseline is allowed, negative is not)."""
    data = json.loads(REGRESSION_BASELINE.read_text(encoding="utf-8"))
    assert data["_count"] >= 0, (
        f"regression-baseline.json '_count' must be >= 0, got: {data['_count']}"
    )


def test_testing_protocol_baseline_section_requires_count_update():
    """Documentation must explicitly say _count must be updated when editing the file."""
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_idx = content.index("## Regression Baseline")
    section = content[baseline_idx:]
    assert "_count" in section and ("update" in section.lower() or "must" in section.lower()), (
        "Regression Baseline section must instruct editors to update _count"
    )


def test_testing_protocol_baseline_section_requires_updated_date_update():
    """Documentation must explicitly say _updated must be set when editing the file."""
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_idx = content.index("## Regression Baseline")
    section = content[baseline_idx:]
    assert "_updated" in section and "date" in section.lower(), (
        "Regression Baseline section must instruct editors to update _updated date"
    )


def test_agent_workflow_fix_wp_checklist_references_count_and_updated():
    """The dev pre-handoff checklist item for FIX WPs must mention _count and _updated."""
    content = AGENT_WORKFLOW.read_text(encoding="utf-8")
    assert "_count" in content and "_updated" in content, (
        "agent-workflow.md FIX WP checklist item must mention _count and _updated"
    )


def test_testing_protocol_baseline_mentions_validation_command():
    """The How-to-Update procedure should include a JSON validation command."""
    content = TESTING_PROTOCOL.read_text(encoding="utf-8")
    baseline_idx = content.index("## Regression Baseline")
    section = content[baseline_idx:]
    assert "json" in section.lower() and ("valid" in section.lower() or "python" in section.lower()), (
        "Regression Baseline 'How to Update' should mention JSON validation"
    )
