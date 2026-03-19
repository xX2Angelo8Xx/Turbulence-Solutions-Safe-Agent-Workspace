"""
Tests for SAF-019: Update VS Code Settings for Auto-Approve.

Verifies that both templates/coding/.vscode/settings.json and
templates/coding/.vscode/settings.json contain the correct auto-approve
configuration.
"""

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SETTINGS_PATHS = [
    REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json",
    REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json",
]

EXPECTED_AUTO_APPROVE_TOOLS = [
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "create_file",
]


def _load(path: pathlib.Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestSettingsFilesExist:
    def test_default_project_settings_exists(self):
        assert SETTINGS_PATHS[0].exists(), (
            f"Missing settings file: {SETTINGS_PATHS[0]}"
        )

    def test_templates_coding_settings_exists(self):
        assert SETTINGS_PATHS[1].exists(), (
            f"Missing settings file: {SETTINGS_PATHS[1]}"
        )


class TestGlobalAutoApproveDisabled:
    def test_default_project_global_auto_approve_is_false(self):
        data = _load(SETTINGS_PATHS[0])
        assert data.get("chat.tools.global.autoApprove") is False

    def test_templates_coding_global_auto_approve_is_false(self):
        data = _load(SETTINGS_PATHS[1])
        assert data.get("chat.tools.global.autoApprove") is False


class TestEditsAutoApproveList:
    def test_default_project_edits_auto_approve_is_list(self):
        data = _load(SETTINGS_PATHS[0])
        assert isinstance(data.get("chat.tools.edits.autoApprove"), list)

    def test_templates_coding_edits_auto_approve_is_list(self):
        data = _load(SETTINGS_PATHS[1])
        assert isinstance(data.get("chat.tools.edits.autoApprove"), list)

    def test_default_project_contains_replace_string_in_file(self):
        data = _load(SETTINGS_PATHS[0])
        assert "replace_string_in_file" in data["chat.tools.edits.autoApprove"]

    def test_default_project_contains_multi_replace_string_in_file(self):
        data = _load(SETTINGS_PATHS[0])
        assert "multi_replace_string_in_file" in data["chat.tools.edits.autoApprove"]

    def test_default_project_contains_create_file(self):
        data = _load(SETTINGS_PATHS[0])
        assert "create_file" in data["chat.tools.edits.autoApprove"]

    def test_templates_coding_contains_replace_string_in_file(self):
        data = _load(SETTINGS_PATHS[1])
        assert "replace_string_in_file" in data["chat.tools.edits.autoApprove"]

    def test_templates_coding_contains_multi_replace_string_in_file(self):
        data = _load(SETTINGS_PATHS[1])
        assert "multi_replace_string_in_file" in data["chat.tools.edits.autoApprove"]

    def test_templates_coding_contains_create_file(self):
        data = _load(SETTINGS_PATHS[1])
        assert "create_file" in data["chat.tools.edits.autoApprove"]

    def test_default_project_exact_tool_count(self):
        data = _load(SETTINGS_PATHS[0])
        tools = data["chat.tools.edits.autoApprove"]
        assert len(tools) == 3, f"Expected exactly 3 tools, got {len(tools)}: {tools}"

    def test_templates_coding_exact_tool_count(self):
        data = _load(SETTINGS_PATHS[1])
        tools = data["chat.tools.edits.autoApprove"]
        assert len(tools) == 3, f"Expected exactly 3 tools, got {len(tools)}: {tools}"


class TestSettingsInSync:
    def test_both_files_have_identical_auto_approve_settings(self):
        d1 = _load(SETTINGS_PATHS[0])
        d2 = _load(SETTINGS_PATHS[1])
        assert d1.get("chat.tools.edits.autoApprove") == d2.get(
            "chat.tools.edits.autoApprove"
        ), "chat.tools.edits.autoApprove differs between the two settings files"

    def test_both_files_have_identical_global_auto_approve(self):
        d1 = _load(SETTINGS_PATHS[0])
        d2 = _load(SETTINGS_PATHS[1])
        assert d1.get("chat.tools.global.autoApprove") == d2.get(
            "chat.tools.global.autoApprove"
        ), "chat.tools.global.autoApprove differs between the two settings files"


class TestJsonValidity:
    def test_default_project_settings_is_valid_json(self):
        # _load raises json.JSONDecodeError if invalid
        data = _load(SETTINGS_PATHS[0])
        assert isinstance(data, dict)

    def test_templates_coding_settings_is_valid_json(self):
        data = _load(SETTINGS_PATHS[1])
        assert isinstance(data, dict)
