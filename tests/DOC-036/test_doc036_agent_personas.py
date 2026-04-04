"""DOC-036: Verify agent persona files are correctly structured."""

import pathlib

TEMPLATE_AGENTS = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "agents"

EXPECTED_AGENTS = ["coordinator", "brainstormer", "researcher", "planner", "programmer", "tester", "workspace-cleaner"]
DELETED_AGENTS = ["scientist", "criticist", "writer", "fixer", "prototyper"]


def test_expected_agents_exist():
    for name in EXPECTED_AGENTS:
        path = TEMPLATE_AGENTS / f"{name}.agent.md"
        assert path.exists(), f"Missing agent file: {path}"


def test_deleted_agents_removed():
    for name in DELETED_AGENTS:
        path = TEMPLATE_AGENTS / f"{name}.agent.md"
        assert not path.exists(), f"Deleted agent still exists: {path}"


def test_no_stale_agent_references():
    for name in EXPECTED_AGENTS:
        path = TEMPLATE_AGENTS / f"{name}.agent.md"
        content = path.read_text(encoding="utf-8")
        for deleted in DELETED_AGENTS:
            assert deleted.lower() not in content.lower(), (
                f"{path.name} still references deleted agent '{deleted}'"
            )


def test_agents_have_agentdocs_section():
    for name in EXPECTED_AGENTS:
        path = TEMPLATE_AGENTS / f"{name}.agent.md"
        content = path.read_text(encoding="utf-8")
        assert "AgentDocs" in content, f"{path.name} missing AgentDocs section"


def test_agents_read_progress_md():
    for name in EXPECTED_AGENTS:
        path = TEMPLATE_AGENTS / f"{name}.agent.md"
        content = path.read_text(encoding="utf-8")
        assert "progress.md" in content, f"{path.name} does not reference progress.md"


def test_researcher_has_fetch_tool():
    path = TEMPLATE_AGENTS / "researcher.agent.md"
    content = path.read_text(encoding="utf-8")
    frontmatter = content.split("---")[1]
    assert "web" in frontmatter or "browser" in frontmatter, "Researcher frontmatter missing web/browser tool"


def test_coordinator_agents_list():
    path = TEMPLATE_AGENTS / "coordinator.agent.md"
    content = path.read_text(encoding="utf-8")
    frontmatter = content.split("---")[1]
    for agent in ["Programmer", "Tester", "Brainstormer", "Researcher", "Planner"]:
        assert agent in frontmatter, f"Coordinator frontmatter missing {agent}"
    for deleted in ["Scientist", "Criticist", "Writer", "Fixer", "Prototyper"]:
        assert deleted not in frontmatter, f"Coordinator frontmatter still lists {deleted}"
