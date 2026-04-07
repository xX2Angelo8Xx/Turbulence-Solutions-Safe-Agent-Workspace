"""
SAF-056 — Tester edge-case tests for AGENT-RULES.md and copilot-instructions.md.

Covers:
- Placeholder tokens preserved (template integrity)
- Critical security sections present in AGENT-RULES.md (denied zones, git rules)
- copilot-instructions.md does not duplicate large rule blocks that could go stale
- Both files are valid UTF-8 with no encoding errors
- venv-preferred / system-fallback language is consistent
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENT_RULES = (
    REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
)
COPILOT_INSTRUCTIONS = (
    REPO_ROOT
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


# ---------------------------------------------------------------------------
# Placeholder token integrity
# ---------------------------------------------------------------------------


def test_agent_rules_placeholder_project_name():
    """{{PROJECT_NAME}} placeholder must be present so the template can be instantiated."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in content, (
        "AGENT-RULES.md must still contain the {{PROJECT_NAME}} placeholder token"
    )


def test_agent_rules_placeholder_workspace_name():
    """{{WORKSPACE_NAME}} placeholder must be present in AGENT-RULES.md."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "{{WORKSPACE_NAME}}" in content, (
        "AGENT-RULES.md must still contain the {{WORKSPACE_NAME}} placeholder token"
    )


# ---------------------------------------------------------------------------
# Critical security sections must be present in AGENT-RULES.md
# ---------------------------------------------------------------------------


def test_agent_rules_denied_zones_section():
    """AGENT-RULES.md must have a Denied Zones section listing .github/, .vscode/, NoAgentZone/."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "Denied" in content, "AGENT-RULES.md must have a Denied Zones section"
    assert ".github/" in content, "Denied Zones must list .github/"
    assert ".vscode/" in content, "Denied Zones must list .vscode/"
    assert "NoAgentZone" in content, "Denied Zones must list NoAgentZone/"


def test_agent_rules_git_rules_section():
    """AGENT-RULES.md must retain the Git Rules section."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "Git Rules" in content or "## 5" in content, (
        "AGENT-RULES.md must retain the Git Rules section"
    )
    # Blocked git operations must still be listed
    assert "git push --force" in content, (
        "AGENT-RULES.md must document that 'git push --force' is blocked"
    )


def test_agent_rules_denial_counter_section():
    """AGENT-RULES.md must retain the session-scoped Denial Counter section."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "Denial Counter" in content or "denial counter" in content or "lockout" in content, (
        "AGENT-RULES.md must retain the Session-Scoped Denial Counter section"
    )


# ---------------------------------------------------------------------------
# copilot-instructions.md must NOT duplicate large AGENT-RULES sections
# ---------------------------------------------------------------------------


def test_copilot_instructions_no_full_terminal_rules():
    """copilot-instructions.md must not duplicate the full Terminal Rules block."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    # A full copy would have 'Permitted Commands' AND 'Blocked Commands' sections
    has_full_terminal_block = (
        "Permitted Commands" in content and "Blocked Commands" in content
    )
    assert not has_full_terminal_block, (
        "copilot-instructions.md must not duplicate the full Terminal Rules block "
        "(both 'Permitted Commands' and 'Blocked Commands' sections found). "
        "Reference AGENT-RULES.md instead."
    )


def test_copilot_instructions_no_full_git_rules():
    """copilot-instructions.md must not duplicate the full Git Rules block."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    # A copy would have the full blocked-operations table
    has_full_git_block = (
        "git push --force" in content
        and "git reset --hard" in content
        and "git filter-branch" in content
    )
    assert not has_full_git_block, (
        "copilot-instructions.md must not reproduce the full Git Rules table. "
        "Reference AGENT-RULES.md instead."
    )


# ---------------------------------------------------------------------------
# File encoding sanity
# ---------------------------------------------------------------------------


def test_agent_rules_valid_utf8():
    """AGENT-RULES.md must be readable as UTF-8 without errors."""
    raw = AGENT_RULES.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"AGENT-RULES.md contains invalid UTF-8 bytes: {exc}") from exc


def test_copilot_instructions_valid_utf8():
    """copilot-instructions.md must be readable as UTF-8 without errors."""
    raw = COPILOT_INSTRUCTIONS.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(
            f"copilot-instructions.md contains invalid UTF-8 bytes: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Python fallback language consistency
# ---------------------------------------------------------------------------


def test_agent_rules_fallback_uses_word_acceptable():
    """
    The system Python fallback lines must use 'acceptable' — not 'preferred'.
    Prevents copy-paste error where system-python lines are labelled 'preferred'
    like the .venv lines.

    Only bare python commands (no .venv prefix) are system-fallback lines.
    """
    content = AGENT_RULES.read_text(encoding="utf-8")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # Only consider lines that are bare python commands (no .venv prefix)
        stripped = line.strip()
        if stripped.startswith("python ") and ".venv" not in line and "preferred" in line.lower():
            raise AssertionError(
                f"AGENT-RULES.md line {i+1}: bare 'python' (system fallback) is "
                f"incorrectly labelled as 'preferred'. Use 'acceptable' instead.\n"
                f"  Line: {line!r}"
            )


def test_agent_rules_venv_label_not_lost():
    """
    The .venv\\Scripts\\python comment must still mention 'preferred'.
    The SAF-056 edit must not have removed the preferred label from the .venv lines.
    """
    content = AGENT_RULES.read_text(encoding="utf-8")
    # Find lines that contain .venv\Scripts\python and check at least one says preferred
    lines = content.splitlines()
    venv_lines_with_comment = [
        ln for ln in lines
        if r".venv\Scripts\python" in ln and "#" in ln
    ]
    assert any("preferred" in ln for ln in venv_lines_with_comment), (
        "AGENT-RULES.md must have at least one .venv\\Scripts\\python comment "
        "that labels it as 'preferred'"
    )
