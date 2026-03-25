"""Tester edge-case tests for DOC-004: Project Folder README.md placeholder.

These tests verify the *structural* requirements that the Developer's tests miss:
  - {{PROJECT_NAME}} must be on its own line (proper Markdown H1)
  - The README must NOT contain stray content from other sessions
  - The README must begin with the placeholder heading (first H1)
  - After placeholder replacement the heading must be standalone

All tests in this file are expected to FAIL under the current implementation
because the placeholder is embedded mid-line on line 27, not as a standalone H1.
"""

import pytest
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_README = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "README.md"
TEMPLATE_README = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "README.md"


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _content(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural: placeholder must be a standalone line (not embedded mid-line)
# ---------------------------------------------------------------------------


def test_default_readme_placeholder_is_standalone_line():
    """# {{PROJECT_NAME}} must appear as a complete standalone line, not embedded
    in the middle of another line such as a bullet-point or prose paragraph."""
    lines = _lines(DEFAULT_README)
    assert "# {{PROJECT_NAME}}" in lines, (
        "# {{PROJECT_NAME}} is not a standalone line in templates/coding/Project/README.md. "
        "It is currently embedded mid-line after German bullet-point text on line 27."
    )


def test_template_readme_placeholder_is_standalone_line():
    """# {{PROJECT_NAME}} must appear as a complete standalone line in the template."""
    lines = _lines(TEMPLATE_README)
    assert "# {{PROJECT_NAME}}" in lines, (
        "# {{PROJECT_NAME}} is not a standalone line in templates/coding/Project/README.md. "
        "It is currently embedded mid-line after German bullet-point text on line 27."
    )


# ---------------------------------------------------------------------------
# Structural: README must start with the placeholder heading
# ---------------------------------------------------------------------------


def test_default_readme_first_nonempty_line_is_placeholder():
    """The first non-empty line of the README must be '# {{PROJECT_NAME}}'.
    No stray content (e.g. from prior sessions) should precede the heading."""
    lines = _lines(DEFAULT_README)
    first_content_line = next((l for l in lines if l.strip()), None)
    assert first_content_line == "# {{PROJECT_NAME}}", (
        f"First non-empty line is {first_content_line!r}, expected '# {{{{PROJECT_NAME}}}}'."
    )


def test_template_readme_first_nonempty_line_is_placeholder():
    """The first non-empty line of the template README must be '# {{PROJECT_NAME}}'."""
    lines = _lines(TEMPLATE_README)
    first_content_line = next((l for l in lines if l.strip()), None)
    assert first_content_line == "# {{PROJECT_NAME}}", (
        f"First non-empty line is {first_content_line!r}, expected '# {{{{PROJECT_NAME}}}}'."
    )


# ---------------------------------------------------------------------------
# Structural: README must have exactly one H1 heading
# ---------------------------------------------------------------------------


def test_default_readme_has_exactly_one_h1():
    """The README must have exactly one H1 heading (the placeholder line).
    Multiple H1 headings indicate stray content — e.g., a German session
    heading '# Mathematik Demo (Streamlit)' should not be present."""
    h1_lines = [l for l in _lines(DEFAULT_README) if re.match(r"^# ", l)]
    assert len(h1_lines) == 1, (
        f"Expected exactly 1 H1 heading, found {len(h1_lines)}: {h1_lines!r}"
    )


def test_template_readme_has_exactly_one_h1():
    """The template README must have exactly one H1 heading."""
    h1_lines = [l for l in _lines(TEMPLATE_README) if re.match(r"^# ", l)]
    assert len(h1_lines) == 1, (
        f"Expected exactly 1 H1 heading, found {len(h1_lines)}: {h1_lines!r}"
    )


# ---------------------------------------------------------------------------
# Structural: README must not contain stray foreign content
# ---------------------------------------------------------------------------


def test_default_readme_no_german_content():
    """The README must not contain the German session content
    '# Mathematik Demo' which is present due to a prior session edit."""
    content = _content(DEFAULT_README)
    assert "Mathematik Demo" not in content, (
        "templates/coding README contains German session content 'Mathematik Demo' "
        "that does not belong in a project folder template."
    )


def test_template_readme_no_german_content():
    """The template README must not contain German session content."""
    content = _content(TEMPLATE_README)
    assert "Mathematik Demo" not in content, (
        "templates/coding README contains German session content 'Mathematik Demo' "
        "that does not belong in a project folder template."
    )


# ---------------------------------------------------------------------------
# Integration: after replacement, heading must be a standalone line
# ---------------------------------------------------------------------------


def test_replacement_produces_standalone_heading(tmp_path):
    """After replace_template_placeholders() runs, the project name should
    appear as '# <name>' on its own line — not embedded mid-line.
    This verifies the WP goal: 'the README dynamically shows the correct
    project name after placeholder replacement.'"""
    from launcher.core.project_creator import replace_template_placeholders

    readme = tmp_path / "README.md"
    readme.write_text(_content(DEFAULT_README), encoding="utf-8")

    replace_template_placeholders(tmp_path, "TestProject")

    result_lines = readme.read_text(encoding="utf-8").splitlines()
    assert "# TestProject" in result_lines, (
        "'# TestProject' is not a standalone line after placeholder replacement. "
        "The project name ended up mid-line rather than as a proper H1 heading."
    )


def test_replacement_removes_all_non_template_content(tmp_path):
    """After replacement, the resulting README should not contain the German
    content that precedes the placeholder in the current corrupted file."""
    from launcher.core.project_creator import replace_template_placeholders

    readme = tmp_path / "README.md"
    readme.write_text(_content(DEFAULT_README), encoding="utf-8")

    replace_template_placeholders(tmp_path, "TestProject")

    result = readme.read_text(encoding="utf-8")
    assert "Mathematik Demo" not in result, (
        "After replacement, the README still contains the German 'Mathematik Demo' "
        "content which should not be present in a project folder README."
    )
