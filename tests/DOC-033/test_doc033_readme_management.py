"""Tests for DOC-033: README management for agent-workbench template."""
import pathlib

TEMPLATE_ROOT = pathlib.Path(__file__).parents[2] / "templates" / "agent-workbench"
README = TEMPLATE_ROOT / "README.md"
AGENTS_README = TEMPLATE_ROOT / ".github" / "agents" / "README.md"


def test_readme_exists():
    assert README.exists(), "templates/agent-workbench/README.md must exist"


def test_readme_contains_project_name_placeholder():
    content = README.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in content, "README must contain {{PROJECT_NAME}} placeholder"


def test_readme_contains_workspace_name_placeholder():
    content = README.read_text(encoding="utf-8")
    assert "{{WORKSPACE_NAME}}" in content, "README must contain {{WORKSPACE_NAME}} placeholder"


def test_readme_mentions_noagentzone():
    content = README.read_text(encoding="utf-8")
    assert "NoAgentZone" in content, "README must mention NoAgentZone"


def test_readme_is_brief():
    lines = README.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 50, f"README must be under 50 lines, got {len(lines)}"


def test_agents_readme_deleted():
    assert not AGENTS_README.exists(), (
        "templates/agent-workbench/.github/agents/README.md must not exist"
    )
