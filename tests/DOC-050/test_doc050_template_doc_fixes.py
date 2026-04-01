"""
DOC-050: Tests for template documentation fixes from v3.3.6 agent feedback report.

Covers:
  - copilot-instructions.md accurate .github/ partial read-only description
  - .github/agents/README.md exists and lists the 7 agents
  - AGENT-RULES §5 git prerequisite note
  - AGENT-RULES §7 semantic_search workaround covers empty results
  - DOC-031 test path regression fix (tests now point to AgentDocs/AGENT-RULES.md)
"""
import pathlib

REPO_ROOT = pathlib.Path(__file__).parents[2]
COPILOT_INSTRUCTIONS = (
    REPO_ROOT / "templates" / "agent-workbench" / ".github"
    / "instructions" / "copilot-instructions.md"
)
AGENTS_README = (
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "agents" / "README.md"
)
AGENT_RULES = (
    REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
)
DOC_031_AGENT_TEST = REPO_ROOT / "tests" / "DOC-031" / "test_doc031_agent_rules.py"
DOC_031_EDGE_TEST = REPO_ROOT / "tests" / "DOC-031" / "test_doc031_tester_edge_cases.py"


# ---------------------------------------------------------------------------
# P1: copilot-instructions.md — .github/ partial read-only description
# ---------------------------------------------------------------------------

def test_copilot_instructions_has_partial_read_only_line():
    """.github/ must be described as partial read-only, not permanent deny."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "Partial read-only" in content, (
        "copilot-instructions.md must describe .github/ as partial read-only"
    )


def test_copilot_instructions_github_not_in_off_limits_line():
    """`.github/` must no longer appear on the Off-limits line alongside .vscode/."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    # The Off-limits line must not group .github/ with the fully-denied paths
    for line in content.splitlines():
        if "Off-limits" in line:
            assert "`.github/`" not in line, (
                "`.github/` must not appear on the Off-limits line — it has partial read access"
            )


def test_copilot_instructions_partial_read_only_lists_subpaths():
    """The partial read-only line must name the allowed subdirectories."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    for subdir in ("instructions/", "skills/", "agents/", "prompts/"):
        assert subdir in content, (
            f"copilot-instructions.md must mention allowed .github/ subdir: {subdir}"
        )


def test_copilot_instructions_hooks_fully_denied():
    """`hooks/` must be mentioned as fully denied in copilot-instructions.md."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "hooks/" in content, (
        "copilot-instructions.md must mention that .github/hooks/ is fully denied"
    )


def test_copilot_instructions_vscode_off_limits():
    """.vscode/ must still be listed as permanent deny."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "`.vscode/`" in content, ".vscode/ must remain listed as off-limits"


def test_copilot_instructions_noagentzone_off_limits():
    """`NoAgentZone/` must still be listed as permanent deny."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "`NoAgentZone/`" in content, "NoAgentZone/ must remain listed as off-limits"


# ---------------------------------------------------------------------------
# P4: .github/agents/README.md exists and lists agents
# ---------------------------------------------------------------------------

def test_agents_readme_exists():
    """.github/agents/README.md must exist."""
    assert AGENTS_README.exists(), ".github/agents/README.md not found"


def test_agents_readme_lists_all_seven_agents():
    """README must reference all 7 agent files."""
    content = AGENTS_README.read_text(encoding="utf-8")
    expected_agents = [
        "coordinator",
        "planner",
        "researcher",
        "brainstormer",
        "programmer",
        "tester",
        "workspace-cleaner",
    ]
    for agent in expected_agents:
        assert agent.lower() in content.lower(), (
            f"README.md must list agent: {agent}"
        )


def test_agents_readme_has_table():
    """README must contain a markdown table."""
    content = AGENTS_README.read_text(encoding="utf-8")
    assert "|" in content, "README.md must contain a markdown table"


# ---------------------------------------------------------------------------
# P3 (doc): AGENT-RULES §5 git prerequisite note
# ---------------------------------------------------------------------------

def test_agent_rules_git_prerequisite_note():
    """AGENT-RULES §5 must contain a prerequisite note about git init."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "Prerequisite" in content, "AGENT-RULES §5 must contain a git Prerequisite note"
    assert "git init" in content, "AGENT-RULES §5 prerequisite note must mention git init"


# ---------------------------------------------------------------------------
# P5: AGENT-RULES §7 semantic_search workaround covers empty results
# ---------------------------------------------------------------------------

def test_agent_rules_semantic_search_workaround_mentions_empty():
    """AGENT-RULES §7 must mention empty results for semantic_search (not only stale)."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "empty" in content.lower(), (
        "AGENT-RULES §7 semantic_search workaround must mention empty results"
    )


# ---------------------------------------------------------------------------
# Path regression fix: DOC-031 tests point to AgentDocs/AGENT-RULES.md
# ---------------------------------------------------------------------------

def test_doc031_agent_test_uses_agentdocs_path():
    """DOC-031 agent test must reference AgentDocs/AGENT-RULES.md, not Project/AGENT-RULES.md."""
    content = DOC_031_AGENT_TEST.read_text(encoding="utf-8")
    assert "AgentDocs" in content, (
        "test_doc031_agent_rules.py must reference AgentDocs/AGENT-RULES.md path"
    )
    assert '/ "Project"\n    / "AGENT-RULES.md"' not in content, (
        "test_doc031_agent_rules.py must not use old Project/AGENT-RULES.md path"
    )


def test_doc031_edge_test_uses_agentdocs_path():
    """DOC-031 edge-case test must reference AgentDocs/AGENT-RULES.md."""
    content = DOC_031_EDGE_TEST.read_text(encoding="utf-8")
    assert "AgentDocs" in content, (
        "test_doc031_tester_edge_cases.py must reference AgentDocs/AGENT-RULES.md path"
    )
