"""
DOC-068: Tests verifying documentation gaps are closed in the clean-workspace template.

Verifies:
  - grep_search and file_search show Zone-checked in AGENT-RULES.md §3
  - NoAgentZone blocking notes present for both search tools
  - get_changed_files appears in §3 as Blocked (with Git Tools header)
  - mcp_gitkraken_* appears in §3 as Blocked (with MCP Tools header)
  - §6 Known Tool Workarounds contains get_changed_files row
  - §6 Known Tool Workarounds contains file_search silent filtering row
  - §6 Known Tool Workarounds contains Get-ChildItem . row
  - README.md does NOT contain 'Force Ask'
  - README.md contains 'Controlled Access'
  - README.md does NOT contain 'trigger an approval dialog'
  - README.md contains accurate auto-allow/deny description
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_RULES = REPO_ROOT / "templates" / "clean-workspace" / "Project" / "AGENT-RULES.md"
README = REPO_ROOT / "templates" / "clean-workspace" / "README.md"
MANIFEST = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "hooks" / "scripts" / "MANIFEST.json"


def _rules_text() -> str:
    return AGENT_RULES.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# §3 Tool Permission Matrix — search tools
# ---------------------------------------------------------------------------

def test_grep_search_is_zone_checked():
    """grep_search permission must be Zone-checked, not Allowed."""
    text = _rules_text()
    assert "| `grep_search` | Zone-checked |" in text, (
        "grep_search must have Zone-checked permission in §3"
    )


def test_grep_search_not_allowed():
    """grep_search must not retain the old 'Allowed' permission value."""
    text = _rules_text()
    assert "| `grep_search` | Allowed |" not in text, (
        "grep_search must not have 'Allowed' permission — should be Zone-checked"
    )


def test_file_search_is_zone_checked():
    """file_search permission must be Zone-checked, not Allowed."""
    text = _rules_text()
    assert "| `file_search` | Zone-checked |" in text, (
        "file_search must have Zone-checked permission in §3"
    )


def test_file_search_not_allowed():
    """file_search must not retain the old 'Allowed' permission value."""
    text = _rules_text()
    assert "| `file_search` | Allowed |" not in text, (
        "file_search must not have 'Allowed' permission — should be Zone-checked"
    )


def test_grep_search_no_agent_zone_blocking_note():
    """grep_search row must include the NoAgentZone blocking note."""
    text = _rules_text()
    assert "includePattern` targeting `NoAgentZone/**` is blocked" in text, (
        "grep_search row must state that includePattern targeting NoAgentZone/** is blocked"
    )


def test_file_search_no_agent_zone_blocking_note():
    """file_search row must include the NoAgentZone blocking note."""
    text = _rules_text()
    assert "`query` targeting `NoAgentZone/**` is blocked" in text, (
        "file_search row must state that query targeting NoAgentZone/** is blocked"
    )


# ---------------------------------------------------------------------------
# §3 Tool Permission Matrix — get_changed_files
# ---------------------------------------------------------------------------

def test_get_changed_files_in_matrix():
    """get_changed_files must appear in §3 permission matrix."""
    text = _rules_text()
    assert "`get_changed_files`" in text, (
        "get_changed_files must be listed in the §3 tool permission matrix"
    )


def test_get_changed_files_is_blocked():
    """get_changed_files must be marked as Blocked."""
    text = _rules_text()
    assert "| `get_changed_files` | Blocked |" in text, (
        "get_changed_files must have Blocked permission in §3"
    )


def test_git_tools_header_present():
    """A 'Git Tools' category header must exist in §3."""
    text = _rules_text()
    assert "**Git Tools**" in text, (
        "§3 must include a 'Git Tools' category header"
    )


# ---------------------------------------------------------------------------
# §3 Tool Permission Matrix — mcp_gitkraken
# ---------------------------------------------------------------------------

def test_mcp_gitkraken_in_matrix():
    """mcp_gitkraken_* must appear in §3 permission matrix."""
    text = _rules_text()
    assert "`mcp_gitkraken_*`" in text, (
        "mcp_gitkraken_* must be listed in the §3 tool permission matrix"
    )


def test_mcp_gitkraken_is_blocked():
    """mcp_gitkraken_* must be marked as Blocked."""
    text = _rules_text()
    assert "| `mcp_gitkraken_*` | Blocked |" in text, (
        "mcp_gitkraken_* must have Blocked permission in §3"
    )


def test_mcp_tools_header_present():
    """A 'MCP Tools' category header must exist in §3."""
    text = _rules_text()
    assert "**MCP Tools**" in text, (
        "§3 must include an 'MCP Tools' category header"
    )


# ---------------------------------------------------------------------------
# §6 Known Tool Workarounds
# ---------------------------------------------------------------------------

def test_section6_get_changed_files_workaround():
    """§6 must contain a workaround row for the blocked get_changed_files tool."""
    text = _rules_text()
    assert "`get_changed_files` tool denied" in text, (
        "§6 must document the get_changed_files workaround"
    )


def test_section6_file_search_silent_filtering():
    """§6 must document the file_search silent filtering of NoAgentZone files."""
    text = _rules_text()
    assert "silently omit `NoAgentZone/` files" in text, (
        "§6 must warn that file_search broad queries silently omit NoAgentZone/ results"
    )


def test_section6_get_child_item_dot_workaround():
    """§6 must contain a workaround row for Get-ChildItem . (explicit dot)."""
    text = _rules_text()
    assert "`Get-ChildItem .`" in text, (
        "§6 must document the Get-ChildItem . workaround"
    )


# ---------------------------------------------------------------------------
# README.md — Tier 2 description
# ---------------------------------------------------------------------------

def test_readme_no_force_ask():
    """README.md must NOT contain the old 'Force Ask' Tier 2 label."""
    text = _readme_text()
    assert "Force Ask" not in text, (
        "README.md must not contain the deprecated 'Force Ask' Tier 2 label"
    )


def test_readme_controlled_access_present():
    """README.md must contain the updated 'Controlled Access' Tier 2 label."""
    text = _readme_text()
    assert "Tier 2 \u2014 Controlled Access" in text, (
        "README.md must contain 'Tier 2 — Controlled Access' label"
    )


def test_readme_no_approval_dialog_wording():
    """README.md must NOT contain the inaccurate 'trigger an approval dialog' wording."""
    text = _readme_text()
    assert "trigger an approval dialog" not in text, (
        "README.md must not contain the outdated 'trigger an approval dialog' description"
    )


def test_readme_accurate_tier2_description():
    """README.md Tier 2 description must mention auto-allow for authorized reads."""
    text = _readme_text()
    assert "auto-allow silently" in text, (
        "README.md Tier 2 description must state that authorized reads auto-allow silently"
    )


# ---------------------------------------------------------------------------
# MANIFEST.json — regenerated and tracks the right files
# ---------------------------------------------------------------------------

def test_manifest_exists():
    """MANIFEST.json for clean-workspace must exist."""
    assert MANIFEST.exists(), (
        f"MANIFEST.json not found at {MANIFEST}"
    )


def test_manifest_tracks_agent_rules():
    """MANIFEST.json must track AGENT-RULES.md."""
    import json
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    assert "Project/AGENT-RULES.md" in files, (
        "MANIFEST.json must include Project/AGENT-RULES.md"
    )


def test_manifest_tracks_readme():
    """MANIFEST.json must track README.md."""
    import json
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    assert "README.md" in files, (
        "MANIFEST.json must include README.md"
    )


def test_manifest_template_field():
    """MANIFEST.json must declare template as clean-workspace."""
    import json
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest.get("template") == "clean-workspace", (
        "MANIFEST.json must have template == 'clean-workspace'"
    )
