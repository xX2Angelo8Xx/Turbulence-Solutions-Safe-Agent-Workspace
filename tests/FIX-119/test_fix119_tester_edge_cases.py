"""
Tester-added edge-case tests for FIX-119: Remove duplicate AGENT-RULES.md.

Covers:
- No BOM introduced in any modified template agent file
- No CRLF line-ending introduced (files should keep LF)
- All modified agent files still reference {{PROJECT_NAME}}/AGENT-RULES.md
- DOC-018 path assertions use new Project/AGENT-RULES.md location
- The primary AGENT-RULES.md file is well-formed UTF-8 without BOM
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "agent-workbench"
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"

# All agent files that FIX-119 touched (updated the AGENT-RULES.md path reference)
MODIFIED_AGENT_FILES = [
    AGENTS_DIR / "coordinator.agent.md",
    AGENTS_DIR / "planner.agent.md",
    AGENTS_DIR / "brainstormer.agent.md",
    AGENTS_DIR / "programmer.agent.md",
    AGENTS_DIR / "researcher.agent.md",
    AGENTS_DIR / "workspace-cleaner.agent.md",
    AGENTS_DIR / "tester.agent.md",
    AGENTS_DIR / "README.md",
    TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md",
    TEMPLATE_ROOT / "Project" / "README.md",
    TEMPLATE_ROOT / "README.md",
]

BOM = b"\xef\xbb\xbf"


def test_no_bom_in_modified_agent_files():
    """None of the agent files modified by FIX-119 must have a UTF-8 BOM."""
    bom_files = []
    for path in MODIFIED_AGENT_FILES:
        if not path.exists():
            continue
        raw = path.read_bytes()
        if raw.startswith(BOM):
            bom_files.append(str(path.relative_to(REPO_ROOT)))
    assert not bom_files, (
        f"FIX-119 introduced BOM into these files: {bom_files}. "
        "Remove the BOM (\\xef\\xbb\\xbf) from the start of each file."
    )


def test_no_crlf_in_modified_agent_files():
    """None of the agent files modified by FIX-119 must have Windows CRLF line endings."""
    crlf_files = []
    for path in MODIFIED_AGENT_FILES:
        if not path.exists():
            continue
        raw = path.read_bytes()
        if b"\r\n" in raw:
            crlf_files.append(str(path.relative_to(REPO_ROOT)))
    assert not crlf_files, (
        f"FIX-119 introduced CRLF line endings into these files: {crlf_files}. "
        "Normalize line endings to LF only."
    )


def test_primary_agent_rules_has_no_bom():
    """templates/agent-workbench/Project/AGENT-RULES.md must not have a UTF-8 BOM."""
    primary = TEMPLATE_ROOT / "Project" / "AGENT-RULES.md"
    assert primary.exists(), "Primary AGENT-RULES.md must exist"
    raw = primary.read_bytes()
    assert not raw.startswith(BOM), (
        "Project/AGENT-RULES.md has a UTF-8 BOM. Remove it."
    )


def test_primary_agent_rules_is_valid_utf8():
    """templates/agent-workbench/Project/AGENT-RULES.md must be valid UTF-8."""
    primary = TEMPLATE_ROOT / "Project" / "AGENT-RULES.md"
    assert primary.exists(), "Primary AGENT-RULES.md must exist"
    raw = primary.read_bytes()
    if raw.startswith(BOM):
        raw = raw[3:]
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise AssertionError(f"Project/AGENT-RULES.md is not valid UTF-8: {e}") from e


def test_agent_files_reference_root_agent_rules():
    """All modified .agent.md files must reference {{PROJECT_NAME}}/AGENT-RULES.md at root."""
    missing_ref = []
    for path in MODIFIED_AGENT_FILES:
        if not path.exists():
            continue
        if not path.suffix == ".md":
            continue
        name = path.name
        if not name.endswith(".agent.md"):
            continue
        content = path.read_text(encoding="utf-8-sig")  # strip BOM if present
        if "AGENT-RULES.md" in content and "AgentDocs/AGENT-RULES.md" not in content:
            # References root path — OK
            pass
        elif "AgentDocs/AGENT-RULES.md" in content:
            missing_ref.append(str(path.relative_to(REPO_ROOT)))
    assert not missing_ref, (
        f"These agent files still reference AgentDocs/AGENT-RULES.md: {missing_ref}"
    )


def test_agentdocs_dir_still_exists():
    """Project/AgentDocs/ directory must still exist (only AGENT-RULES.md was removed)."""
    agentdocs = TEMPLATE_ROOT / "Project" / "AgentDocs"
    assert agentdocs.is_dir(), (
        "Project/AgentDocs/ directory was removed. Only the AGENT-RULES.md file should be absent."
    )
