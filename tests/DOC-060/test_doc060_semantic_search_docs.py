"""
DOC-060: Tests verifying semantic_search limitation is documented in
AGENT-RULES.md and copilot-instructions.md.
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENT_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
COPILOT_INSTRUCTIONS = (
    REPO_ROOT
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AGENT-RULES.md tests
# ---------------------------------------------------------------------------


def test_agent_rules_has_known_workarounds_section():
    content = _read(AGENT_RULES)
    assert "## 7. Known Workarounds" in content, (
        "AGENT-RULES.md must have a '## 7. Known Workarounds' section"
    )


def test_agent_rules_semantic_search_row_exists():
    content = _read(AGENT_RULES)
    assert "semantic_search" in content, (
        "AGENT-RULES.md Known Workarounds must contain a semantic_search entry"
    )


def test_agent_rules_semantic_search_mentions_fresh_workspace():
    content = _read(AGENT_RULES)
    assert "fresh workspace" in content.lower(), (
        "AGENT-RULES.md must mention 'fresh workspace' in the semantic_search entry"
    )


def test_agent_rules_semantic_search_mentions_indexing():
    content = _read(AGENT_RULES)
    assert "index" in content.lower(), (
        "AGENT-RULES.md must mention VS Code indexing in the semantic_search entry"
    )


def test_agent_rules_semantic_search_recommends_grep_search():
    content = _read(AGENT_RULES)
    assert "grep_search" in content, (
        "AGENT-RULES.md semantic_search workaround must recommend grep_search"
    )


# ---------------------------------------------------------------------------
# copilot-instructions.md tests
# ---------------------------------------------------------------------------


def test_copilot_instructions_has_known_limitations_section():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "Known Tool Limitations" in content, (
        "copilot-instructions.md must have a 'Known Tool Limitations' section"
    )


def test_copilot_instructions_semantic_search_entry_exists():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "semantic_search" in content, (
        "copilot-instructions.md must contain a semantic_search entry"
    )


def test_copilot_instructions_semantic_search_mentions_fresh_workspace():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "fresh workspace" in content.lower(), (
        "copilot-instructions.md must mention 'fresh workspace' for semantic_search"
    )


def test_copilot_instructions_semantic_search_mentions_indexing():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "index" in content.lower(), (
        "copilot-instructions.md must mention indexing for semantic_search"
    )


def test_copilot_instructions_semantic_search_recommends_grep_search():
    content = _read(COPILOT_INSTRUCTIONS)
    # Both semantic_search and grep_search must appear
    assert "grep_search" in content, (
        "copilot-instructions.md must recommend grep_search as semantic_search fallback"
    )


# ---------------------------------------------------------------------------
# Edge cases added by Tester
# ---------------------------------------------------------------------------


def test_agent_rules_semantic_search_workaround_mentions_include_pattern():
    """The workaround must teach agents to scope grep_search with includePattern."""
    content = _read(AGENT_RULES)
    assert "includePattern" in content, (
        "AGENT-RULES.md semantic_search workaround must mention includePattern "
        "so agents know how to scope grep_search correctly"
    )


def test_copilot_instructions_semantic_search_workaround_mentions_include_pattern():
    """The Known Tool Limitations row must specify includePattern as the fallback detail."""
    content = _read(COPILOT_INSTRUCTIONS)
    assert "includePattern" in content, (
        "copilot-instructions.md semantic_search row must mention includePattern"
    )


def test_agent_rules_semantic_search_in_table_row():
    """The semantic_search workaround must live inside a Markdown table row (pipe-delimited)."""
    content = _read(AGENT_RULES)
    table_rows = [
        line for line in content.splitlines()
        if line.startswith("|") and "semantic_search" in line
    ]
    assert table_rows, (
        "AGENT-RULES.md semantic_search entry must be in a Markdown table row (|...| format)"
    )


def test_copilot_instructions_semantic_search_in_table_row():
    """The semantic_search limitation must be a table row in Known Tool Limitations."""
    content = _read(COPILOT_INSTRUCTIONS)
    table_rows = [
        line for line in content.splitlines()
        if line.startswith("|") and "semantic_search" in line
    ]
    assert table_rows, (
        "copilot-instructions.md semantic_search entry must be in a Markdown table row (|...| format)"
    )
