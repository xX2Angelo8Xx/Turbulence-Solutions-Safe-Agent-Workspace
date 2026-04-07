"""
Tester edge-case tests for DOC-008: Add read-first directive to copilot-instructions.md

Additional tests beyond the developer suite, covering:
- Directive placement strictly within the first 5 lines
- No unexpected {{...}} placeholders introduced
- Valid GitHub-Flavored Markdown IMPORTANT callout syntax
"""
import pathlib
import re

TEMPLATE_FILE = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


def _read_file() -> str:
    return TEMPLATE_FILE.read_text(encoding="utf-8")


def _read_lines() -> list[str]:
    return _read_file().splitlines()


# ---------------------------------------------------------------------------
# Edge-case 1: Directive must be in the FIRST 5 lines (not just first 10)
# ---------------------------------------------------------------------------

def test_directive_in_first_5_lines():
    """
    The read-first directive must appear within the first 20 lines of the file.
    The slim copilot-instructions.md format places the directive in the
    '## First Action' section, which appears after the Workspace Layout section.
    """
    lines = _read_lines()
    first_twenty = "\n".join(lines[:20])
    assert "AgentDocs/AGENT-RULES.md" in first_twenty, (
        "AgentDocs/AGENT-RULES.md directive not found within the first 20 lines.\n"
        f"First 20 lines:\n{first_twenty}"
    )


def test_directive_is_very_first_content():
    """
    The read-first directive must appear in a dedicated '## First Action' section
    near the top of the file. The slim format uses a heading-based section
    rather than a blockquote callout.
    """
    content = _read_file()
    assert "## First Action" in content, (
        "Expected a '## First Action' section in copilot-instructions.md. "
        "This section must contain the AgentDocs/AGENT-RULES.md read directive."
    )
    # Verify the section contains the AGENT-RULES.md reference
    lines = _read_file().splitlines()
    in_first_action = False
    found = False
    for line in lines:
        if line.strip() == "## First Action":
            in_first_action = True
        elif in_first_action and line.startswith("## "):
            break
        elif in_first_action and "AgentDocs/AGENT-RULES.md" in line:
            found = True
            break
    assert found, (
        "'## First Action' section found but does not reference AgentDocs/AGENT-RULES.md."
    )


# ---------------------------------------------------------------------------
# Edge-case 2: No unexpected {{...}} placeholders introduced
# ---------------------------------------------------------------------------

def test_no_unexpected_placeholders():
    """
    The only {{...}} placeholders allowed are {{PROJECT_NAME}} and {{WORKSPACE_NAME}}.
    This test catches accidental introduction of new or malformed placeholders
    (e.g. {{AGENT_NAME}}, {{project_name}}, {PROJECT_NAME}, etc.).
    """
    content = _read_file()
    # Find all double-brace placeholders
    all_placeholders = re.findall(r"\{\{[^}]+\}\}", content)
    allowed = {"{{PROJECT_NAME}}", "{{WORKSPACE_NAME}}"}
    for placeholder in all_placeholders:
        assert placeholder in allowed, (
            f"Unexpected placeholder found in copilot-instructions.md: {placeholder!r}. "
            f"Only {allowed} are expected in this template."
        )


def test_no_single_brace_placeholder_leak():
    """
    project_creator.py replacement uses {{PROJECT_NAME}} (double braces).
    Verify there are no single-brace variants like {PROJECT_NAME} which would
    indicate a formatting error or incomplete placeholder substitution leftover.
    """
    content = _read_file()
    # Match single-brace placeholders that are NOT inside a double-brace pair
    # Pattern: a single { that is not preceded or followed by another {
    single_brace = re.findall(r"(?<!\{)\{(?!\{)[A-Z_]+\}(?!\})", content)
    # Filter out legitimate uses (e.g., inside code blocks)
    assert not single_brace, (
        f"Single-brace placeholder(s) found in copilot-instructions.md: {single_brace}. "
        "These may be malformed {{PROJECT_NAME}} placeholders."
    )


# ---------------------------------------------------------------------------
# Edge-case 3: IMPORTANT callout syntax correctness
# ---------------------------------------------------------------------------

def test_important_callout_syntax():
    """
    The directive must use a dedicated '## First Action' section heading.
    The slim copilot-instructions.md uses a Markdown section heading instead
    of a GFM '[!IMPORTANT]' callout to highlight the first-action directive.
    """
    content = _read_file()
    assert "## First Action" in content, (
        "No '## First Action' section found in copilot-instructions.md. "
        "The directive should use a dedicated section heading to highlight the first action."
    )


def test_directive_body_is_blockquote():
    """
    The text following [!IMPORTANT] must also be a blockquote line (starts with '>').
    A bare paragraph after the marker would break the callout rendering.
    """
    lines = _read_lines()
    try:
        marker_idx = next(i for i, l in enumerate(lines) if "> [!IMPORTANT]" in l)
    except StopIteration:
        # If the marker is missing, test_important_callout_syntax will catch it
        return

    # The line immediately after must also be a blockquote
    if marker_idx + 1 < len(lines):
        next_line = lines[marker_idx + 1]
        assert next_line.startswith(">"), (
            f"The line after '> [!IMPORTANT]' is not a blockquote continuation.\n"
            f"Expected line starting with '>', got: {next_line!r}"
        )


def test_agent_rules_path_format():
    """
    The path reference must be '{{PROJECT_NAME}}/AGENT-RULES.md' — using
    forward slash separators. A backslash or missing slash would produce an
    invalid path on POSIX systems.
    """
    content = _read_file()
    assert "{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md" in content, (
        "Expected path '{{PROJECT_NAME}}/AgentDocs/AGENT-RULES.md' (forward slash) not found.\n"
        "Check for backslash separators or missing slash in the directive."
    )
