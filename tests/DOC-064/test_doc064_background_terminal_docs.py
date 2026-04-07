"""
DOC-064: Tests verifying that run_in_terminal (isBackground:true) is documented
in both template AGENT-RULES.md files and both copilot-instructions.md files.
Fixes BUG-209.
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

AW_AGENT_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
CW_AGENT_RULES = REPO_ROOT / "templates" / "clean-workspace" / "Project" / "AGENT-RULES.md"
AW_COPILOT = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "instructions" / "copilot-instructions.md"
CW_COPILOT = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "instructions" / "copilot-instructions.md"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ── AGENT-RULES containment tests ────────────────────────────────────────────

def test_agent_workbench_agent_rules_has_isBackground():
    """agent-workbench AGENT-RULES.md must mention isBackground restriction."""
    content = _read(AW_AGENT_RULES)
    assert "isBackground:true" in content, (
        "agent-workbench/Project/AGENT-RULES.md is missing isBackground:true entry"
    )


def test_clean_workspace_agent_rules_has_isBackground():
    """clean-workspace AGENT-RULES.md must mention isBackground restriction."""
    content = _read(CW_AGENT_RULES)
    assert "isBackground:true" in content, (
        "clean-workspace/Project/AGENT-RULES.md is missing isBackground:true entry"
    )


def test_agent_workbench_agent_rules_use_instead_guidance():
    """agent-workbench AGENT-RULES.md must include use_instead timeout guidance."""
    content = _read(AW_AGENT_RULES)
    assert "timeout" in content.lower(), (
        "agent-workbench/Project/AGENT-RULES.md is missing timeout guidance for isBackground"
    )
    assert "foreground" in content.lower(), (
        "agent-workbench/Project/AGENT-RULES.md is missing 'foreground' guidance for isBackground"
    )


def test_clean_workspace_agent_rules_use_instead_guidance():
    """clean-workspace AGENT-RULES.md must include use_instead timeout guidance."""
    content = _read(CW_AGENT_RULES)
    assert "timeout" in content.lower(), (
        "clean-workspace/Project/AGENT-RULES.md is missing timeout guidance for isBackground"
    )
    assert "foreground" in content.lower(), (
        "clean-workspace/Project/AGENT-RULES.md is missing 'foreground' guidance for isBackground"
    )


# ── copilot-instructions containment tests ────────────────────────────────────

def test_agent_workbench_copilot_instructions_has_isBackground():
    """agent-workbench copilot-instructions.md Known Tool Limitations must list isBackground."""
    content = _read(AW_COPILOT)
    assert "isBackground:true" in content, (
        "agent-workbench copilot-instructions.md is missing isBackground:true in Known Tool Limitations"
    )


def test_clean_workspace_copilot_instructions_has_isBackground():
    """clean-workspace copilot-instructions.md Known Tool Limitations must list isBackground."""
    content = _read(CW_COPILOT)
    assert "isBackground:true" in content, (
        "clean-workspace copilot-instructions.md is missing isBackground:true in Known Tool Limitations"
    )


def test_agent_workbench_copilot_instructions_use_instead_guidance():
    """agent-workbench copilot-instructions.md must include timeout/foreground guidance."""
    content = _read(AW_COPILOT)
    assert "timeout" in content.lower(), (
        "agent-workbench copilot-instructions.md is missing timeout guidance for isBackground"
    )
    assert "foreground" in content.lower(), (
        "agent-workbench copilot-instructions.md is missing 'foreground' guidance for isBackground"
    )


def test_clean_workspace_copilot_instructions_use_instead_guidance():
    """clean-workspace copilot-instructions.md must include timeout/foreground guidance."""
    content = _read(CW_COPILOT)
    assert "timeout" in content.lower(), (
        "clean-workspace copilot-instructions.md is missing timeout guidance for isBackground"
    )
    assert "foreground" in content.lower(), (
        "clean-workspace copilot-instructions.md is missing 'foreground' guidance for isBackground"
    )


# ── Location specificity tests ────────────────────────────────────────────────

def test_agent_workbench_agent_rules_blocked_commands_section():
    """agent-workbench AGENT-RULES.md must have isBackground in the Blocked Commands section."""
    content = _read(AW_AGENT_RULES)
    blocked_idx = content.find("### Blocked Commands")
    assert blocked_idx != -1, "Could not find '### Blocked Commands' section in agent-workbench AGENT-RULES.md"
    # Find end of blocked commands section (next heading or end of file)
    next_heading_idx = content.find("\n## ", blocked_idx + 1)
    if next_heading_idx == -1:
        section = content[blocked_idx:]
    else:
        section = content[blocked_idx:next_heading_idx]
    assert "isBackground:true" in section, (
        "isBackground:true not found in the Blocked Commands section of agent-workbench AGENT-RULES.md"
    )


def test_agent_workbench_agent_rules_security_gate_reason():
    """agent-workbench AGENT-RULES.md blocked entry must mention security gate reason."""
    content = _read(AW_AGENT_RULES)
    assert "Security gate cannot validate background command streams" in content, (
        "agent-workbench AGENT-RULES.md is missing the security gate reason for isBackground"
    )


def test_clean_workspace_agent_rules_security_gate_reason():
    """clean-workspace AGENT-RULES.md blocked entry must mention security gate reason."""
    content = _read(CW_AGENT_RULES)
    assert "Security gate cannot validate background command streams" in content, (
        "clean-workspace AGENT-RULES.md is missing the security gate reason for isBackground"
    )
