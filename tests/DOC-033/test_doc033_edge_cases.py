"""Edge-case tests for DOC-033: README management for agent-workbench template.

Added by Tester Agent to cover cases beyond the Developer's baseline tests.
"""
import pathlib
import re

TEMPLATE_ROOT = pathlib.Path(__file__).parents[2] / "templates" / "agent-workbench"
README = TEMPLATE_ROOT / "README.md"
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"

# All expected .agent.md files that must survive the deletion of README.md
EXPECTED_AGENT_FILES = [
    "brainstormer.agent.md",
    "coordinator.agent.md",
    "criticist.agent.md",
    "fixer.agent.md",
    "planner.agent.md",
    "programmer.agent.md",
    "prototyper.agent.md",
    "researcher.agent.md",
    "scientist.agent.md",
    "tester.agent.md",
    "writer.agent.md",
]

# Patterns that indicate an agent-facing instruction document
AGENT_INSTRUCTION_PATTERNS = [
    r"^##\s+Instructions",
    r"^##\s+Security Zones",
    r"\bYou are an? (AI|agent|assistant)\b",
    r"\bYour task is\b",
    r"\bALWAYS\b",
    r"\bNEVER\b",
    r"\bdo not access\b",
    r"\bdo not read\b",
    r"\bYou must\b",
    r"\bYou should\b",
]


def test_readme_not_agent_facing():
    """README must not contain patterns that indicate it is directed at AI agents."""
    content = README.read_text(encoding="utf-8")
    for pattern in AGENT_INSTRUCTION_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        assert match is None, (
            f"README appears to contain agent-facing instruction pattern "
            f"'{pattern}': matched '{match.group()}'"
        )


def test_readme_mentions_agent_rules_file():
    """README must reference AGENT-RULES.md so users know where to customise agent behaviour."""
    content = README.read_text(encoding="utf-8")
    assert "AGENT-RULES.md" in content, (
        "README must reference AGENT-RULES.md to guide users on customising agent behaviour"
    )


def test_agent_md_files_still_present():
    """All .agent.md files in .github/agents/ must still exist — only README.md was deleted."""
    missing = [f for f in EXPECTED_AGENT_FILES if not (AGENTS_DIR / f).exists()]
    assert missing == [], (
        f"The following .agent.md files are unexpectedly missing from "
        f".github/agents/: {missing}"
    )


def test_agents_dir_contains_only_agent_md_files():
    """No README.md or other unexpected files should exist in .github/agents/."""
    actual_files = {p.name for p in AGENTS_DIR.iterdir() if p.is_file()}
    unexpected = actual_files - set(EXPECTED_AGENT_FILES)
    assert unexpected == set(), (
        f"Unexpected files found in .github/agents/: {unexpected}"
    )


def test_readme_is_user_friendly_greeting():
    """README must start with a user-friendly heading (the workspace name placeholder)."""
    content = README.read_text(encoding="utf-8")
    first_non_empty = next(
        (line for line in content.splitlines() if line.strip()), ""
    )
    assert first_non_empty.startswith("#"), (
        "README must start with a markdown heading"
    )
    assert "{{WORKSPACE_NAME}}" in first_non_empty or "Welcome" in content, (
        "README should greet the user with the workspace name or a Welcome message"
    )


def test_readme_no_raw_agent_names():
    """README must not expose internal agent file names (e.g. 'brainstormer.agent.md')."""
    content = README.read_text(encoding="utf-8")
    for agent_file in EXPECTED_AGENT_FILES:
        assert agent_file not in content, (
            f"README must not reference internal agent file '{agent_file}'"
        )
