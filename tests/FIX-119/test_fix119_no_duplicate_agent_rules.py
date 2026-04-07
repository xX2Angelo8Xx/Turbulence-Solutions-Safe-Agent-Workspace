"""
Tests for FIX-119: AGENT-RULES.md location in agent-workbench template.

Updated by FIX-128: AGENT-RULES.md has been moved to Project/AgentDocs/AGENT-RULES.md.
Verifies that:
- Project/AgentDocs/AGENT-RULES.md exists (canonical location after FIX-128)
- Project/AGENT-RULES.md does NOT exist (removed by FIX-128)
- All template files reference the AgentDocs path, not the bare Project root path
- MANIFEST.json contains an entry for Project/AgentDocs/AGENT-RULES.md
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
    """Project/AGENT-RULES.md must not exist (FIX-128 moved it to AgentDocs)."""
    old_path = TEMPLATE_ROOT / "Project" / "AGENT-RULES.md"
    assert not old_path.exists(), (
        f"Stale AGENT-RULES.md found at old path {old_path}. "
        "FIX-128 moved it to Project/AgentDocs/AGENT-RULES.md."
    )


def test_primary_file_exists():
    """Project/AgentDocs/AGENT-RULES.md must exist (canonical location after FIX-128)."""
    primary = TEMPLATE_ROOT / "Project" / "AgentDocs" / "AGENT-RULES.md"
    assert primary.is_file(), (
        f"Primary AGENT-RULES.md not found at {primary}. "
        "FIX-128 should have moved it to Project/AgentDocs/AGENT-RULES.md."
    )


def test_copilot_instructions_references_root():
    """copilot-instructions.md must reference {{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md."""
    ci = TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md"
    content = ci.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "copilot-instructions.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_agent_files_do_not_reference_agentdocs():
    """All agent .md files must reference AgentDocs/AGENT-RULES.md (not the bare root path)."""
    for filename in AGENT_FILES:
        path = AGENTS_DIR / filename
        content = path.read_text(encoding="utf-8")
        assert "AgentDocs/AGENT-RULES.md" in content, (
            f"{filename} does not reference AgentDocs/AGENT-RULES.md"
        )


def test_workspace_readme_references_root():
    """templates/agent-workbench/README.md must reference AgentDocs/AGENT-RULES.md."""
    readme = TEMPLATE_ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "templates/agent-workbench/README.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_project_readme_references_root():
    """templates/agent-workbench/Project/README.md must reference AgentDocs/AGENT-RULES.md."""
    readme = TEMPLATE_ROOT / "Project" / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "Project/README.md must reference AgentDocs/AGENT-RULES.md"
    )


def test_manifest_no_agentdocs_entry():
    """MANIFEST.json must contain an entry for Project/AgentDocs/AGENT-RULES.md."""
    manifest = TEMPLATE_ROOT / ".github" / "hooks" / "scripts" / "MANIFEST.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    files = data.get("files", data)
    assert "Project/AgentDocs/AGENT-RULES.md" in files, (
        "MANIFEST.json must have an entry for 'Project/AgentDocs/AGENT-RULES.md'"
    )
