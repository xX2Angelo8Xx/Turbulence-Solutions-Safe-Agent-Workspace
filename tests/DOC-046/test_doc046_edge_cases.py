"""Edge-case tests for DOC-046: Slim copilot-instructions and update references."""
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "agent-workbench"
COPILOT_INSTRUCTIONS = TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md"
AGENTS_DIR = TEMPLATE_ROOT / ".github" / "agents"
README = TEMPLATE_ROOT / "README.md"
PROJECT_CREATOR = REPO_ROOT / "src" / "launcher" / "core" / "project_creator.py"

AGENT_FILES = [
    "brainstormer.agent.md",
    "coordinator.agent.md",
    "planner.agent.md",
    "programmer.agent.md",
    "researcher.agent.md",
    "tester.agent.md",
    "workspace-cleaner.agent.md",
]


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


# --- project_creator.py docstring ---

def test_project_creator_exists():
    assert PROJECT_CREATOR.exists(), "project_creator.py must exist"


def test_project_creator_docstring_references_agentdocs():
    content = _read(PROJECT_CREATOR)
    assert "AgentDocs/AGENT-RULES.md" in content, (
        "project_creator.py docstring must reference AgentDocs/AGENT-RULES.md"
    )


def test_project_creator_no_old_agent_rules_path():
    content = _read(PROJECT_CREATOR)
    # Allow <project_name>/AgentDocs/AGENT-RULES.md but not bare <project_name>/AGENT-RULES.md
    bare_old = re.compile(r"[<{][^>/}]+[>/}]/AGENT-RULES\.md")
    # Remove all occurrences that DO contain AgentDocs
    stripped = content.replace("AgentDocs/AGENT-RULES.md", "")
    assert not bare_old.search(stripped), (
        "project_creator.py must not reference the old direct AGENT-RULES.md path "
        "without AgentDocs/"
    )


# --- copilot-instructions.md structural requirements ---

def test_copilot_instructions_has_workspace_layout_section():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "Workspace Layout" in content, (
        "copilot-instructions.md must contain a 'Workspace Layout' section"
    )


def test_copilot_instructions_uses_project_name_variable():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "{{PROJECT_NAME}}" in content, (
        "copilot-instructions.md must use {{PROJECT_NAME}} template variable"
    )


def test_copilot_instructions_has_security_section():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "Security" in content, (
        "copilot-instructions.md must contain a 'Security' section"
    )


def test_copilot_instructions_security_mentions_permanent_denial():
    content = _read(COPILOT_INSTRUCTIONS)
    # Verify the security section contains the non-retry / permanence message
    assert "permanent" in content.lower() or "do not retry" in content.lower(), (
        "copilot-instructions.md security section must mention that denials are permanent "
        "and agents must not retry"
    )


def test_copilot_instructions_has_known_tool_limitations():
    content = _read(COPILOT_INSTRUCTIONS)
    assert "Known Tool Limitations" in content, (
        "copilot-instructions.md must contain a 'Known Tool Limitations' section"
    )


def test_copilot_instructions_tool_limitations_has_table():
    content = _read(COPILOT_INSTRUCTIONS)
    # A Markdown table must have at least one | char on a data line
    lines = content.splitlines()
    table_lines = [l for l in lines if "|" in l]
    assert len(table_lines) >= 2, (  # header + separator at minimum
        "copilot-instructions.md Known Tool Limitations must include a Markdown table"
    )


def test_copilot_instructions_has_first_action_pointer():
    content = _read(COPILOT_INSTRUCTIONS)
    # Should direct agents to read AGENT-RULES.md as first action
    assert "First Action" in content or "AGENT-RULES.md" in content, (
        "copilot-instructions.md must direct agents to read AGENT-RULES.md"
    )


# --- README doesn't have bare old reference anywhere ---

def test_readme_old_path_absent_in_full_file():
    content = _read(README)
    # Strip AgentDocs occurrences and check the bare form is gone
    stripped = content.replace("AgentDocs/AGENT-RULES.md", "")
    assert "AGENT-RULES.md" not in stripped, (
        "README.md must not contain any bare AGENT-RULES.md reference "
        "outside the AgentDocs/ path"
    )


# --- Agent files are non-trivially non-empty ---

def test_all_agent_files_have_substantive_content():
    for filename in AGENT_FILES:
        path = AGENTS_DIR / filename
        lines = _read(path).splitlines()
        non_empty = [l for l in lines if l.strip()]
        assert len(non_empty) >= 3, (
            f"{filename} must have at least 3 non-empty lines; got {len(non_empty)}"
        )


# --- No rogue {{PROJECT_NAME}}/AGENT-RULES.md (without AgentDocs) anywhere in agent files ---

def test_all_agent_files_no_bare_agent_rules_anywhere():
    """Guard against any form of bare AGENT-RULES.md reference (not under AgentDocs/)."""
    for filename in AGENT_FILES:
        content = _read(AGENTS_DIR / filename)
        stripped = content.replace("AgentDocs/AGENT-RULES.md", "")
        assert "AGENT-RULES.md" not in stripped, (
            f"{filename} must not contain bare AGENT-RULES.md outside AgentDocs/"
        )
