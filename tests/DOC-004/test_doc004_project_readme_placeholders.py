"""Tests for DOC-004: Project Folder README.md placeholder usage.

Verifies that both Default-Project/Project/README.md and
templates/coding/Project/README.md:
  - Contain the {{PROJECT_NAME}} placeholder in the H1 heading
  - Do NOT contain a hardcoded '# Project' heading
  - Behave correctly when processed by replace_template_placeholders()
  - Both files are identical in content
"""

import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_README = REPO_ROOT / "Default-Project" / "Project" / "README.md"
TEMPLATE_README = REPO_ROOT / "templates" / "coding" / "Project" / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Static content tests — Default-Project/Project/README.md
# ---------------------------------------------------------------------------


def test_default_readme_exists():
    """Default-Project/Project/README.md must exist."""
    assert DEFAULT_README.exists(), f"Missing: {DEFAULT_README}"


def test_default_readme_contains_project_name_placeholder():
    """Default-Project README must contain {{PROJECT_NAME}} placeholder."""
    content = _read(DEFAULT_README)
    assert "{{PROJECT_NAME}}" in content


def test_default_readme_h1_uses_placeholder():
    """Default-Project README H1 heading must use {{PROJECT_NAME}}."""
    content = _read(DEFAULT_README)
    assert "# {{PROJECT_NAME}}" in content


def test_default_readme_no_hardcoded_project_heading():
    """Default-Project README must not have a bare '# Project' H1 heading."""
    content = _read(DEFAULT_README)
    # Allow '# Project' only if followed by a non-space char (e.g., '#Name'),
    # but a standalone '# Project' on its own line is forbidden.
    lines = content.splitlines()
    assert "# Project" not in lines, (
        "Found hardcoded '# Project' heading — must be '# {{PROJECT_NAME}}'"
    )


# ---------------------------------------------------------------------------
# Static content tests — templates/coding/Project/README.md
# ---------------------------------------------------------------------------


def test_template_readme_exists():
    """templates/coding/Project/README.md must exist."""
    assert TEMPLATE_README.exists(), f"Missing: {TEMPLATE_README}"


def test_template_readme_contains_project_name_placeholder():
    """Template README must contain {{PROJECT_NAME}} placeholder."""
    content = _read(TEMPLATE_README)
    assert "{{PROJECT_NAME}}" in content


def test_template_readme_h1_uses_placeholder():
    """Template README H1 heading must use {{PROJECT_NAME}}."""
    content = _read(TEMPLATE_README)
    assert "# {{PROJECT_NAME}}" in content


def test_template_readme_no_hardcoded_project_heading():
    """Template README must not have a bare '# Project' H1 heading."""
    content = _read(TEMPLATE_README)
    lines = content.splitlines()
    assert "# Project" not in lines, (
        "Found hardcoded '# Project' heading — must be '# {{PROJECT_NAME}}'"
    )


# ---------------------------------------------------------------------------
# Parity test — both files must be identical
# ---------------------------------------------------------------------------


def test_both_readmes_are_identical():
    """Default-Project and templates/coding README must have identical content."""
    assert _read(DEFAULT_README) == _read(TEMPLATE_README), (
        "Default-Project/Project/README.md and templates/coding/Project/README.md differ"
    )


# ---------------------------------------------------------------------------
# Integration tests — replace_template_placeholders()
# ---------------------------------------------------------------------------


def test_replace_placeholder_substitutes_project_name(tmp_path):
    """replace_template_placeholders() replaces {{PROJECT_NAME}} in a copy of README."""
    from launcher.core.project_creator import replace_template_placeholders

    readme = tmp_path / "README.md"
    readme.write_text(_read(DEFAULT_README), encoding="utf-8")

    replace_template_placeholders(tmp_path, "MyProject")

    result = readme.read_text(encoding="utf-8")
    assert "MyProject" in result
    assert "{{PROJECT_NAME}}" not in result


def test_replace_placeholder_produces_correct_heading(tmp_path):
    """After replacement, README heading becomes '# <project_name>'."""
    from launcher.core.project_creator import replace_template_placeholders

    readme = tmp_path / "README.md"
    readme.write_text(_read(DEFAULT_README), encoding="utf-8")

    replace_template_placeholders(tmp_path, "Falcon")

    result = readme.read_text(encoding="utf-8")
    assert "# Falcon" in result


def test_replace_placeholder_works_with_hyphenated_name(tmp_path):
    """Placeholder replacement works with a hyphenated project name."""
    from launcher.core.project_creator import replace_template_placeholders

    readme = tmp_path / "README.md"
    readme.write_text(_read(TEMPLATE_README), encoding="utf-8")

    replace_template_placeholders(tmp_path, "My-Awesome-Project")

    result = readme.read_text(encoding="utf-8")
    assert "# My-Awesome-Project" in result
    assert "{{PROJECT_NAME}}" not in result


def test_replace_placeholder_idempotent_after_no_placeholder(tmp_path):
    """replace_template_placeholders() on a file without placeholders does not change it."""
    from launcher.core.project_creator import replace_template_placeholders

    content = "# Static Heading\n\nNo placeholders here.\n"
    readme = tmp_path / "README.md"
    readme.write_text(content, encoding="utf-8")

    replace_template_placeholders(tmp_path, "AnyName")

    assert readme.read_text(encoding="utf-8") == content
