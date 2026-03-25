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
    The read-first directive must appear within the first 5 lines of the file.
    Placing it later would force agents to scroll past header content before
    seeing the instruction, defeating its purpose.
    """
    lines = _read_lines()
    first_five = "\n".join(lines[:5])
    assert "AGENT-RULES.md" in first_five, (
        "AGENT-RULES.md directive not found within the first 5 lines.\n"
        f"First 5 lines:\n{first_five}"
    )


def test_directive_is_very_first_content():
    """
    The directive must be the very first non-empty content in the file.
    Nothing should appear before it — not a heading, not a blank line with text,
    not a comment.
    """
    lines = _read_lines()
    # Skip leading blank lines (there should be none, but be lenient about that)
    first_content_line = next((l for l in lines if l.strip()), "")
    assert first_content_line.startswith(">"), (
        f"First non-empty line of copilot-instructions.md does not start with '>'.\n"
        f"Expected a blockquote directive, got: {first_content_line!r}"
    )


# ---------------------------------------------------------------------------
# Edge-case 2: No unexpected {{...}} placeholders introduced
# ---------------------------------------------------------------------------

def test_no_unexpected_placeholders():
    """
    The only {{...}} placeholder allowed in the directive is {{PROJECT_NAME}}.
    This test catches accidental introduction of new or malformed placeholders
    (e.g. {{AGENT_NAME}}, {{project_name}}, {PROJECT_NAME}, etc.).
    """
    content = _read_file()
    # Find all double-brace placeholders
    all_placeholders = re.findall(r"\{\{[^}]+\}\}", content)
    for placeholder in all_placeholders:
        assert placeholder == "{{PROJECT_NAME}}", (
            f"Unexpected placeholder found in copilot-instructions.md: {placeholder!r}. "
            "Only {{PROJECT_NAME}} is expected in this template."
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
    The directive must use the exact GitHub-Flavored Markdown IMPORTANT callout
    syntax: '> [!IMPORTANT]' on its own line.
    This is the standard GFM alert syntax supported by GitHub, GitLab, and VS Code.
    """
    lines = _read_lines()
    # [!IMPORTANT] must appear as a standalone callout marker
    callout_lines = [l for l in lines if "[!IMPORTANT]" in l]
    assert callout_lines, (
        "No '[!IMPORTANT]' callout marker found in copilot-instructions.md. "
        "The directive should use '> [!IMPORTANT]' to render as a prominent callout."
    )
    # The callout line must start with '>' (blockquote prefix)
    for line in callout_lines:
        assert line.strip().startswith(">"), (
            f"[!IMPORTANT] marker is not inside a blockquote ('>') in line: {line!r}"
        )
    # Syntax must be exactly '> [!IMPORTANT]' (case matters for GFM)
    assert any(line.strip() == "> [!IMPORTANT]" for line in lines), (
        f"Expected '> [!IMPORTANT]' as an exact line; found callout lines: {callout_lines}. "
        "Check for typos or extra content on the [!IMPORTANT] line."
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
    The path reference must be '{{PROJECT_NAME}}/AGENT-RULES.md' — using a
    forward slash separator. A backslash or missing slash would produce an
    invalid path on POSIX systems.
    """
    content = _read_file()
    assert "{{PROJECT_NAME}}/AGENT-RULES.md" in content, (
        "Expected path '{{PROJECT_NAME}}/AGENT-RULES.md' (forward slash) not found.\n"
        "Check for backslash separators or missing slash in the directive."
    )
