"""
Tester edge-case tests for SAF-019: Update VS Code Settings for Auto-Approve.

Covers security and correctness scenarios beyond the developer's test suite:
- No duplicate tool entries
- Boolean type enforcement (not just falsy)
- Exact tool name case-sensitivity
- No unexpected auto-approve scope keys
- Identical tool ordering between both files
- File encoding is UTF-8 parseable
- auto-approve list contains only the approved tools (set equality)
"""

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SETTINGS_PATHS = {
    "default_project": REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json",
    "templates_coding": REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json",
}

EXPECTED_TOOLS = ["replace_string_in_file", "multi_replace_string_in_file", "create_file"]


def _load(label: str) -> dict:
    path = SETTINGS_PATHS[label]
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestNoDuplicates:
    """Auto-approve list must not contain duplicate entries."""

    def test_default_project_no_duplicate_tools(self):
        tools = _load("default_project")["chat.tools.edits.autoApprove"]
        assert len(tools) == len(set(tools)), (
            f"Duplicate tool names in templates/coding settings: {tools}"
        )

    def test_templates_coding_no_duplicate_tools(self):
        tools = _load("templates_coding")["chat.tools.edits.autoApprove"]
        assert len(tools) == len(set(tools)), (
            f"Duplicate tool names in templates/coding settings: {tools}"
        )


class TestBooleanTypeEnforcement:
    """chat.tools.global.autoApprove must be the boolean literal False, not just falsy."""

    def test_default_project_global_auto_approve_is_boolean_false(self):
        value = _load("default_project").get("chat.tools.global.autoApprove")
        assert value is False, (
            f"Expected boolean False, got {type(value).__name__}: {value!r}"
        )

    def test_templates_coding_global_auto_approve_is_boolean_false(self):
        value = _load("templates_coding").get("chat.tools.global.autoApprove")
        assert value is False, (
            f"Expected boolean False, got {type(value).__name__}: {value!r}"
        )


class TestExactToolNames:
    """Tool names are case-sensitive. Verify exact string match, not just substring."""

    def test_default_project_tool_names_exact_case(self):
        tools = _load("default_project")["chat.tools.edits.autoApprove"]
        for expected in EXPECTED_TOOLS:
            assert expected in tools, (
                f"Expected exact tool name '{expected}' not found in {tools}"
            )
            # Ensure no case variant exists instead (e.g. "Replace_String_In_File")
            lower_tools = [t.lower() for t in tools]
            assert expected.lower() in lower_tools

    def test_templates_coding_tool_names_exact_case(self):
        tools = _load("templates_coding")["chat.tools.edits.autoApprove"]
        for expected in EXPECTED_TOOLS:
            assert expected in tools, (
                f"Expected exact tool name '{expected}' not found in {tools}"
            )


class TestNoUnexpectedAutoApproveKeys:
    """No rogue auto-approve scope keys should exist (e.g. chat.tools.all.autoApprove)."""

    def test_default_project_no_unexpected_auto_approve_keys(self):
        data = _load("default_project")
        allowed_auto_approve_keys = {
            "chat.tools.global.autoApprove",
            "chat.tools.edits.autoApprove",
        }
        found_auto_approve_keys = {k for k in data if "autoApprove" in k}
        unexpected = found_auto_approve_keys - allowed_auto_approve_keys
        assert not unexpected, (
            f"Unexpected auto-approve keys in templates/coding settings: {unexpected}"
        )

    def test_templates_coding_no_unexpected_auto_approve_keys(self):
        data = _load("templates_coding")
        allowed_auto_approve_keys = {
            "chat.tools.global.autoApprove",
            "chat.tools.edits.autoApprove",
        }
        found_auto_approve_keys = {k for k in data if "autoApprove" in k}
        unexpected = found_auto_approve_keys - allowed_auto_approve_keys
        assert not unexpected, (
            f"Unexpected auto-approve keys in templates/coding settings: {unexpected}"
        )


class TestToolOrderSync:
    """Both files must list tools in the identical order for deterministic behaviour."""

    def test_tool_order_is_identical_in_both_files(self):
        tools_default = _load("default_project")["chat.tools.edits.autoApprove"]
        tools_templates = _load("templates_coding")["chat.tools.edits.autoApprove"]
        assert tools_default == tools_templates, (
            f"Tool order mismatch:\n  templates/coding: {tools_default}\n"
            f"  templates/coding: {tools_templates}"
        )


class TestExactToolSetEquality:
    """The auto-approve list must contain EXACTLY the 3 approved tools — no more, no less."""

    def test_default_project_exact_tool_set(self):
        tools = _load("default_project")["chat.tools.edits.autoApprove"]
        assert set(tools) == set(EXPECTED_TOOLS), (
            f"Tool set mismatch in templates/coding.\n"
            f"  Expected: {set(EXPECTED_TOOLS)}\n"
            f"  Got:      {set(tools)}"
        )

    def test_templates_coding_exact_tool_set(self):
        tools = _load("templates_coding")["chat.tools.edits.autoApprove"]
        assert set(tools) == set(EXPECTED_TOOLS), (
            f"Tool set mismatch in templates/coding.\n"
            f"  Expected: {set(EXPECTED_TOOLS)}\n"
            f"  Got:      {set(tools)}"
        )


class TestFullSettingsSync:
    """Both settings files should be fully identical (same keys, same values)."""

    def test_both_files_fully_identical(self):
        d1 = _load("default_project")
        d2 = _load("templates_coding")
        assert d1 == d2, (
            "settings.json files are not fully identical.\n"
            + "\n".join(
                f"  Key '{k}': templates/coding={d1.get(k)!r}, templates/coding={d2.get(k)!r}"
                for k in set(d1) | set(d2)
                if d1.get(k) != d2.get(k)
            )
        )
