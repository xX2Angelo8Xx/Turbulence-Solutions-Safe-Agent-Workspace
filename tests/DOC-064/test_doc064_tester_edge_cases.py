"""
DOC-064: Tester edge-case tests for isBackground:true documentation.

Tester additions beyond the Developer's test_doc064_background_terminal_docs.py:
- Verify the clean-workspace entry appears in a blocked/restricted section (not just anywhere)
- Verify security-gate reason text is correct in both copilot-instructions files
- Verify both MANIFEST.json files are up to date after template edits
- Boundary: check the blocked section heading terminates before the entry goes missing
- Verify no duplicate isBackground entries (single authoritative entry per file)
"""

import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

AW_AGENT_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
CW_AGENT_RULES = REPO_ROOT / "templates" / "clean-workspace" / "Project" / "AGENT-RULES.md"
AW_COPILOT = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "instructions" / "copilot-instructions.md"
CW_COPILOT = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "instructions" / "copilot-instructions.md"
AW_MANIFEST = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
CW_MANIFEST = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
GENERATE_MANIFEST = REPO_ROOT / "scripts" / "generate_manifest.py"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# ── Location in blocked/restricted section ────────────────────────────────────

def test_clean_workspace_agent_rules_isBackground_in_restricted_section():
    """clean-workspace AGENT-RULES.md must have isBackground in a 'Known Tool Workarounds' or blocked/restricted section."""
    content = _read(CW_AGENT_RULES)
    # Find the section heading containing blocked/workaround guidance
    section_markers = ["Known Tool Workarounds", "Blocked", "blocked", "Restricted"]
    section_idx = -1
    section_heading = None
    for marker in section_markers:
        idx = content.find(marker)
        if idx != -1:
            section_idx = idx
            section_heading = marker
            break
    assert section_idx != -1, (
        f"Could not find any blocked/workaround section in clean-workspace AGENT-RULES.md. "
        f"Checked: {section_markers}"
    )
    # isBackground must appear after the section heading
    isBackground_idx = content.find("isBackground:true")
    assert isBackground_idx > section_idx, (
        f"isBackground:true (pos {isBackground_idx}) must appear after "
        f"'{section_heading}' heading (pos {section_idx}) in clean-workspace AGENT-RULES.md"
    )


def test_agent_workbench_agent_rules_isBackground_in_blocked_section():
    """agent-workbench AGENT-RULES.md must have isBackground in the Blocked Commands section (§4)."""
    content = _read(AW_AGENT_RULES)
    blocked_idx = content.find("### Blocked Commands")
    assert blocked_idx != -1, "Missing '### Blocked Commands' in agent-workbench AGENT-RULES.md"
    # Find next heading after the blocked section
    next_heading_idx = content.find("\n## ", blocked_idx + 1)
    next_sub_heading_idx = content.find("\n### ", blocked_idx + 1)
    # Take whichever comes first as the end of the section
    end_idx = len(content)
    if next_heading_idx != -1:
        end_idx = min(end_idx, next_heading_idx)
    if next_sub_heading_idx != -1:
        end_idx = min(end_idx, next_sub_heading_idx)
    section = content[blocked_idx:end_idx]
    assert "isBackground:true" in section, (
        "isBackground:true not found within the Blocked Commands section in agent-workbench AGENT-RULES.md"
    )


# ── Security gate reason in copilot-instructions ──────────────────────────────

def test_agent_workbench_copilot_instructions_security_gate_reason():
    """agent-workbench copilot-instructions.md must state the security gate reason for isBackground."""
    content = _read(AW_COPILOT)
    assert "Security gate cannot validate background command streams" in content, (
        "agent-workbench copilot-instructions.md is missing the security gate reason for isBackground"
    )


def test_clean_workspace_copilot_instructions_security_gate_reason():
    """clean-workspace copilot-instructions.md must state the security gate reason for isBackground."""
    content = _read(CW_COPILOT)
    assert "Security gate cannot validate background command streams" in content, (
        "clean-workspace copilot-instructions.md is missing the security gate reason for isBackground"
    )


# ── Copilot-instructions Known Tool Limitations section ──────────────────────

def test_agent_workbench_copilot_instructions_isBackground_in_known_limitations():
    """agent-workbench copilot-instructions.md must have isBackground in the Known Tool Limitations table."""
    content = _read(AW_COPILOT)
    # Find the Known Tool Limitations heading (or equivalent)
    markers = ["Known Tool Limitations", "Known Tool Workarounds", "Known Limitations"]
    section_idx = -1
    for marker in markers:
        idx = content.find(marker)
        if idx != -1:
            section_idx = idx
            break
    assert section_idx != -1, (
        "Could not find 'Known Tool Limitations' section in agent-workbench copilot-instructions.md"
    )
    isBackground_idx = content.find("isBackground:true")
    assert isBackground_idx > section_idx, (
        "isBackground:true must appear inside the Known Tool Limitations section in "
        "agent-workbench copilot-instructions.md"
    )


def test_clean_workspace_copilot_instructions_isBackground_in_known_limitations():
    """clean-workspace copilot-instructions.md must have isBackground in the Known Tool Limitations table."""
    content = _read(CW_COPILOT)
    markers = ["Known Tool Limitations", "Known Tool Workarounds", "Known Limitations"]
    section_idx = -1
    for marker in markers:
        idx = content.find(marker)
        if idx != -1:
            section_idx = idx
            break
    assert section_idx != -1, (
        "Could not find 'Known Tool Limitations' section in clean-workspace copilot-instructions.md"
    )
    isBackground_idx = content.find("isBackground:true")
    assert isBackground_idx > section_idx, (
        "isBackground:true must appear inside the Known Tool Limitations section in "
        "clean-workspace copilot-instructions.md"
    )


# ── No duplicate entries ──────────────────────────────────────────────────────

def test_agent_workbench_agent_rules_single_isBackground_entry():
    """agent-workbench AGENT-RULES.md must have exactly one isBackground:true entry in blocked table."""
    content = _read(AW_AGENT_RULES)
    # Count occurrences in the blocked commands section only
    blocked_idx = content.find("### Blocked Commands")
    assert blocked_idx != -1
    next_section = content.find("\n## ", blocked_idx + 1)
    section = content[blocked_idx:next_section] if next_section != -1 else content[blocked_idx:]
    count = section.count("isBackground:true")
    assert count == 1, (
        f"Expected exactly 1 isBackground:true entry in Blocked Commands section, found {count}"
    )


def test_clean_workspace_agent_rules_single_isBackground_entry():
    """clean-workspace AGENT-RULES.md must have exactly one isBackground:true entry."""
    content = _read(CW_AGENT_RULES)
    count = content.count("isBackground:true")
    assert count == 1, (
        f"Expected exactly 1 isBackground:true entry in clean-workspace AGENT-RULES.md, found {count}"
    )


# ── MANIFEST integrity after template edits ───────────────────────────────────

def test_agent_workbench_manifest_is_current():
    """MANIFEST.json for agent-workbench must be up to date after DOC-064 template edits."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_MANIFEST), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"agent-workbench MANIFEST.json is out of date (exit {result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_clean_workspace_manifest_is_current():
    """MANIFEST.json for clean-workspace must be up to date after DOC-064 template edits."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_MANIFEST), "--check", "--template", "clean-workspace"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"clean-workspace MANIFEST.json is out of date (exit {result.returncode}):\n"
        f"{result.stdout}\n{result.stderr}"
    )


# ── MANIFEST.json structure (copilot-instructions.md tracked as security-critical) ──

def test_agent_workbench_manifest_copilot_instructions_is_security_critical():
    """agent-workbench MANIFEST must mark copilot-instructions.md as security_critical."""
    data = json.loads(AW_MANIFEST.read_text(encoding="utf-8"))
    key = ".github/instructions/copilot-instructions.md"
    assert key in data["files"], f"{key} not tracked in agent-workbench MANIFEST.json"
    assert data["files"][key].get("security_critical") is True, (
        f"{key} must be security_critical=true in agent-workbench MANIFEST.json"
    )


def test_clean_workspace_manifest_copilot_instructions_is_security_critical():
    """clean-workspace MANIFEST must mark copilot-instructions.md as security_critical."""
    data = json.loads(CW_MANIFEST.read_text(encoding="utf-8"))
    key = ".github/instructions/copilot-instructions.md"
    assert key in data["files"], f"{key} not tracked in clean-workspace MANIFEST.json"
    assert data["files"][key].get("security_critical") is True, (
        f"{key} must be security_critical=true in clean-workspace MANIFEST.json"
    )
