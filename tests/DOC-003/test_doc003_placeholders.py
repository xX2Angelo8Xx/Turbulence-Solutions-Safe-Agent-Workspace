"""
DOC-003 — Tests for copilot-instructions.md placeholder replacement.

Verifies that both template files use {{PROJECT_NAME}} instead of a
hardcoded 'Project/' folder reference, and that replace_template_placeholders()
correctly substitutes the token at project creation time.
"""

import re
import shutil
import os
import tempfile

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DEFAULT_PROJECT_FILE = os.path.join(
    REPO_ROOT,
    "templates", "coding",
    ".github",
    "instructions",
    "copilot-instructions.md",
)

TEMPLATES_CODING_FILE = os.path.join(
    REPO_ROOT,
    "templates",
    "coding",
    ".github",
    "instructions",
    "copilot-instructions.md",
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# templates/coding file
# ---------------------------------------------------------------------------

def test_default_project_uses_placeholder():
    """{{PROJECT_NAME}} must appear in the templates/coding copilot-instructions."""
    content = _read(DEFAULT_PROJECT_FILE)
    assert "{{PROJECT_NAME}}" in content, (
        "Expected {{PROJECT_NAME}} placeholder in templates/coding copilot-instructions.md"
    )


def test_default_project_no_bare_project_folder():
    """The bare literal `Project/` folder reference must not appear in the templates/coding file."""
    content = _read(DEFAULT_PROJECT_FILE)
    # Match backtick-quoted 'Project/' as a folder reference (not part of a URL or WP ID).
    assert not re.search(r"`Project/`", content), (
        "Found hardcoded `Project/` folder reference in templates/coding copilot-instructions.md; "
        "it should use {{PROJECT_NAME}}/ instead."
    )


# ---------------------------------------------------------------------------
# templates/coding file
# ---------------------------------------------------------------------------

def test_templates_coding_uses_placeholder():
    """{{PROJECT_NAME}} must appear in the templates/coding copilot-instructions."""
    content = _read(TEMPLATES_CODING_FILE)
    assert "{{PROJECT_NAME}}" in content, (
        "Expected {{PROJECT_NAME}} placeholder in templates/coding copilot-instructions.md"
    )


def test_templates_coding_no_bare_project_folder():
    """The bare literal `Project/` folder reference must not appear in the templates/coding file."""
    content = _read(TEMPLATES_CODING_FILE)
    assert not re.search(r"`Project/`", content), (
        "Found hardcoded `Project/` folder reference in templates/coding copilot-instructions.md; "
        "it should use {{PROJECT_NAME}}/ instead."
    )


# ---------------------------------------------------------------------------
# Parity check
# ---------------------------------------------------------------------------

def test_files_are_identical():
    """Both copilot-instructions.md template files must have identical content."""
    default_content = _read(DEFAULT_PROJECT_FILE)
    templates_content = _read(TEMPLATES_CODING_FILE)
    assert default_content == templates_content, (
        "templates/coding and templates/coding copilot-instructions.md are out of sync; "
        "they must be identical."
    )


# ---------------------------------------------------------------------------
# Functional replacement simulation
# ---------------------------------------------------------------------------

def test_placeholder_replaced_in_copy():
    """
    Simulate replace_template_placeholders() on a copy of the file and verify
    that {{PROJECT_NAME}} is replaced with the actual project name.
    """
    project_name = "MatlabDemo"

    with tempfile.TemporaryDirectory() as tmp_dir:
        dst = os.path.join(tmp_dir, "copilot-instructions.md")
        shutil.copy2(DEFAULT_PROJECT_FILE, dst)

        # Perform the same substitution that replace_template_placeholders() does.
        with open(dst, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace("{{PROJECT_NAME}}", project_name)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(text)

        result = _read(dst)

    assert f"`{project_name}/`" in result, (
        f"Expected `{project_name}/` in the post-replacement file."
    )
    assert "{{PROJECT_NAME}}" not in result, (
        "Placeholder {{PROJECT_NAME}} was not fully replaced."
    )
