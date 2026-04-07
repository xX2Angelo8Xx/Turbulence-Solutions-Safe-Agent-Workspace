"""Tests for FIX-127: Fix upgrade parity for copilot-instructions.md and counter_config.json.

Verifies:
1. _detect_project_name derives the correct project name from workspace folder names
2. After upgrade, copilot-instructions.md has resolved project name (not {{PROJECT_NAME}})
3. counter_config.json is NOT touched during upgrade
4. counter_config.json is marked security_critical=false in both manifests
"""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_SUBPATH = Path(".github") / "hooks" / "scripts" / "MANIFEST.json"
_COUNTER_CONFIG_REL = ".github/hooks/scripts/counter_config.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_str(text: str) -> str:
    """Compute SHA256 of a UTF-8 string with CRLF normalized to LF (matches generate_manifest)."""
    data = text.encode("utf-8").replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    """Compute SHA256 of raw bytes for binary comparison (matches workspace_upgrader)."""
    return hashlib.sha256(data).hexdigest()


def _build_fake_template(tmp_path: Path, copilot_content: str) -> Path:
    """Build a minimal fake template directory with MANIFEST.json."""
    template_dir = tmp_path / "templates" / "agent-workbench"

    # Create copilot-instructions.md with {{PROJECT_NAME}} tokens
    copilot_path = template_dir / ".github" / "instructions" / "copilot-instructions.md"
    copilot_path.parent.mkdir(parents=True, exist_ok=True)
    copilot_path.write_text(copilot_content, encoding="utf-8")

    # Create a minimal counter_config.json (NOT security_critical in new manifest)
    counter_config_path = template_dir / ".github" / "hooks" / "scripts" / "counter_config.json"
    counter_config_path.parent.mkdir(parents=True, exist_ok=True)
    template_counter_content = json.dumps({"counter_enabled": True, "lockout_threshold": 3})
    counter_config_path.write_text(template_counter_content, encoding="utf-8")

    # Build MANIFEST.json — only copilot-instructions.md is security_critical
    copilot_hash = _sha256_str(copilot_content)
    counter_hash = _sha256_str(template_counter_content)

    manifest = {
        "_comment": "Test manifest",
        "template": "agent-workbench",
        "file_count": 2,
        "files": {
            ".github/instructions/copilot-instructions.md": {
                "sha256": copilot_hash,
                "security_critical": True,
            },
            _COUNTER_CONFIG_REL: {
                "sha256": counter_hash,
                "security_critical": False,
            },
        },
    }

    manifest_path = template_dir / _MANIFEST_SUBPATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return template_dir.parent.parent  # returns tmp_path/templates/.. → templates_dir


# ---------------------------------------------------------------------------
# Test 1: _detect_project_name
# ---------------------------------------------------------------------------

class TestDetectProjectName:
    """Unit tests for _detect_project_name()."""

    def test_sae_prefix_stripped(self, tmp_path):
        """`SAE-MyProject` → `MyProject`."""
        from launcher.core.workspace_upgrader import _detect_project_name

        workspace = tmp_path / "SAE-MyProject"
        workspace.mkdir()
        assert _detect_project_name(workspace) == "MyProject"

    def test_sae_prefix_stripped_complex_name(self, tmp_path):
        """`SAE-Falcon-Test` → `Falcon-Test`."""
        from launcher.core.workspace_upgrader import _detect_project_name

        workspace = tmp_path / "SAE-Falcon-Test"
        workspace.mkdir()
        assert _detect_project_name(workspace) == "Falcon-Test"

    def test_no_sae_prefix_returns_folder_name(self, tmp_path):
        """Folder without SAE- prefix returns folder name unchanged."""
        from launcher.core.workspace_upgrader import _detect_project_name

        workspace = tmp_path / "MyProject"
        workspace.mkdir()
        assert _detect_project_name(workspace) == "MyProject"

    def test_sae_only_returns_empty_string(self, tmp_path):
        """`SAE-` with no suffix → empty string (edge case)."""
        from launcher.core.workspace_upgrader import _detect_project_name

        workspace = tmp_path / "SAE-"
        workspace.mkdir()
        assert _detect_project_name(workspace) == ""


# ---------------------------------------------------------------------------
# Test 2: After upgrade, copilot-instructions.md has resolved project name
# ---------------------------------------------------------------------------

class TestCopilotInstructionsPlaceholderResolution:
    """After upgrade_workspace(), copilot-instructions.md must have resolved placeholders."""

    def _build_workspace(self, tmp_path: Path, project_name: str) -> Path:
        """Create workspace SAE-{project_name} with an outdated copilot-instructions.md."""
        workspace = tmp_path / f"SAE-{project_name}"
        copilot = workspace / ".github" / "instructions" / "copilot-instructions.md"
        copilot.parent.mkdir(parents=True, exist_ok=True)
        # Write the "old" version (any content that doesn't match template hash)
        copilot.write_text("Old copilot instructions content.", encoding="utf-8")

        # Create a dummy .github/version file
        version_file = workspace / ".github" / "version"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text("0.0.0", encoding="utf-8")

        # Create existing counter_config.json with user-specific settings
        counter_path = workspace / ".github" / "hooks" / "scripts" / "counter_config.json"
        counter_path.parent.mkdir(parents=True, exist_ok=True)
        counter_path.write_text(
            json.dumps({"counter_enabled": True, "lockout_threshold": 99}),
            encoding="utf-8",
        )

        return workspace

    def test_placeholder_resolved_after_upgrade(self, tmp_path):
        """After upgrade, copilot-instructions.md must not contain {{PROJECT_NAME}}."""
        from launcher.core.workspace_upgrader import upgrade_workspace

        project_name = "Falcon"
        template_content = (
            "You work in `{{PROJECT_NAME}}/` inside `{{WORKSPACE_NAME}}/`.\n"
            "Read `{{PROJECT_NAME}}/AGENT-RULES.md` for rules."
        )

        workspace = self._build_workspace(tmp_path, project_name)
        fake_templates_dir = tmp_path / "fake_templates"

        # Build fake template
        template_dir = fake_templates_dir / "agent-workbench"
        copilot_path = template_dir / ".github" / "instructions" / "copilot-instructions.md"
        copilot_path.parent.mkdir(parents=True, exist_ok=True)
        # Write in binary mode (LF only) so hash matches across platforms
        content_bytes = template_content.encode("utf-8")
        copilot_path.write_bytes(content_bytes)

        manifest = {
            "files": {
                ".github/instructions/copilot-instructions.md": {
                    "sha256": _sha256_bytes(content_bytes),
                    "security_critical": True,
                },
                _COUNTER_CONFIG_REL: {
                    "sha256": "abc123",
                    "security_critical": False,
                },
            }
        }
        manifest_path = template_dir / _MANIFEST_SUBPATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with patch("launcher.core.workspace_upgrader.TEMPLATES_DIR", fake_templates_dir):
            report = upgrade_workspace(workspace)

        assert not report.errors, f"Upgrade had errors: {report.errors}"

        copilot_result = (workspace / ".github" / "instructions" / "copilot-instructions.md").read_text(encoding="utf-8")
        assert "{{PROJECT_NAME}}" not in copilot_result, (
            "copilot-instructions.md still contains {{PROJECT_NAME}} after upgrade"
        )
        assert "{{WORKSPACE_NAME}}" not in copilot_result, (
            "copilot-instructions.md still contains {{WORKSPACE_NAME}} after upgrade"
        )
        assert project_name in copilot_result, (
            f"Expected project name '{project_name}' to appear in copilot-instructions.md"
        )

    def test_workspace_name_resolved_after_upgrade(self, tmp_path):
        """After upgrade, copilot-instructions.md must contain `SAE-<project>` for the workspace name."""
        from launcher.core.workspace_upgrader import upgrade_workspace

        project_name = "Alpha"
        template_content = "Workspace: `{{WORKSPACE_NAME}}/`."

        workspace = self._build_workspace(tmp_path, project_name)
        fake_templates_dir = tmp_path / "fake_templates"

        template_dir = fake_templates_dir / "agent-workbench"
        copilot_path = template_dir / ".github" / "instructions" / "copilot-instructions.md"
        copilot_path.parent.mkdir(parents=True, exist_ok=True)
        # Write in binary mode (LF only) so hash matches across platforms
        content_bytes = template_content.encode("utf-8")
        copilot_path.write_bytes(content_bytes)

        manifest = {
            "files": {
                ".github/instructions/copilot-instructions.md": {
                    "sha256": _sha256_bytes(content_bytes),
                    "security_critical": True,
                },
            }
        }
        manifest_path = template_dir / _MANIFEST_SUBPATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with patch("launcher.core.workspace_upgrader.TEMPLATES_DIR", fake_templates_dir):
            report = upgrade_workspace(workspace)

        assert not report.errors, f"Upgrade had errors: {report.errors}"
        copilot_result = (workspace / ".github" / "instructions" / "copilot-instructions.md").read_text(encoding="utf-8")
        assert f"SAE-{project_name}" in copilot_result, (
            f"Expected SAE-{project_name} in copilot-instructions.md, got: {copilot_result!r}"
        )


# ---------------------------------------------------------------------------
# Test 3: counter_config.json is NOT touched during upgrade
# ---------------------------------------------------------------------------

class TestCounterConfigNotTouched:
    """counter_config.json must never be overwritten by upgrade_workspace()."""

    def test_counter_config_preserved_during_upgrade(self, tmp_path):
        """User's counter_config.json with custom threshold must survive an upgrade."""
        from launcher.core.workspace_upgrader import upgrade_workspace

        workspace = tmp_path / "SAE-TestProj"
        # Create an outdated copilot-instructions.md so an upgrade is triggered
        copilot = workspace / ".github" / "instructions" / "copilot-instructions.md"
        copilot.parent.mkdir(parents=True, exist_ok=True)
        copilot.write_text("old content", encoding="utf-8")

        version_file = workspace / ".github" / "version"
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text("0.0.0", encoding="utf-8")

        # User has custom counter_config.json
        counter_path = workspace / ".github" / "hooks" / "scripts" / "counter_config.json"
        counter_path.parent.mkdir(parents=True, exist_ok=True)
        user_counter_content = json.dumps({
            "counter_enabled": False,
            "lockout_threshold": 42,
        })
        counter_path.write_text(user_counter_content, encoding="utf-8")

        fake_templates_dir = tmp_path / "fake_templates"
        template_dir = fake_templates_dir / "agent-workbench"
        new_copilot_content = "New `{{PROJECT_NAME}}` content."
        copilot_tmpl = template_dir / ".github" / "instructions" / "copilot-instructions.md"
        copilot_tmpl.parent.mkdir(parents=True, exist_ok=True)
        # Write in binary mode so hash comparison is consistent across platforms
        new_copilot_bytes = new_copilot_content.encode("utf-8")
        copilot_tmpl.write_bytes(new_copilot_bytes)

        # Template counter_config has different values
        counter_tmpl = template_dir / ".github" / "hooks" / "scripts" / "counter_config.json"
        counter_tmpl.parent.mkdir(parents=True, exist_ok=True)
        template_counter_content = json.dumps({"counter_enabled": True, "lockout_threshold": 3})
        counter_tmpl.write_bytes(template_counter_content.encode("utf-8"))

        # Write copilot template in binary mode so hash matches
        new_copilot_bytes = new_copilot_content.encode("utf-8")

        manifest = {
            "files": {
                ".github/instructions/copilot-instructions.md": {
                    "sha256": _sha256_bytes(new_copilot_bytes),
                    "security_critical": True,
                },
                _COUNTER_CONFIG_REL: {
                    "sha256": _sha256_bytes(template_counter_content.encode("utf-8")),
                    "security_critical": False,  # not upgraded
                },
            }
        }
        manifest_path = template_dir / _MANIFEST_SUBPATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with patch("launcher.core.workspace_upgrader.TEMPLATES_DIR", fake_templates_dir):
            report = upgrade_workspace(workspace)

        assert not report.errors, f"Upgrade had errors: {report.errors}"

        # User's counter_config.json must be unchanged
        preserved = counter_path.read_text(encoding="utf-8")
        assert preserved == user_counter_content, (
            f"counter_config.json was overwritten. Expected user content, got: {preserved!r}"
        )

    def test_counter_config_in_never_touch_patterns(self):
        """counter_config.json must appear in _NEVER_TOUCH_PATTERNS."""
        from launcher.core.workspace_upgrader import _NEVER_TOUCH_PATTERNS

        assert _COUNTER_CONFIG_REL in _NEVER_TOUCH_PATTERNS, (
            f"'{_COUNTER_CONFIG_REL}' must be in _NEVER_TOUCH_PATTERNS. "
            f"Current patterns: {_NEVER_TOUCH_PATTERNS}"
        )

    def test_counter_config_is_user_content(self):
        """_is_user_content() must return True for counter_config.json."""
        from launcher.core.workspace_upgrader import _is_user_content

        assert _is_user_content(_COUNTER_CONFIG_REL), (
            "_is_user_content() must return True for counter_config.json"
        )


# ---------------------------------------------------------------------------
# Test 4: counter_config.json marked security_critical=false in manifests
# ---------------------------------------------------------------------------

class TestCounterConfigManifestClassification:
    """counter_config.json must be security_critical=false in both shipped MANIFESTs."""

    def test_counter_config_not_security_critical_agent_workbench(self):
        """counter_config.json must be security_critical=false in agent-workbench MANIFEST."""
        manifest_path = (
            REPO_ROOT / "templates" / "agent-workbench" / _MANIFEST_SUBPATH
        )
        assert manifest_path.exists(), f"MANIFEST.json not found: {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest["files"].get(_COUNTER_CONFIG_REL)
        assert entry is not None, (
            f"'{_COUNTER_CONFIG_REL}' not found in agent-workbench MANIFEST"
        )
        assert entry["security_critical"] is False, (
            f"counter_config.json must have security_critical=false in agent-workbench MANIFEST, "
            f"got: {entry['security_critical']}"
        )

    def test_counter_config_not_security_critical_clean_workspace(self):
        """counter_config.json must be security_critical=false in clean-workspace MANIFEST."""
        manifest_path = (
            REPO_ROOT / "templates" / "clean-workspace" / _MANIFEST_SUBPATH
        )
        assert manifest_path.exists(), f"MANIFEST.json not found: {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest["files"].get(_COUNTER_CONFIG_REL)
        assert entry is not None, (
            f"'{_COUNTER_CONFIG_REL}' not found in clean-workspace MANIFEST"
        )
        assert entry["security_critical"] is False, (
            f"counter_config.json must have security_critical=false in clean-workspace MANIFEST, "
            f"got: {entry['security_critical']}"
        )

    def test_copilot_instructions_still_security_critical_agent_workbench(self):
        """copilot-instructions.md must remain security_critical=true after FIX-127."""
        manifest_path = (
            REPO_ROOT / "templates" / "agent-workbench" / _MANIFEST_SUBPATH
        )
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest["files"].get(".github/instructions/copilot-instructions.md")
        assert entry is not None, (
            "'.github/instructions/copilot-instructions.md' not found in agent-workbench MANIFEST"
        )
        assert entry["security_critical"] is True, (
            "copilot-instructions.md MUST remain security_critical=true — it is the first layer of defense"
        )

    def test_generate_manifest_excludes_counter_config_from_critical(self):
        """generate_manifest._is_security_critical() must return False for counter_config.json."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        try:
            # Re-import to ensure we get the updated version
            import importlib
            import generate_manifest as gm
            importlib.reload(gm)
            assert gm._is_security_critical(_COUNTER_CONFIG_REL) is False, (
                "_is_security_critical() must return False for counter_config.json"
            )
        finally:
            sys.path.pop(0)
