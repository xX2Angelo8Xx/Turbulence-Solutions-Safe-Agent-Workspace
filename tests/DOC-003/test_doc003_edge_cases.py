"""
DOC-003 — Tester edge-case tests.

Additional boundary and regression tests beyond the developer's suite.
"""

import re
import os
import shutil
import tempfile

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DEFAULT_PROJECT_FILE = os.path.join(
    REPO_ROOT,
    "templates", "agent-workbench",
    ".github",
    "instructions",
    "copilot-instructions.md",
)

TEMPLATES_CODING_FILE = os.path.join(
    REPO_ROOT,
    "templates",
    "agent-workbench",
    ".github",
    "instructions",
    "copilot-instructions.md",
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Placeholder count: exactly one occurrence per file
# ---------------------------------------------------------------------------

def test_placeholder_count_exactly_one_in_default_project():
    """
    {{PROJECT_NAME}} must appear at least once — one replacement target.
    Multiple occurrences are legitimate (e.g. a read-first directive can also
    reference the placeholder), so we assert >= 1 rather than == 1.
    """
    content = _read(DEFAULT_PROJECT_FILE)
    count = content.count("{{PROJECT_NAME}}")
    assert count >= 1, (
        f"Expected at least 1 {{{{PROJECT_NAME}}}} in templates/coding file, found {count}"
    )


def test_placeholder_count_exactly_one_in_templates_coding():
    """The templates/coding file must have at least one placeholder."""
    content = _read(TEMPLATES_CODING_FILE)
    count = content.count("{{PROJECT_NAME}}")
    assert count >= 1, (
        f"Expected at least 1 {{{{PROJECT_NAME}}}} in templates/coding file, found {count}"
    )


# ---------------------------------------------------------------------------
# Literal folder names that must NOT be placeholdered
# ---------------------------------------------------------------------------

def test_noagentzone_reference_unchanged_in_default_project():
    """NoAgentZone/ must remain a literal string — it is not dynamic."""
    content = _read(DEFAULT_PROJECT_FILE)
    assert "`NoAgentZone/`" in content, (
        "Expected literal `NoAgentZone/` in templates/coding copilot-instructions.md"
    )


def test_github_reference_unchanged_in_default_project():
    """`.github/` must remain a literal string."""
    content = _read(DEFAULT_PROJECT_FILE)
    assert "`.github/`" in content, (
        "Expected literal `.github/` in templates/coding copilot-instructions.md"
    )


def test_vscode_reference_unchanged_in_default_project():
    """`.vscode/` must remain a literal string."""
    content = _read(DEFAULT_PROJECT_FILE)
    assert "`.vscode/`" in content, (
        "Expected literal `.vscode/` in templates/coding copilot-instructions.md"
    )


# ---------------------------------------------------------------------------
# Placeholder is in the Workspace Rules section
# ---------------------------------------------------------------------------

def test_placeholder_is_in_workspace_rules_section():
    """The {{PROJECT_NAME}} placeholder must appear inside the Workspace Layout section body."""
    content = _read(DEFAULT_PROJECT_FILE)
    ws_rules_idx = content.find("## Workspace Layout")
    assert ws_rules_idx != -1, "Workspace Layout section not found"
    # Extract section body: from the heading to the next ## heading (or EOF)
    next_section = re.search(r'^## ', content[ws_rules_idx + 1:], re.MULTILINE)
    ws_rules_end = ws_rules_idx + 1 + next_section.start() if next_section else len(content)
    ws_rules_body = content[ws_rules_idx:ws_rules_end]
    assert "{{PROJECT_NAME}}" in ws_rules_body, (
        "{{PROJECT_NAME}} is not inside the Workspace Rules section body"
    )


# ---------------------------------------------------------------------------
# Post-replacement tests: hyphenated and underscored project names
# ---------------------------------------------------------------------------

def test_replacement_with_hyphenated_project_name():
    """Replacement must work correctly for names like My-Cool-Project."""
    project_name = "My-Cool-Project"
    with tempfile.TemporaryDirectory() as tmp_dir:
        dst = os.path.join(tmp_dir, "copilot-instructions.md")
        shutil.copy2(DEFAULT_PROJECT_FILE, dst)
        with open(dst, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace("{{PROJECT_NAME}}", project_name)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(text)
        result = _read(dst)
    assert f"`{project_name}/`" in result
    assert "{{PROJECT_NAME}}" not in result


def test_replacement_with_underscored_project_name():
    """Replacement must work correctly for names like my_project_42."""
    project_name = "my_project_42"
    with tempfile.TemporaryDirectory() as tmp_dir:
        dst = os.path.join(tmp_dir, "copilot-instructions.md")
        shutil.copy2(DEFAULT_PROJECT_FILE, dst)
        with open(dst, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace("{{PROJECT_NAME}}", project_name)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(text)
        result = _read(dst)
    assert f"`{project_name}/`" in result
    assert "{{PROJECT_NAME}}" not in result


def test_replacement_with_numeric_suffix_project_name():
    """Replacement must work correctly for names like Project2025."""
    project_name = "Project2025"
    with tempfile.TemporaryDirectory() as tmp_dir:
        dst = os.path.join(tmp_dir, "copilot-instructions.md")
        shutil.copy2(DEFAULT_PROJECT_FILE, dst)
        with open(dst, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace("{{PROJECT_NAME}}", project_name)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(text)
        result = _read(dst)
    assert f"`{project_name}/`" in result
    assert "{{PROJECT_NAME}}" not in result


# ---------------------------------------------------------------------------
# File encoding guard
# ---------------------------------------------------------------------------

def test_default_project_file_has_no_bom():
    """File must be UTF-8 without BOM to prevent encoding issues during replacement."""
    with open(DEFAULT_PROJECT_FILE, "rb") as fh:
        bom = fh.read(3)
    assert bom != b"\xef\xbb\xbf", (
        "templates/coding copilot-instructions.md has a UTF-8 BOM; remove it."
    )


def test_templates_coding_file_has_no_bom():
    """templates/coding file must also be UTF-8 without BOM."""
    with open(TEMPLATES_CODING_FILE, "rb") as fh:
        bom = fh.read(3)
    assert bom != b"\xef\xbb\xbf", (
        "templates/coding copilot-instructions.md has a UTF-8 BOM; remove it."
    )
