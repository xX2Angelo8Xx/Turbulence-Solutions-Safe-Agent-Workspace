"""Tests for FIX-128: Move AGENT-RULES.md into AgentDocs in agent-workbench.

Acceptance criteria:
  1. templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md exists.
  2. templates/agent-workbench/Project/AGENT-RULES.md does NOT exist.
  3. All agent-workbench template cross-references use the new path.
  4. clean-workspace/Project/AGENT-RULES.md is untouched (still exists at old path).
  5. MANIFEST.json no longer has the old key; has the new key.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
AW_PROJECT = REPO_ROOT / "templates" / "agent-workbench" / "Project"
CW_PROJECT = REPO_ROOT / "templates" / "clean-workspace" / "Project"
MANIFEST = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"


# ── File location tests ───────────────────────────────────────────────────────

def test_agent_rules_exists_in_agentdocs():
    """AGENT-RULES.md must exist at Project/AgentDocs/AGENT-RULES.md."""
    target = AW_PROJECT / "AgentDocs" / "AGENT-RULES.md"
    assert target.is_file(), f"AGENT-RULES.md not found at new location: {target}"


def test_agent_rules_not_at_project_root():
    """AGENT-RULES.md must NOT exist at Project/AGENT-RULES.md in agent-workbench."""
    old_path = AW_PROJECT / "AGENT-RULES.md"
    assert not old_path.exists(), (
        f"AGENT-RULES.md still exists at old location: {old_path}"
    )


def test_clean_workspace_agent_rules_untouched():
    """clean-workspace/Project/AGENT-RULES.md must still exist (clean-workspace unaffected)."""
    cw_path = CW_PROJECT / "AGENT-RULES.md"
    assert cw_path.is_file(), (
        f"clean-workspace AGENT-RULES.md was accidentally removed: {cw_path}"
    )


# ── Cross-reference tests ─────────────────────────────────────────────────────

def test_project_readme_references_new_path():
    """Project/README.md must reference AgentDocs/AGENT-RULES.md, not bare AGENT-RULES.md."""
    content = (AW_PROJECT / "README.md").read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "Project/README.md does not reference AgentDocs/AGENT-RULES.md"
    )


def test_project_readme_no_bare_agent_rules_link():
    """Project/README.md must not have a bare `AGENT-RULES.md` link at the top (line 5)."""
    lines = (AW_PROJECT / "README.md").read_text(encoding="utf-8").splitlines()
    # Line 5 (index 4) used to say "See `AGENT-RULES.md`" — must now say "AgentDocs/"
    for line in lines[:10]:
        if "See `AGENT-RULES.md`" in line:
            raise AssertionError(
                f"Project/README.md still has old bare reference on line: {line!r}"
            )


def test_copilot_instructions_references_new_path():
    """copilot-instructions.md must reference AgentDocs/AGENT-RULES.md."""
    content = (
        REPO_ROOT
        / "templates"
        / "agent-workbench"
        / ".github"
        / "instructions"
        / "copilot-instructions.md"
    ).read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "copilot-instructions.md does not reference AgentDocs/AGENT-RULES.md"
    )


def test_workspace_readme_references_new_path():
    """templates/agent-workbench/README.md must reference AgentDocs/AGENT-RULES.md."""
    content = (REPO_ROOT / "templates" / "agent-workbench" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "agent-workbench/README.md does not reference AgentDocs/AGENT-RULES.md"
    )


# ── MANIFEST.json tests ───────────────────────────────────────────────────────

def test_manifest_has_new_key():
    """MANIFEST.json must contain the new key 'Project/AgentDocs/AGENT-RULES.md'."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    assert "Project/AgentDocs/AGENT-RULES.md" in files, (
        "MANIFEST.json does not have 'Project/AgentDocs/AGENT-RULES.md'"
    )


def test_manifest_no_old_key():
    """MANIFEST.json must NOT contain the old key 'Project/AGENT-RULES.md'."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    assert "Project/AGENT-RULES.md" not in files, (
        "MANIFEST.json still has stale 'Project/AGENT-RULES.md' key"
    )
