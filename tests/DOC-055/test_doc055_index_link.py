"""
Tests for DOC-055: Fix index.md Scripts Link.

Verifies that the display text for the scripts/README.md link in
docs/work-rules/index.md is correct and that the target file exists.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
INDEX_MD = REPO_ROOT / "docs" / "work-rules" / "index.md"


def _get_index_content() -> str:
    return INDEX_MD.read_text(encoding="utf-8")


def test_index_md_exists():
    """docs/work-rules/index.md must exist."""
    assert INDEX_MD.exists(), f"Missing file: {INDEX_MD}"


def test_scripts_link_display_text_is_correct():
    """Display text must be 'scripts/README.md', not '../scripts/README.md'."""
    content = _get_index_content()
    assert "[scripts/README.md]" in content, (
        "Expected display text 'scripts/README.md' not found in index.md"
    )


def test_scripts_link_display_text_is_not_wrong():
    """Old incorrect display text '../scripts/README.md' must not be present."""
    content = _get_index_content()
    assert "[../scripts/README.md]" not in content, (
        "Old incorrect display text '../scripts/README.md' still present in index.md"
    )


def test_scripts_link_href_is_correct():
    """The href target must be '../../scripts/README.md'."""
    content = _get_index_content()
    assert "(../../scripts/README.md)" in content, (
        "Expected href '../../scripts/README.md' not found in index.md"
    )


def test_scripts_link_full_markdown_form():
    """The complete markdown link must match the expected form."""
    content = _get_index_content()
    expected = "[scripts/README.md](../../scripts/README.md)"
    assert expected in content, (
        f"Expected full link '{expected}' not found in index.md"
    )


def test_target_file_exists():
    """The resolved target file scripts/README.md must exist at repo root."""
    target = REPO_ROOT / "scripts" / "README.md"
    assert target.exists(), (
        f"Link target does not exist: {target}"
    )
