"""
Tests for DOC-007: AGENT-RULES.md template.

Verifies that templates/coding/Project/AGENT-RULES.md exists and contains
all 7 required sections as defined in US-033 ACs 2-7, plus the read-first
directive and required placeholders.
"""
import re
from pathlib import Path

AGENT_RULES_PATH = (
    Path(__file__).parent.parent.parent
    / "templates" / "coding" / "Project" / "AGENT-RULES.md"
)


def _content() -> str:
    return AGENT_RULES_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Basic existence
# ---------------------------------------------------------------------------

def test_file_exists():
    assert AGENT_RULES_PATH.is_file(), (
        f"AGENT-RULES.md not found at {AGENT_RULES_PATH}"
    )


# ---------------------------------------------------------------------------
# Read-first directive (must appear near the top)
# ---------------------------------------------------------------------------

def test_has_read_first_directive():
    content = _content()
    # Must instruct agents to read this file at session start.
    assert re.search(r"read this file.{0,60}start.{0,60}session", content, re.IGNORECASE), (
        "Missing 'read this file at the start of every session' directive"
    )


# ---------------------------------------------------------------------------
# Placeholders
# ---------------------------------------------------------------------------

def test_placeholder_project_name():
    content = _content()
    assert "{{PROJECT_NAME}}" in content, "Missing {{PROJECT_NAME}} placeholder"


def test_placeholder_workspace_name():
    content = _content()
    assert "{{WORKSPACE_NAME}}" in content, "Missing {{WORKSPACE_NAME}} placeholder"


# ---------------------------------------------------------------------------
# Section 1 — Allowed Zone
# ---------------------------------------------------------------------------

def test_has_allowed_zone_section():
    content = _content()
    assert re.search(r"##.*allowed zone", content, re.IGNORECASE), (
        "Missing 'Allowed Zone' section"
    )


def test_allowed_zone_references_project_name():
    content = _content()
    # The allowed zone must name the PROJECT_NAME placeholder.
    # Use [^\n]* to prevent the header pattern from spanning multiple lines.
    allowed_section = re.search(
        r"##[^\n]*allowed zone(.*?)(?=^##|\Z)", content,
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    assert allowed_section, "Could not locate Allowed Zone section body"
    assert "{{PROJECT_NAME}}" in allowed_section.group(1), (
        "Allowed Zone section must reference {{PROJECT_NAME}}"
    )


# ---------------------------------------------------------------------------
# Section 2 — Denied Zones
# ---------------------------------------------------------------------------

def test_has_denied_zones_section():
    content = _content()
    assert re.search(r"##.*denied zone", content, re.IGNORECASE), (
        "Missing 'Denied Zones' section"
    )


def test_denied_zone_github():
    content = _content()
    assert ".github/" in content, "Denied zone .github/ not mentioned"


def test_denied_zone_vscode():
    content = _content()
    assert ".vscode/" in content, "Denied zone .vscode/ not mentioned"


def test_denied_zone_noagentzone():
    content = _content()
    assert "NoAgentZone/" in content, "Denied zone NoAgentZone/ not mentioned"


# ---------------------------------------------------------------------------
# Section 3 — Tool Permission Matrix
# ---------------------------------------------------------------------------

def test_has_tool_permission_matrix():
    content = _content()
    assert re.search(r"##.*tool.{0,20}permission.{0,20}matrix", content, re.IGNORECASE), (
        "Missing 'Tool Permission Matrix' section"
    )


def test_matrix_covers_file_tools():
    content = _content()
    for tool in ("read_file", "create_file", "replace_string_in_file",
                 "multi_replace_string_in_file", "list_dir"):
        assert tool in content, f"Tool {tool} not found in permission matrix"


def test_matrix_covers_search_tools():
    content = _content()
    for tool in ("grep_search", "file_search", "semantic_search"):
        assert tool in content, f"Search tool {tool} not found in permission matrix"


def test_matrix_covers_lsp_tools():
    content = _content()
    for tool in ("vscode_listCodeUsages", "vscode_renameSymbol"):
        assert tool in content, f"LSP tool {tool} not found in permission matrix"


def test_matrix_has_allowed_or_denied_or_zone_checked():
    content = _content()
    # Matrix must use at least one of the three permission labels
    assert "Allowed" in content, "Permission label 'Allowed' not found in matrix"
    assert "Denied" in content, "Permission label 'Denied' not found in matrix"
    assert "Zone-checked" in content, "Permission label 'Zone-checked' not found in matrix"


# ---------------------------------------------------------------------------
# Section 4 — Terminal Rules
# ---------------------------------------------------------------------------

def test_has_terminal_rules_section():
    content = _content()
    assert re.search(r"##.*terminal.{0,20}rules", content, re.IGNORECASE), (
        "Missing 'Terminal Rules' section"
    )


def test_terminal_rules_has_permitted_examples():
    content = _content()
    # Must show at least python and git as permitted
    assert re.search(r"python|\.venv", content, re.IGNORECASE), (
        "Terminal Rules must include python/.venv permitted examples"
    )
    assert re.search(r"git status|git add", content), (
        "Terminal Rules must include git command examples"
    )


def test_terminal_rules_has_blocked_examples():
    content = _content()
    assert re.search(r"blocked|BLOCKED", content), (
        "Terminal Rules must include blocked command examples"
    )


# ---------------------------------------------------------------------------
# Section 5 — Git Rules
# ---------------------------------------------------------------------------

def test_has_git_rules_section():
    content = _content()
    assert re.search(r"##.*git.{0,20}rules", content, re.IGNORECASE), (
        "Missing 'Git Rules' section"
    )


def test_git_rules_allowed_operations():
    content = _content()
    for op in ("git status", "git log", "git diff", "git add", "git commit",
               "git fetch", "git pull", "git checkout"):
        assert op in content, f"Allowed git operation '{op}' not listed"


def test_git_rules_blocked_operations():
    content = _content()
    for blocked in ("push --force", "reset --hard", "filter-branch",
                    "gc --force", "clean -f"):
        assert blocked in content, f"Blocked git op '{blocked}' not listed"


# ---------------------------------------------------------------------------
# Section 6 — Session-Scoped Denial Counter
# ---------------------------------------------------------------------------

def test_has_denial_counter_section():
    content = _content()
    assert re.search(r"##.*denial.{0,30}counter|##.*session.{0,30}denial", content, re.IGNORECASE), (
        "Missing 'Session-Scoped Denial Counter' section"
    )


def test_denial_counter_mentions_block_n_of_m():
    content = _content()
    assert re.search(r"block.{0,10}N.{0,10}of.{0,10}M", content, re.IGNORECASE), (
        "Denial counter section must describe 'Block N of M' format"
    )


def test_denial_counter_mentions_new_chat_resets():
    content = _content()
    assert re.search(r"new chat.{0,30}reset|reset.{0,30}new chat", content, re.IGNORECASE), (
        "Denial counter section must state that a new chat resets the counter"
    )


# ---------------------------------------------------------------------------
# Section 7 — Known Workarounds
# ---------------------------------------------------------------------------

def test_has_workarounds_section():
    content = _content()
    assert re.search(r"##.*known.{0,20}workaround", content, re.IGNORECASE), (
        "Missing 'Known Workarounds' section"
    )


def test_workarounds_is_a_table():
    content = _content()
    workarounds_match = re.search(
        r"##.*known.{0,20}workaround(.*?)(?=^##|\Z)", content,
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    assert workarounds_match, "Could not locate Known Workarounds section body"
    section = workarounds_match.group(1)
    # A markdown table has pipe characters
    assert "|" in section, "Known Workarounds must be presented as a markdown table"


def test_workarounds_mentions_set_content():
    content = _content()
    assert "Set-Content" in content, (
        "Known Workarounds should mention Set-Content as Out-File alternative"
    )
