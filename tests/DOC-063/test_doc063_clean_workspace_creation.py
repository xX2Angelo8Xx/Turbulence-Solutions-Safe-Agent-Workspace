"""
DOC-063: Tests for clean-workspace template creation.

Verifies:
1. 'clean-workspace' appears in list_templates() output (dropdown discovery)
2. create_project() with clean-workspace template creates the correct workspace structure
3. NO .github/agents/, .github/prompts/, .github/skills/ in created workspace
4. NO AgentDocs/ at the workspace root
5. AGENT-RULES.md exists at the project root (inside the renamed project folder)
6. security_gate.py exists and is byte-identical to the template source
7. Placeholders {{PROJECT_NAME}} and {{WORKSPACE_NAME}} are replaced in .md files
8. .vscode/settings.json exists with the correct .github and .vscode exclusion patterns
"""
from __future__ import annotations

import hashlib
import json
import py_compile
import sys
from pathlib import Path

import pytest

from launcher.config import TEMPLATES_DIR
from launcher.core.project_creator import create_project, is_template_ready, list_templates

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEMPLATE_NAME = "clean-workspace"
CLEAN_TEMPLATE = TEMPLATES_DIR / TEMPLATE_NAME
_SCRIPTS_DIR = str(CLEAN_TEMPLATE / ".github" / "hooks" / "scripts")


def _sha256(path: Path) -> str:
    """Return lower-case hex SHA256 of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ===========================================================================
# 1. Template discovery — list_templates() and is_template_ready()
# ===========================================================================


class TestCleanWorkspaceInDropdown:
    """Verify clean-workspace is auto-discovered by list_templates()."""

    def test_clean_workspace_in_list_templates(self):
        """list_templates() must include 'clean-workspace' so it appears in the dropdown."""
        templates = list_templates(TEMPLATES_DIR)
        assert TEMPLATE_NAME in templates, (
            f"'clean-workspace' must appear in list_templates(); got: {templates}"
        )

    def test_clean_workspace_is_template_ready(self):
        """is_template_ready() must return True for the clean-workspace template."""
        assert is_template_ready(TEMPLATES_DIR, TEMPLATE_NAME), (
            "clean-workspace template must be non-empty and ready for use"
        )


# ===========================================================================
# 2. create_project() output structure
# ===========================================================================


class TestCreateProjectStructure:
    """Verify create_project() with clean-workspace produces the correct filesystem structure."""

    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path):
        dest = tmp_path / "dest"
        dest.mkdir()
        self.workspace = create_project(CLEAN_TEMPLATE, dest, "TestProject")

    # --- positive structural checks ---

    def test_workspace_directory_created(self):
        """Workspace root directory must be created inside the destination."""
        assert self.workspace.is_dir(), "Workspace directory must be created"

    def test_workspace_prefixed_with_sae(self):
        """Workspace directory must be prefixed 'SAE-' followed by the project name."""
        assert self.workspace.name == "SAE-TestProject", (
            "Workspace must be named SAE-TestProject"
        )

    def test_project_subfolder_renamed(self):
        """The 'Project/' subfolder inside the workspace must be renamed to the project name."""
        assert (self.workspace / "TestProject").is_dir(), (
            "Project/ subfolder must be renamed to 'TestProject'"
        )

    def test_agent_rules_at_project_root(self):
        """AGENT-RULES.md must exist inside the renamed project subfolder."""
        agent_rules = self.workspace / "TestProject" / "AGENT-RULES.md"
        assert agent_rules.is_file(), (
            "AGENT-RULES.md must exist inside the project folder (TestProject/)"
        )

    def test_security_gate_exists(self):
        """security_gate.py must exist in .github/hooks/scripts/ of the created workspace."""
        sg = self.workspace / ".github" / "hooks" / "scripts" / "security_gate.py"
        assert sg.is_file(), "security_gate.py must exist in the created workspace"

    def test_security_gate_byte_identical_to_source(self):
        """security_gate.py in the created workspace must be byte-identical to the template source."""
        created_sg = self.workspace / ".github" / "hooks" / "scripts" / "security_gate.py"
        source_sg = CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py"
        assert _sha256(created_sg) == _sha256(source_sg), (
            "security_gate.py in the created workspace must be byte-identical to the template source"
        )

    def test_vscode_settings_exists(self):
        """.vscode/settings.json must exist in the created workspace."""
        settings = self.workspace / ".vscode" / "settings.json"
        assert settings.is_file(), ".vscode/settings.json must exist in the created workspace"

    def test_vscode_settings_excludes_github(self):
        """settings.json must exclude .github so agents cannot see security files."""
        settings = self.workspace / ".vscode" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        files_exclude = data.get("files.exclude", {})
        assert ".github" in files_exclude, (
            "settings.json files.exclude must contain '.github'"
        )

    def test_vscode_settings_excludes_vscode(self):
        """settings.json must exclude .vscode so agents cannot see VS Code config."""
        settings = self.workspace / ".vscode" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8"))
        files_exclude = data.get("files.exclude", {})
        assert ".vscode" in files_exclude, (
            "settings.json files.exclude must contain '.vscode'"
        )

    # --- absence checks: directories that must NOT exist ---

    def test_no_agents_directory(self):
        """Created workspace must NOT contain .github/agents/ (clean-workspace has no custom agents)."""
        agents_dir = self.workspace / ".github" / "agents"
        assert not agents_dir.exists(), (
            "clean-workspace must not contain .github/agents/"
        )

    def test_no_prompts_directory(self):
        """Created workspace must NOT contain .github/prompts/ (clean-workspace has no custom prompts)."""
        prompts_dir = self.workspace / ".github" / "prompts"
        assert not prompts_dir.exists(), (
            "clean-workspace must not contain .github/prompts/"
        )

    def test_no_skills_directory(self):
        """Created workspace must NOT contain .github/skills/ (clean-workspace has no custom skills)."""
        skills_dir = self.workspace / ".github" / "skills"
        assert not skills_dir.exists(), (
            "clean-workspace must not contain .github/skills/"
        )

    def test_no_agentdocs_directory(self):
        """Created workspace must NOT contain AgentDocs/ at the workspace root."""
        agentdocs_dir = self.workspace / "AgentDocs"
        assert not agentdocs_dir.exists(), (
            "clean-workspace must not contain AgentDocs/ at the workspace root"
        )


# ===========================================================================
# 3. Placeholder replacement
# ===========================================================================


class TestPlaceholderReplacement:
    """Verify {{PROJECT_NAME}} and {{WORKSPACE_NAME}} are replaced in .md files."""

    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path):
        dest = tmp_path / "dest"
        dest.mkdir()
        self.workspace = create_project(CLEAN_TEMPLATE, dest, "MyProject")

    def test_project_name_replaced_in_agent_rules(self):
        """AGENT-RULES.md must contain the actual project name, not the placeholder."""
        agent_rules = self.workspace / "MyProject" / "AGENT-RULES.md"
        content = agent_rules.read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in content, (
            "{{PROJECT_NAME}} placeholder must be replaced in AGENT-RULES.md"
        )
        assert "MyProject" in content, (
            "AGENT-RULES.md must contain the actual project name after placeholder replacement"
        )

    def test_workspace_name_replaced_in_agent_rules(self):
        """AGENT-RULES.md must contain the workspace name (SAE-<project>), not the placeholder."""
        agent_rules = self.workspace / "MyProject" / "AGENT-RULES.md"
        content = agent_rules.read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" not in content, (
            "{{WORKSPACE_NAME}} placeholder must be replaced in AGENT-RULES.md"
        )
        assert "SAE-MyProject" in content, (
            "AGENT-RULES.md must contain the workspace name (SAE-MyProject) after replacement"
        )

    def test_no_raw_placeholders_in_any_md_file(self):
        """No {{PROJECT_NAME}} or {{WORKSPACE_NAME}} tokens must remain in any .md file."""
        for md_file in self.workspace.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            rel = md_file.relative_to(self.workspace)
            assert "{{PROJECT_NAME}}" not in content, (
                f"{{{{PROJECT_NAME}}}} placeholder still present in {rel}"
            )
            assert "{{WORKSPACE_NAME}}" not in content, (
                f"{{{{WORKSPACE_NAME}}}} placeholder still present in {rel}"
            )


# ===========================================================================
# 4. Security gate functional
# ===========================================================================


class TestSecurityGateFunctional:
    """Verify the security_gate.py shipped in the clean-workspace template is functional."""

    def test_security_gate_no_syntax_errors(self):
        """security_gate.py must compile without syntax errors."""
        import os, tempfile
        sg_path = str(CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py")
        # Write compiled output to a temp file to avoid creating __pycache__ in the template.
        with tempfile.NamedTemporaryFile(suffix=".pyc", delete=False) as f:
            tmp = f.name
        try:
            py_compile.compile(sg_path, cfile=tmp, doraise=True)
        finally:
            os.unlink(tmp)

    def test_security_gate_importable_and_decide_returns_action(self):
        """security_gate.decide() must return 'allow', 'ask', or 'deny' for a test event."""
        import importlib

        # Save any pre-existing security_gate / zone_classifier module objects so
        # that other tests (e.g. snapshot tests) are not affected by this import.
        # The clean-workspace versions are loaded only for the duration of this test.
        _orig_sg = sys.modules.pop("security_gate", None)
        _orig_zc = sys.modules.pop("zone_classifier", None)
        if _SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, _SCRIPTS_DIR)
        try:
            sg = importlib.import_module("security_gate")
            # Use a harmless always-allow tool event (TodoWrite bypasses zone checks).
            hook_input = {
                "tool_name": "TodoWrite",
                "tool_input": {},
            }
            ws_root = "/workspace/SAE-MyProject"
            result = sg.decide(hook_input, ws_root)
            assert isinstance(result, str), "decide() must return a string"
            assert result in ("allow", "ask", "deny"), (
                f"action must be 'allow', 'ask', or 'deny'; got: {result!r}"
            )
        finally:
            # Clean up sys.path to avoid polluting other tests.
            if _SCRIPTS_DIR in sys.path:
                sys.path.remove(_SCRIPTS_DIR)
            # Remove the clean-workspace modules loaded during this test.
            for mod_name in list(sys.modules.keys()):
                if mod_name in ("security_gate", "zone_classifier"):
                    del sys.modules[mod_name]
            # Restore the original modules so other tests (e.g. snapshot tests)
            # continue to reference the same module objects they imported at
            # collection time.  Without this restore, the snapshot conftest
            # fixture patches a different zone_classifier instance than the one
            # held by the snapshot test module's 'sg' import, which causes the
            # _patch_detect_project_folder fixture to have no effect.
            if _orig_sg is not None:
                sys.modules["security_gate"] = _orig_sg
            if _orig_zc is not None:
                sys.modules["zone_classifier"] = _orig_zc
            # Remove any __pycache__ created by the importlib.import_module call
            # to prevent polluting the template directory and failing GUI-035
            # TestNoTemplatePollution tests (BUG-211).
            import shutil
            pycache = CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "__pycache__"
            if pycache.exists():
                shutil.rmtree(pycache)


# ===========================================================================
# 5. Edge cases — missing acceptance-criteria coverage (added by Tester)
# ===========================================================================


class TestMissingACCoverage:
    """Tester-added tests for US-078 acceptance-criteria items not covered by Developer."""

    @pytest.fixture(autouse=True)
    def _workspace(self, tmp_path):
        dest = tmp_path / "dest"
        dest.mkdir()
        self.workspace = create_project(CLEAN_TEMPLATE, dest, "TesterProject")

    def test_manifest_json_exists(self):
        """MANIFEST.json must exist at .github/hooks/scripts/MANIFEST.json (FIX-122: moved from root)."""
        manifest = self.workspace / ".github" / "hooks" / "scripts" / "MANIFEST.json"
        assert manifest.is_file(), (
            "MANIFEST.json must exist at .github/hooks/scripts/MANIFEST.json (FIX-122)"
        )

    def test_copilot_instructions_exists(self):
        """copilot-instructions.md must exist in .github/instructions/ (US-078 AC 5)."""
        ci = self.workspace / ".github" / "instructions" / "copilot-instructions.md"
        assert ci.is_file(), (
            ".github/instructions/copilot-instructions.md must exist in the created workspace"
        )

    def test_copilot_instructions_no_agents_dir_reference(self):
        """copilot-instructions.md must not reference .github/agents/ (US-078 AC 5 — simplified)."""
        ci = self.workspace / ".github" / "instructions" / "copilot-instructions.md"
        content = ci.read_text(encoding="utf-8")
        assert ".github/agents" not in content, (
            "copilot-instructions.md must not reference .github/agents/ "
            "(clean-workspace has no custom agents — US-078 AC 5)"
        )

    def test_create_project_hyphenated_name(self, tmp_path):
        """create_project() must handle a hyphenated project name correctly."""
        dest = tmp_path / "dest_hyph"
        dest.mkdir()
        ws = create_project(CLEAN_TEMPLATE, dest, "My-Project")
        assert ws.is_dir(), "Workspace directory must be created for hyphenated name"
        assert ws.name == "SAE-My-Project", (
            "Workspace must be named SAE-My-Project for input 'My-Project'"
        )
        assert (ws / "My-Project").is_dir(), (
            "Project subfolder must be named 'My-Project'"
        )

    def test_security_gate_denies_noagentzone(self):
        """security_gate.decide() must deny access to NoAgentZone/ (US-078 AC 6)."""
        _orig_sg = sys.modules.pop("security_gate", None)
        _orig_zc = sys.modules.pop("zone_classifier", None)
        if _SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, _SCRIPTS_DIR)
        try:
            import importlib
            sg = importlib.import_module("security_gate")
            hook_input = {
                "tool_name": "read_file",
                "filePath": "/workspace/SAE-TestProject/NoAgentZone/secret.txt",
            }
            result = sg.decide(hook_input, "/workspace/SAE-TestProject")
            assert result == "deny", (
                f"security_gate must deny access to NoAgentZone/; got: {result!r}"
            )
        finally:
            if _SCRIPTS_DIR in sys.path:
                sys.path.remove(_SCRIPTS_DIR)
            for mod_name in list(sys.modules.keys()):
                if mod_name in ("security_gate", "zone_classifier"):
                    del sys.modules[mod_name]
            if _orig_sg is not None:
                sys.modules["security_gate"] = _orig_sg
            if _orig_zc is not None:
                sys.modules["zone_classifier"] = _orig_zc
            # Remove any __pycache__ created by the importlib.import_module call
            # to prevent polluting the template directory and failing GUI-035
            # TestNoTemplatePollution tests (BUG-211).
            import shutil
            pycache = CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "__pycache__"
            if pycache.exists():
                shutil.rmtree(pycache)
