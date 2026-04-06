"""Edge-case tests for GUI-035: Create clean-workspace template structure.

Tester-authored edge cases covering:
- MANIFEST.json hash integrity (hashes must match real file contents)
- Additional byte-identical files not in the Developer's test suite
- Template placeholder completeness
- settings.json security-critical entries
- No pycache or test artifacts in template
- No .github/prompts references in copilot-instructions
- github/version placeholder format
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CLEAN_WORKSPACE = _REPO_ROOT / "templates" / "clean-workspace"
_AGENT_WORKBENCH = _REPO_ROOT / "templates" / "agent-workbench"


def _sha256_normalized(path: Path) -> str:
    """Compute SHA256 with CRLF-normalized to LF (matches generate_manifest.py)."""
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# MANIFEST.json hash integrity  (critical: hashes must match actual files)
# ---------------------------------------------------------------------------

class TestManifestHashIntegrity:
    """Verify every hash in MANIFEST.json matches the actual file content.

    This is the most important edge case: a manifest with wrong hashes would
    allow a tampered security file to go undetected.
    """

    def _load_manifest(self) -> dict:
        return json.loads((_CLEAN_WORKSPACE / ".github" / "hooks" / "scripts" / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_all_manifest_hashes_match_files(self):
        """Every SHA256 in MANIFEST.json must match the actual file on disk."""
        manifest = self._load_manifest()
        files = manifest.get("files", {})
        assert files, "MANIFEST.json must contain at least one file entry"

        mismatches = []
        for rel_path, entry in files.items():
            full_path = _CLEAN_WORKSPACE / rel_path
            if not full_path.exists():
                mismatches.append(f"MISSING: {rel_path}")
                continue
            actual = _sha256_normalized(full_path)
            expected = entry.get("sha256", "")
            if actual != expected:
                mismatches.append(
                    f"HASH_MISMATCH: {rel_path}\n"
                    f"  expected={expected}\n"
                    f"  actual  ={actual}"
                )

        assert not mismatches, (
            "MANIFEST.json hashes do not match actual files:\n" + "\n".join(mismatches)
        )

    def test_manifest_file_count_matches_entries(self):
        """MANIFEST.json file_count must equal the number of file entries."""
        manifest = self._load_manifest()
        declared_count = manifest.get("file_count", 0)
        actual_count = len(manifest.get("files", {}))
        assert declared_count == actual_count, (
            f"MANIFEST.json file_count={declared_count} does not match "
            f"actual entry count={actual_count}"
        )

    def test_all_security_critical_files_marked(self):
        """All hook scripts must be marked security_critical=true in MANIFEST.json."""
        manifest = self._load_manifest()
        files = manifest.get("files", {})
        security_files = [
            ".github/hooks/scripts/security_gate.py",
            ".github/hooks/scripts/update_hashes.py",
            ".github/hooks/scripts/zone_classifier.py",
            ".github/hooks/scripts/require-approval.ps1",
            ".github/hooks/scripts/require-approval.sh",
            ".github/hooks/scripts/reset_hook_counter.py",
            ".github/hooks/scripts/counter_config.json",
            ".github/hooks/require-approval.json",
        ]
        for f in security_files:
            assert f in files, f"MANIFEST.json must track {f}"
            assert files[f].get("security_critical") is True, (
                f"{f} must be marked security_critical=true in MANIFEST.json"
            )


# ---------------------------------------------------------------------------
# Additional byte-identical file checks (not in Developer's test suite)
# ---------------------------------------------------------------------------

class TestAdditionalByteIdenticalFiles:
    """counter_config.json, reset_hook_counter.py, .gitignore, and NoAgentZone/README.md
    are security-critical or shared infrastructure — they must be byte-identical to
    agent-workbench to prevent divergence in the security enforcement layer.
    """

    @pytest.mark.parametrize("rel_path", [
        ".github/hooks/scripts/counter_config.json",
        ".github/hooks/scripts/reset_hook_counter.py",
        ".gitignore",
        "NoAgentZone/README.md",
    ])
    def test_file_byte_identical_to_agent_workbench(self, rel_path: str):
        """File must be byte-identical (CRLF-normalised) to agent-workbench."""
        clean = _CLEAN_WORKSPACE / rel_path
        agent = _AGENT_WORKBENCH / rel_path
        assert clean.is_file(), f"clean-workspace missing: {rel_path}"
        assert agent.is_file(), f"agent-workbench missing (reference): {rel_path}"
        assert _sha256_normalized(clean) == _sha256_normalized(agent), (
            f"{rel_path} differs from agent-workbench — must be byte-identical"
        )


# ---------------------------------------------------------------------------
# Template placeholder completeness
# ---------------------------------------------------------------------------

class TestTemplatePlaceholders:
    """Template files must contain all required placeholders so that the launcher
    can substitute project names, workspace names, and version numbers correctly.
    Placeholders not substituted at creation time would silently appear in the
    live workspace, confusing the AI agent.
    """

    def test_readme_has_workspace_name_placeholder(self):
        """README.md must contain {{WORKSPACE_NAME}} placeholder."""
        content = (_CLEAN_WORKSPACE / "README.md").read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" in content, (
            "README.md must contain {{WORKSPACE_NAME}} template placeholder"
        )

    def test_readme_has_project_name_placeholder(self):
        """README.md must reference {{PROJECT_NAME}} so project folder is named."""
        content = (_CLEAN_WORKSPACE / "README.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" in content, (
            "README.md must contain {{PROJECT_NAME}} template placeholder"
        )

    def test_project_readme_has_project_name_placeholder(self):
        """Project/README.md must contain {{PROJECT_NAME}} placeholder."""
        content = (_CLEAN_WORKSPACE / "Project" / "README.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" in content, (
            "Project/README.md must contain {{PROJECT_NAME}} template placeholder"
        )

    def test_copilot_instructions_has_workspace_name_placeholder(self):
        """copilot-instructions.md must contain {{WORKSPACE_NAME}} placeholder."""
        content = (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" in content, (
            "copilot-instructions.md must contain {{WORKSPACE_NAME}} placeholder"
        )

    def test_github_version_has_version_placeholder(self):
        """.github/version must contain {{VERSION}} placeholder."""
        content = (_CLEAN_WORKSPACE / ".github" / "version").read_text(encoding="utf-8")
        assert "{{VERSION}}" in content.strip(), (
            ".github/version must contain {{VERSION}} placeholder for launcher substitution"
        )

    def test_agent_rules_has_workspace_name_placeholder(self):
        """Project/AGENT-RULES.md must contain {{WORKSPACE_NAME}} placeholder."""
        content = (_CLEAN_WORKSPACE / "Project" / "AGENT-RULES.md").read_text(encoding="utf-8")
        assert "{{WORKSPACE_NAME}}" in content, (
            "Project/AGENT-RULES.md must contain {{WORKSPACE_NAME}} template placeholder"
        )


# ---------------------------------------------------------------------------
# settings.json security completeness
# ---------------------------------------------------------------------------

class TestVscodeSettingsCompleteness:
    """settings.json must hide all security tiers from the file explorer.
    Failing to hide NoAgentZone would expose it to the AI agent.
    """

    def _load_settings(self) -> dict:
        return json.loads(
            (_CLEAN_WORKSPACE / ".vscode" / "settings.json").read_text(encoding="utf-8")
        )

    def test_search_exclude_hides_novagentzone(self):
        """search.exclude must hide **/NoAgentZone so agents cannot discover it."""
        settings = self._load_settings()
        search_excl = settings.get("search.exclude", {})
        assert "**/NoAgentZone" in search_excl, (
            "settings.json search.exclude must hide **/NoAgentZone"
        )

    def test_chat_auto_approve_disabled(self):
        """chat.tools.global.autoApprove must be false to prevent unrestricted tool use."""
        settings = self._load_settings()
        assert settings.get("chat.tools.global.autoApprove") is False, (
            "settings.json chat.tools.global.autoApprove must be false"
        )

    def test_workspace_trust_enabled(self):
        """security.workspace.trust.enabled must be true."""
        settings = self._load_settings()
        assert settings.get("security.workspace.trust.enabled") is True, (
            "settings.json security.workspace.trust.enabled must be true"
        )


# ---------------------------------------------------------------------------
# No polluting files in template
# ---------------------------------------------------------------------------

class TestNoTemplatePollution:
    """Template must not contain __pycache__, .pytest_cache, or any .pyc files.
    Including cached Python bytecode would pollute new workspaces created from
    this template.
    """

    def test_no_pycache_directories(self):
        """Template must not contain any __pycache__ directories."""
        pycache_dirs = list(_CLEAN_WORKSPACE.rglob("__pycache__"))
        assert not pycache_dirs, (
            f"clean-workspace must not contain __pycache__ directories: {pycache_dirs}"
        )

    def test_no_pyc_files(self):
        """Template must not contain any .pyc files."""
        pyc_files = list(_CLEAN_WORKSPACE.rglob("*.pyc"))
        assert not pyc_files, (
            f"clean-workspace must not contain .pyc files: {pyc_files}"
        )

    def test_no_pytest_cache(self):
        """Template must not contain .pytest_cache directories."""
        pytest_cache = list(_CLEAN_WORKSPACE.rglob(".pytest_cache"))
        assert not pytest_cache, (
            f"clean-workspace must not contain .pytest_cache: {pytest_cache}"
        )


# ---------------------------------------------------------------------------
# copilot-instructions content safety
# ---------------------------------------------------------------------------

class TestCopilotInstructionsSafety:
    """copilot-instructions.md must not reference infrastructure that does not
    exist in the clean-workspace template. Missing directories referenced in
    instructions silently mislead the AI agent.
    """

    def _content(self) -> str:
        return (
            _CLEAN_WORKSPACE / ".github" / "instructions" / "copilot-instructions.md"
        ).read_text(encoding="utf-8")

    def test_no_prompts_reference(self):
        """copilot-instructions.md must not reference .github/prompts/."""
        assert ".github/prompts" not in self._content(), (
            "copilot-instructions.md must not reference .github/prompts/ (directory not in template)"
        )

    def test_no_agentdocs_path_reference(self):
        """copilot-instructions.md must not reference Project/AgentDocs path."""
        assert "Project/AgentDocs" not in self._content(), (
            "copilot-instructions.md must not reference Project/AgentDocs (directory not in template)"
        )
