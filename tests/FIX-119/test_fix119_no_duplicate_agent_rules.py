"""
Tests for FIX-119: Remove duplicate AGENT-RULES.md from AgentDocs.

Verifies that:
- Project/AgentDocs/AGENT-RULES.md no longer exists (duplicate removed)
- Project/AGENT-RULES.md still exists (primary preserved)
- All template files reference the root path, not the AgentDocs path
- MANIFEST.json does not contain an entry for Project/AgentDocs/AGENT-RULES.md
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "agent-workbench"
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"
AGENT_FILES = [
    "coordinator.agent.md",
    "planner.agent.md",
    "brainstormer.agent.md",
    "programmer.agent.md",
    "README.md",
    "researcher.agent.md",
    "workspace-cleaner.agent.md",
    "tester.agent.md",
]


def test_duplicate_file_does_not_exist():
    """Project/AgentDocs/AGENT-RULES.md must not exist (FIX-119 removed it)."""
    duplicate = TEMPLATE_ROOT / "Project" / "AgentDocs" / "AGENT-RULES.md"
    assert not duplicate.exists(), (
        f"Duplicate AGENT-RULES.md still exists at {duplicate}. "
        "FIX-119 should have removed it."
    )


def test_primary_file_exists():
    """Project/AGENT-RULES.md must exist (the canonical copy)."""
    primary = TEMPLATE_ROOT / "Project" / "AGENT-RULES.md"
    assert primary.is_file(), (
        f"Primary AGENT-RULES.md not found at {primary}. "
        "FIX-119 should have preserved this file."
    )


def test_copilot_instructions_references_root():
    """copilot-instructions.md must reference {{PROJECT_NAME}}/AGENT-RULES.md, not the AgentDocs path."""
    ci = TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md"
    content = ci.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" not in content, (
        "copilot-instructions.md still references AgentDocs/AGENT-RULES.md"
    )
    assert "{{PROJECT_NAME}}/AGENT-RULES.md" in content, (
        "copilot-instructions.md must reference {{PROJECT_NAME}}/AGENT-RULES.md"
    )


def test_agent_files_do_not_reference_agentdocs():
    """All agent .md files must not reference AgentDocs/AGENT-RULES.md."""
    for filename in AGENT_FILES:
        path = AGENTS_DIR / filename
        content = path.read_text(encoding="utf-8")
        assert "AgentDocs/AGENT-RULES.md" not in content, (
            f"{filename} still references AgentDocs/AGENT-RULES.md"
        )


def test_workspace_readme_references_root():
    """templates/agent-workbench/README.md must not reference AgentDocs/AGENT-RULES.md."""
    readme = TEMPLATE_ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" not in content, (
        "templates/agent-workbench/README.md still references AgentDocs/AGENT-RULES.md"
    )


def test_project_readme_references_root():
    """templates/agent-workbench/Project/README.md must not reference AgentDocs/AGENT-RULES.md."""
    readme = TEMPLATE_ROOT / "Project" / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" not in content, (
        "Project/README.md still references AgentDocs/AGENT-RULES.md"
    )


def test_manifest_no_agentdocs_entry():
    """MANIFEST.json must not contain an entry for Project/AgentDocs/AGENT-RULES.md."""
    manifest = TEMPLATE_ROOT / "MANIFEST.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    files = data.get("files", data)
    assert "Project/AgentDocs/AGENT-RULES.md" not in files, (
        "MANIFEST.json still has an entry for Project/AgentDocs/AGENT-RULES.md"
    )
