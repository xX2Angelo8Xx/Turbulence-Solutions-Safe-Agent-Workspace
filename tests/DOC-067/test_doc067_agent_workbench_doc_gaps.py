"""
DOC-067: Tests verifying documentation changes in the agent-workbench template.

Checks:
1. mcp_gitkraken_* row appears in AGENT-RULES.md Tool Permission Matrix
2. README.md does NOT contain the old "Force Ask" tier label
3. README.md does NOT contain "trigger an approval dialog"
4. README.md contains the corrected "Controlled Access" Tier 2 label
5. Get-ChildItem . workaround appears in AGENT-RULES.md §7 Known Workarounds
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
README = REPO_ROOT / "templates" / "agent-workbench" / "README.md"


def _agent_rules_text() -> str:
    return AGENT_RULES.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README.read_text(encoding="utf-8")


def test_mcp_gitkraken_row_present():
    """mcp_gitkraken_* row must appear in the Tool Permission Matrix."""
    text = _agent_rules_text()
    assert "mcp_gitkraken_*" in text, (
        "AGENT-RULES.md is missing the mcp_gitkraken_* row in the Tool Permission Matrix"
    )


def test_mcp_gitkraken_marked_blocked():
    """mcp_gitkraken_* row must be marked as Blocked."""
    text = _agent_rules_text()
    # Find the line containing mcp_gitkraken_* and confirm it contains "Blocked"
    for line in text.splitlines():
        if "mcp_gitkraken_*" in line:
            assert "Blocked" in line, (
                f"mcp_gitkraken_* row found but not marked Blocked: {line!r}"
            )
            return
    raise AssertionError("mcp_gitkraken_* row not found in AGENT-RULES.md")


def test_readme_no_force_ask():
    """README.md must not contain the old 'Force Ask' Tier 2 label."""
    text = _readme_text()
    assert "Force Ask" not in text, (
        "README.md still contains the old 'Force Ask' tier label — it should be 'Controlled Access'"
    )


def test_readme_no_approval_dialog():
    """README.md must not contain 'trigger an approval dialog'."""
    text = _readme_text()
    assert "trigger an approval dialog" not in text, (
        "README.md still contains the old 'trigger an approval dialog' wording"
    )


def test_readme_tier2_controlled_access():
    """README.md must contain the corrected Tier 2 label 'Controlled Access'."""
    text = _readme_text()
    assert "Controlled Access" in text, (
        "README.md is missing the corrected Tier 2 label 'Controlled Access'"
    )


def test_get_childitem_dot_workaround_present():
    """§7 Known Workarounds must document that Get-ChildItem . is blocked."""
    text = _agent_rules_text()
    assert "Get-ChildItem ." in text and "explicit dot" in text, (
        "AGENT-RULES.md §7 is missing the Get-ChildItem . (explicit dot) workaround"
    )
