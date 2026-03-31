"""DOC-039: Verify Tidyup agent and Coordinator integration."""

import pathlib

AGENTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "agents"
AGENT_RULES = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"


def test_tidyup_agent_exists():
    assert (AGENTS_DIR / "tidyup.agent.md").exists()


def test_tidyup_has_frontmatter():
    content = (AGENTS_DIR / "tidyup.agent.md").read_text(encoding="utf-8")
    parts = content.split("---")
    assert len(parts) >= 3
    assert "Tidyup" in parts[1]


def test_tidyup_has_audit_checks():
    content = (AGENTS_DIR / "tidyup.agent.md").read_text(encoding="utf-8")
    assert "architecture.md" in content
    assert "decisions.md" in content
    assert "progress.md" in content
    assert "open-questions.md" in content


def test_coordinator_includes_tidyup():
    content = (AGENTS_DIR / "coordinator.agent.md").read_text(encoding="utf-8")
    frontmatter = content.split("---")[1]
    assert "Tidyup" in frontmatter


def test_coordinator_tools_preserved():
    """User-edited tools line should not have been changed."""
    content = (AGENTS_DIR / "coordinator.agent.md").read_text(encoding="utf-8")
    frontmatter = content.split("---")[1]
    assert "vscode" in frontmatter or "execute" in frontmatter


def test_agent_rules_includes_tidyup():
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "Tidyup" in content


def test_no_deleted_agent_references():
    deleted = ["Scientist", "Criticist", "Writer", "Fixer", "Prototyper"]
    for agent_file in AGENTS_DIR.glob("*.agent.md"):
        content = agent_file.read_text(encoding="utf-8")
        for name in deleted:
            assert name not in content, f"{agent_file.name} references deleted agent {name}"
