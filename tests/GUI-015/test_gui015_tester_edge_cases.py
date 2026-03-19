"""Tester edge-case additions for GUI-015 — Rename Root Folder to TS-SAE-{ProjectName}.

Tests beyond the developer's baseline, covering:
  - Special characters in folder name (hyphen, underscore, dot, numeric)
  - Exact prefix verification ('TS-SAE-', uppercase, hyphen-separated)
  - Empty folder name creates 'TS-SAE-' only
  - Very long name (100 chars) still receives prefix
  - Unicode names (Latin extended, CJK)
  - Case preservation (no normalisation applied)
  - Two-level traversal boundary — absorbed by the TS-SAE- prefix component,
    so the result stays inside destination and no ValueError is raised
"""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.core.project_creator import create_project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_template(tmp_path: Path) -> Path:
    """Minimal template directory used by all edge-case tests."""
    template = tmp_path / "template"
    template.mkdir()
    (template / "README.md").write_text("template readme")
    return template


@pytest.fixture()
def tmp_dest(tmp_path: Path) -> Path:
    """Destination directory used by all edge-case tests."""
    dest = tmp_path / "dest"
    dest.mkdir()
    return dest


# ---------------------------------------------------------------------------
# Special characters in folder name
# ---------------------------------------------------------------------------

class TestSpecialCharactersInName:
    """Folder names with common valid filesystem characters preserve the prefix correctly."""

    def test_hyphen_in_name(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Hyphens in folder_name are preserved verbatim in the prefixed folder name."""
        result = create_project(tmp_template, tmp_dest, "My-Project")
        assert result.name == "TS-SAE-My-Project"
        assert result.is_dir()

    def test_underscore_in_name(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Underscores in folder_name are preserved verbatim in the prefixed folder name."""
        result = create_project(tmp_template, tmp_dest, "My_Project")
        assert result.name == "TS-SAE-My_Project"
        assert result.is_dir()

    def test_dot_in_name(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Dots embedded in folder_name are preserved (e.g. version strings like v1.0.0)."""
        result = create_project(tmp_template, tmp_dest, "v1.0.0")
        assert result.name == "TS-SAE-v1.0.0"
        assert result.is_dir()

    def test_digits_in_name(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Digit characters in folder_name receive the TS-SAE- prefix correctly."""
        result = create_project(tmp_template, tmp_dest, "Project2025")
        assert result.name == "TS-SAE-Project2025"
        assert result.is_dir()

    def test_prefix_is_exactly_ts_sae_uppercase_hyphen(
        self, tmp_template: Path, tmp_dest: Path
    ) -> None:
        """The hardcoded prefix must be exactly 'TS-SAE-' — uppercase, hyphen-separated.

        Variations such as 'ts-sae-', 'TS_SAE_', or 'TSSAE' are NOT acceptable.
        This test guards against accidental edits to the prefix constant.
        """
        result = create_project(tmp_template, tmp_dest, "CheckPrefix")
        assert result.name.startswith("TS-SAE-"), (
            f"Prefix must be exactly 'TS-SAE-' but got: {result.name!r}"
        )
        assert result.name == "TS-SAE-CheckPrefix"


# ---------------------------------------------------------------------------
# Empty folder name
# ---------------------------------------------------------------------------

class TestEmptyFolderName:
    def test_empty_name_creates_prefix_only_folder(
        self, tmp_template: Path, tmp_dest: Path
    ) -> None:
        """An empty folder_name creates a folder named 'TS-SAE-' (prefix only).

        This edge case is only reachable via direct API usage — the GUI rejects
        empty names through validate_folder_name().  The function must not raise;
        it should create the directory on disk.
        """
        result = create_project(tmp_template, tmp_dest, "")
        assert result.name == "TS-SAE-"
        assert result.is_dir()


# ---------------------------------------------------------------------------
# Very long folder name
# ---------------------------------------------------------------------------

class TestVeryLongFolderName:
    def test_100_char_name_receives_prefix(
        self, tmp_template: Path, tmp_dest: Path
    ) -> None:
        """A 100-character name is within OS path limits and must receive the prefix.

        With 'TS-SAE-' (7 chars) prepended the total folder name becomes 107 chars,
        well within the 255-char POSIX filename limit and leaves enough room under
        the Windows MAX_PATH (260) for a typical pytest tmp_path prefix.
        """
        long_name = "X" * 100
        result = create_project(tmp_template, tmp_dest, long_name)
        assert result.name == f"TS-SAE-{long_name}"
        assert result.is_dir()


# ---------------------------------------------------------------------------
# Unicode names
# ---------------------------------------------------------------------------

class TestUnicodeNames:
    def test_latin_extended_unicode(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Latin-extended Unicode (accented characters) in folder_name is supported."""
        result = create_project(tmp_template, tmp_dest, "Café")
        assert result.name == "TS-SAE-Café"
        assert result.is_dir()

    def test_cjk_unicode_name(self, tmp_template: Path, tmp_dest: Path) -> None:
        """CJK (Japanese) Unicode characters in folder_name are handled correctly.

        Modern Windows, macOS, and Linux filesystems all support Unicode file names.
        """
        result = create_project(tmp_template, tmp_dest, "プロジェクト")
        assert result.name == "TS-SAE-プロジェクト"
        assert result.is_dir()


# ---------------------------------------------------------------------------
# Case preservation
# ---------------------------------------------------------------------------

class TestCasePreservation:
    """The TS-SAE- prefix is always uppercase; the user-supplied name is never
    normalised — case is preserved exactly as provided by the caller."""

    def test_mixed_case_preserved(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Mixed-case folder_name is stored exactly as provided."""
        result = create_project(tmp_template, tmp_dest, "MixedCASEname")
        assert result.name == "TS-SAE-MixedCASEname"

    def test_all_lowercase_not_capitalised(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Fully lowercase folder_name is NOT capitalised by create_project."""
        result = create_project(tmp_template, tmp_dest, "alllowercase")
        assert result.name == "TS-SAE-alllowercase"

    def test_all_uppercase_preserved(self, tmp_template: Path, tmp_dest: Path) -> None:
        """Fully uppercase folder_name is NOT lowercased by create_project."""
        result = create_project(tmp_template, tmp_dest, "ALLUPPERCASE")
        assert result.name == "TS-SAE-ALLUPPERCASE"


# ---------------------------------------------------------------------------
# Path-traversal 2-level boundary (TS-SAE- absorb effect)
# ---------------------------------------------------------------------------

class TestTwoLevelTraversalBoundary:
    """The TS-SAE- prefix introduces one extra path component.

    When path normalization resolves the prefixed name the 'TS-SAE-..' component
    is treated as a literal directory name.  A subsequent '..' pops only that
    component, returning to destination.  Therefore a 2-level traversal attempt
    ('../../x') resolves to dest/x — still inside the destination — and does NOT
    trigger the ValueError guard.

    This is NOT a security regression:
      - validate_folder_name() blocks '/' and '\\' at the GUI boundary.
      - The create_project() guard is defense-in-depth for direct API usage.
      - 3-level traversal ('../../../x') still escapes and is still blocked.
    """

    def test_two_level_traversal_absorbed_stays_in_dest(
        self, tmp_template: Path, tmp_dest: Path
    ) -> None:
        """2-level traversal resolves to dest/ (inside destination) — no ValueError raised."""
        # Should NOT raise — the resolved path is inside destination.
        result = create_project(tmp_template, tmp_dest, "../../boundary")
        assert result.is_relative_to(tmp_dest.resolve()), (
            f"Expected result inside {tmp_dest}, got {result}"
        )
        assert result.is_dir()
