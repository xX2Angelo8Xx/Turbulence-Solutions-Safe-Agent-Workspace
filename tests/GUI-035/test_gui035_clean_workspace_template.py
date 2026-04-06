"""Tests for GUI-035: Create clean-workspace template structure.

Verifies that templates/clean-workspace/ exists with all required files,
is auto-discovered by list_templates(), has no forbidden directories,
and that security gate files are byte-identical to agent-workbench.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CLEAN_WORKSPACE = _REPO_ROOT / "templates" / "clean-workspace"
_AGENT_WORKBENCH = _REPO_ROOT / "templates" / "agent-workbench"
_TEMPLATES_DIR = _REPO_ROOT / "templates"
_CLEAN_WORKSPACE_MANIFEST = _CLEAN_WORKSPACE / ".github" / "hooks" / "scripts" / "MANIFEST.json"


def _sha256_normalized(path: Path) -> str:
    """Compute SHA256 with CRLF-normalized to LF (matches generate_manifest.py)."""
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Directory structure
# ---------------------------------------------------------------------------

class TestTemplateDirectoryExists:
    def test_template_directory_exists(self):
        """templates/clean-workspace/ must exist."""
        assert _CLEAN_WORKSPACE.is_dir(), (
            f"templates/clean-workspace/ does not exist at {_CLEAN_WORKSPACE}"
        )


class TestRequiredFiles:
    @pytest.mark.parametrize("rel_path", [
        ".github/hooks/scripts/security_gate.py",
        ".github/hooks/scripts/update_hashes.py",
        ".github/hooks/scripts/zone_classifier.py",
        ".github/hooks/scripts/require-approval.ps1",
        ".github/hooks/scripts/require-approval.sh",
        ".github/hooks/scripts/reset_hook_counter.py",
        ".github/hooks/scripts/counter_config.json",
        ".github/hooks/require-approval.json",
        ".github/instructions/copilot-instructions.md",
        ".vscode/settings.json",
        "NoAgentZone/README.md",
        "Project/AGENT-RULES.md",
        "Project/README.md",
        ".gitignore",
        ".github/hooks/scripts/MANIFEST.json",
        "README.md",
    ])
    def test_required_file_present(self, rel_path: str):
        """Each required file must exist in the clean-workspace template."""
        file_path = _CLEAN_WORKSPACE / rel_path
        assert file_path.is_file(), (
            f"Required file missing from clean-workspace: {rel_path}"
        )


# ---------------------------------------------------------------------------
# Forbidden directories
# ---------------------------------------------------------------------------

class TestForbiddenDirectories:
    def test_no_agents_dir(self):
        """clean-workspace must NOT contain .github/agents/."""
        assert not (_CLEAN_WORKSPACE / ".github" / "agents").exists(), (
            ".github/agents/ must not exist in clean-workspace"
        )

    def test_no_prompts_dir(self):
        """clean-workspace must NOT contain .github/prompts/."""
        assert not (_CLEAN_WORKSPACE / ".github" / "prompts").exists(), (
            ".github/prompts/ must not exist in clean-workspace"
        )

    def test_no_skills_dir(self):
        """clean-workspace must NOT contain .github/skills/."""
        assert not (_CLEAN_WORKSPACE / ".github" / "skills").exists(), (
            ".github/skills/ must not exist in clean-workspace"
        )

    def test_no_agentdocs_in_project(self):
        """clean-workspace Project/ must NOT contain AgentDocs/."""
        assert not (_CLEAN_WORKSPACE / "Project" / "AgentDocs").exists(), (
            "Project/AgentDocs/ must not exist in clean-workspace"
        )


# ---------------------------------------------------------------------------
# Byte-identical security files
# ---------------------------------------------------------------------------

class TestSecurityFilesIdentical:
    @pytest.mark.parametrize("rel_path", [
        ".github/hooks/scripts/security_gate.py",
        ".github/hooks/scripts/update_hashes.py",
        ".github/hooks/scripts/zone_classifier.py",
        ".github/hooks/scripts/require-approval.ps1",
        ".github/hooks/scripts/require-approval.sh",
        ".github/hooks/require-approval.json",
    ])
    def test_security_file_byte_identical(self, rel_path: str):
        """Security files in clean-workspace must be byte-identical to agent-workbench."""
        clean = _CLEAN_WORKSPACE / rel_path
        agent = _AGENT_WORKBENCH / rel_path
        assert clean.is_file(), f"clean-workspace missing: {rel_path}"
        assert agent.is_file(), f"agent-workbench missing (reference): {rel_path}"
        assert _sha256_normalized(clean) == _sha256_normalized(agent), (
            f"File differs from agent-workbench: {rel_path}"
        )


# ---------------------------------------------------------------------------
# Content checks
# ---------------------------------------------------------------------------

class TestVscodeSettings:
    def test_settings_has_github_hidden(self):
        """settings.json must have .github in files.exclude."""
        settings = json.loads(
            (_CLEAN_WORKSPACE / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )
        assert ".github" in settings.get("files.exclude", {}), (
            "settings.json must hide .github in files.exclude"
        )

    def test_settings_has_vscode_hidden(self):
        """settings.json must have .vscode in files.exclude."""
        settings = json.loads(
            (_CLEAN_WORKSPACE / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )
        assert ".vscode" in settings.get("files.exclude", {}), (
            "settings.json must hide .vscode in files.exclude"
        )


class TestCopilotInstructions:
    def test_no_agents_reference(self):
        """copilot-instructions.md must not reference .github/agents/."""
        content = (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")
        assert ".github/agents" not in content, (
            "copilot-instructions.md must not reference .github/agents/ (no agents directory)"
        )

    def test_no_skills_reference(self):
        """copilot-instructions.md must not reference .github/skills/."""
        content = (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")
        assert ".github/skills" not in content, (
            "copilot-instructions.md must not reference .github/skills/ (no skills directory)"
        )

    def test_no_agentdocs_reference(self):
        """copilot-instructions.md must not reference AgentDocs."""
        content = (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")
        assert "AgentDocs" not in content, (
            "copilot-instructions.md must not reference AgentDocs (no AgentDocs directory)"
        )

    def test_has_project_name_placeholder(self):
        """copilot-instructions.md must contain {{PROJECT_NAME}} placeholder."""
        content = (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" in content, (
            "copilot-instructions.md must contain {{PROJECT_NAME}} template placeholder"
        )


class TestAgentRules:
    def test_no_agentdocs_section(self):
        """AGENT-RULES.md must not reference AgentDocs."""
        content = (
            _CLEAN_WORKSPACE / "Project" / "AGENT-RULES.md"
        ).read_text(encoding="utf-8")
        assert "AgentDocs" not in content, (
            "Project/AGENT-RULES.md must not contain AgentDocs references"
        )

    def test_has_project_name_placeholder(self):
        """AGENT-RULES.md must contain {{PROJECT_NAME}} placeholder."""
        content = (
            _CLEAN_WORKSPACE / "Project" / "AGENT-RULES.md"
        ).read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" in content, (
            "Project/AGENT-RULES.md must contain {{PROJECT_NAME}} template placeholder"
        )


# ---------------------------------------------------------------------------
# MANIFEST.json
# ---------------------------------------------------------------------------

class TestManifestJson:
    def test_manifest_is_valid_json(self):
        """MANIFEST.json must be valid JSON."""
        content = _CLEAN_WORKSPACE_MANIFEST.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_manifest_template_field(self):
        """MANIFEST.json must have template field set to 'clean-workspace'."""
        data = json.loads(
            _CLEAN_WORKSPACE_MANIFEST.read_text(encoding="utf-8")
        )
        assert data.get("template") == "clean-workspace", (
            "MANIFEST.json template field must be 'clean-workspace'"
        )

    def test_manifest_has_file_count(self):
        """MANIFEST.json must have a positive file_count."""
        data = json.loads(
            _CLEAN_WORKSPACE_MANIFEST.read_text(encoding="utf-8")
        )
        assert data.get("file_count", 0) > 0, (
            "MANIFEST.json file_count must be positive"
        )

    def test_manifest_tracks_security_gate(self):
        """MANIFEST.json must track security_gate.py."""
        data = json.loads(
            _CLEAN_WORKSPACE_MANIFEST.read_text(encoding="utf-8")
        )
        files = data.get("files", {})
        assert ".github/hooks/scripts/security_gate.py" in files, (
            "MANIFEST.json must track security_gate.py"
        )

    def test_manifest_security_gate_is_critical(self):
        """security_gate.py must be marked security_critical in MANIFEST.json."""
        data = json.loads(
            _CLEAN_WORKSPACE_MANIFEST.read_text(encoding="utf-8")
        )
        entry = data.get("files", {}).get(".github/hooks/scripts/security_gate.py", {})
        assert entry.get("security_critical") is True, (
            "security_gate.py must be marked security_critical=true in MANIFEST.json"
        )


# ---------------------------------------------------------------------------
# Template auto-discovery
# ---------------------------------------------------------------------------

class TestTemplateDiscovery:
    def test_list_templates_discovers_clean_workspace(self):
        """list_templates() must return 'clean-workspace' as a discoverable template."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "project_creator",
            _REPO_ROOT / "src" / "launcher" / "core" / "project_creator.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        templates = mod.list_templates(_TEMPLATES_DIR)
        assert "clean-workspace" in templates, (
            f"list_templates() did not discover clean-workspace. Got: {templates}"
        )

    def test_is_template_ready(self):
        """is_template_ready() must return True for clean-workspace."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "project_creator",
            _REPO_ROOT / "src" / "launcher" / "core" / "project_creator.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert mod.is_template_ready(_TEMPLATES_DIR, "clean-workspace") is True, (
            "is_template_ready() must return True for clean-workspace"
        )

    def test_generate_manifest_supports_clean_workspace(self):
        """generate_manifest.py must support --template clean-workspace."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generate_manifest",
            _REPO_ROOT / "scripts" / "generate_manifest.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        manifest = mod.generate_manifest("clean-workspace")
        assert manifest.get("template") == "clean-workspace", (
            "generate_manifest('clean-workspace') must return template='clean-workspace'"
        )
        assert manifest.get("file_count", 0) > 0, (
            "generate_manifest('clean-workspace') must return a positive file_count"
        )
