"""
DOC-031: Tests for the rewritten AGENT-RULES.md.
Verifies content accuracy and structural requirements.
"""
import pathlib
import re

AGENT_RULES_PATH = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / "Project"
    / "AgentDocs"
    / "AGENT-RULES.md"
)


def _content() -> str:
    return AGENT_RULES_PATH.read_text(encoding="utf-8")


def _lines() -> list[str]:
    return AGENT_RULES_PATH.read_text(encoding="utf-8").splitlines()


def test_file_exists():
    assert AGENT_RULES_PATH.exists(), "AGENT-RULES.md must exist at the expected path"


def test_contains_project_name_placeholder():
    assert "{{PROJECT_NAME}}" in _content(), "File must contain {{PROJECT_NAME}} placeholder"


def test_contains_workspace_name_placeholder():
    assert "{{WORKSPACE_NAME}}" in _content(), "File must contain {{WORKSPACE_NAME}} placeholder"


def test_does_not_contain_blocked_by_design():
    assert "blocked by design" not in _content().lower(), (
        "File must not contain stale 'blocked by design' memory reference"
    )


def test_github_partial_read_access_mentioned():
    content = _content()
    # "read-only" and ".github/" must both appear in the document to
    # reflect the partial read access model
    assert "read-only" in content.lower(), "File must mention read-only access for .github/"
    assert ".github/" in content, "File must mention .github/ in the denied zones section"


def test_cmd_c_in_blocked_commands():
    content = _content()
    assert "cmd /c" in content, "File must list 'cmd /c' in the blocked commands section"


def test_python_m_venv_mentioned():
    content = _content()
    assert "python -m venv" in content, "File must mention 'python -m venv' for .venv creation"


def test_does_not_contain_s8_agent_personas():
    content = _content()
    assert "Available Agent Personas" not in content, (
        "§8 Available Agent Personas section must be removed"
    )
    # §8 heading must not appear (neither as unicode nor as plain text)
    assert not re.search(r"##\s*8\.", content), (
        "No §8 heading must appear in the document"
    )


def test_file_has_fewer_than_220_lines():
    lines = _lines()
    assert len(lines) < 220, (
        f"File must have fewer than 220 lines; found {len(lines)}"
    )


def test_key_sections_present():
    content = _content()
    required_sections = [
        "Allowed Zone",
        "Denied Zones",
        "Tool Permission Matrix",
        "Terminal Rules",
        "Git Rules",
        "Denial Counter",
        "Known Workarounds",
    ]
    for section in required_sections:
        assert section in content, f"Required section '{section}' not found in AGENT-RULES.md"
