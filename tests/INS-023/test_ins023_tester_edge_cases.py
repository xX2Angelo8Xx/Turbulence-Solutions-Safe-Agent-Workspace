"""Tester edge-case tests for INS-023 — skip README files during project creation.

Additional edge cases beyond those written by the Developer:

1. Deeply nested README.md (3+ directory levels) must be removed.
2. README.md inside .github/ must also be removed when include_readmes=False.
3. Files named README-DEV.md, README.rst, etc. must NOT be removed (exact match).
4. Read-only README.md must not crash project creation (PermissionError test).
5. Symlink pointing to README.md — unlink removes the symlink itself (not target).
6. Capitalisation variant Readme.md — on case-sensitive filesystems it must survive.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from launcher.core.project_creator import create_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_template(tmp_path: Path, with_readme: bool = True) -> Path:
    """Return a minimal template that satisfies create_project's requirements."""
    tpl = tmp_path / "template"
    tpl.mkdir()
    if with_readme:
        (tpl / "README.md").write_text("# Root README", encoding="utf-8")
    # Required by create_project (write_counter_config needs the scripts dir)
    hooks_dir = tpl / ".github" / "hooks" / "scripts"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return tpl


def _create(tpl: Path, dest: Path, name: str = "EdgeTest", include_readmes: bool = False) -> Path:
    dest.mkdir(exist_ok=True)
    return create_project(
        template_path=tpl,
        destination=dest,
        folder_name=name,
        include_readmes=include_readmes,
    )


# ---------------------------------------------------------------------------
# 1. Deeply nested README in subdirs
# ---------------------------------------------------------------------------

class TestDeeplyNestedReadme:
    def test_readme_three_levels_deep_is_removed(self, tmp_path: Path) -> None:
        """A README.md buried three directory levels deep must be deleted."""
        tpl = _minimal_template(tmp_path)

        deep = tpl / "level1" / "level2" / "level3"
        deep.mkdir(parents=True)
        (deep / "README.md").write_text("deep readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        remaining = list(created.rglob("README.md"))
        assert remaining == [], f"Deep-nested README.md not removed: {remaining}"

    def test_readme_four_levels_deep_is_removed(self, tmp_path: Path) -> None:
        """A README.md four directory levels deep must be deleted."""
        tpl = _minimal_template(tmp_path)

        deep = tpl / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "README.md").write_text("very deep readme", encoding="utf-8")

        # Add a second README at a shallower level too
        (tpl / "a" / "README.md").write_text("shallow readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        remaining = list(created.rglob("README.md"))
        assert remaining == [], f"Multi-level README.md files not all removed: {remaining}"

    def test_non_readme_files_in_deep_dirs_survive(self, tmp_path: Path) -> None:
        """Other .md files alongside a deep README.md must not be deleted."""
        tpl = _minimal_template(tmp_path)

        deep = tpl / "docs" / "internal"
        deep.mkdir(parents=True)
        (deep / "README.md").write_text("readme", encoding="utf-8")
        (deep / "GUIDE.md").write_text("guide content", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert not list(created.rglob("README.md")), "README.md was not removed"
        guide_files = list(created.rglob("GUIDE.md"))
        assert len(guide_files) == 1, "GUIDE.md was incorrectly removed"


# ---------------------------------------------------------------------------
# 2. README inside .github/
# ---------------------------------------------------------------------------

class TestReadmeInGithubDir:
    def test_readme_in_github_root_removed(self, tmp_path: Path) -> None:
        """README.md directly inside .github/ must be removed."""
        tpl = _minimal_template(tmp_path)

        github_dir = tpl / ".github"
        (github_dir / "README.md").write_text("github readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        github_readmes = list((created / ".github").rglob("README.md"))
        assert github_readmes == [], f".github/README.md was not removed: {github_readmes}"

    def test_copilot_instructions_survive_after_github_readme_removed(
        self, tmp_path: Path
    ) -> None:
        """copilot-instructions.md in .github/instructions must survive."""
        tpl = _minimal_template(tmp_path)

        instructions_dir = tpl / ".github" / "instructions"
        instructions_dir.mkdir(parents=True, exist_ok=True)
        (instructions_dir / "copilot-instructions.md").write_text(
            "# Copilot", encoding="utf-8"
        )
        (tpl / ".github" / "README.md").write_text("readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        copilot_files = list(created.rglob("copilot-instructions.md"))
        assert len(copilot_files) >= 1, "copilot-instructions.md was incorrectly removed"


# ---------------------------------------------------------------------------
# 3. Exact name match — README variants must NOT be deleted
# ---------------------------------------------------------------------------

class TestExactNameMatchOnly:
    def test_readme_dev_md_survives(self, tmp_path: Path) -> None:
        """README-DEV.md must NOT be deleted (only exact 'README.md' matches)."""
        tpl = _minimal_template(tmp_path)
        (tpl / "README-DEV.md").write_text("dev readme variant", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert (created / "README-DEV.md").exists(), "README-DEV.md was incorrectly deleted"
        assert not (created / "README.md").exists(), "README.md must still be removed"

    def test_readme_rst_survives(self, tmp_path: Path) -> None:
        """README.rst must NOT be deleted."""
        tpl = _minimal_template(tmp_path)
        (tpl / "README.rst").write_text("RST readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert (created / "README.rst").exists(), "README.rst was incorrectly deleted"

    def test_readme_txt_survives(self, tmp_path: Path) -> None:
        """README.txt must NOT be deleted."""
        tpl = _minimal_template(tmp_path)
        (tpl / "README.txt").write_text("TXT readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert (created / "README.txt").exists(), "README.txt was incorrectly deleted"

    def test_myreadme_md_survives(self, tmp_path: Path) -> None:
        """A file named MyREADME.md must NOT be deleted."""
        tpl = _minimal_template(tmp_path)
        (tpl / "MyREADME.md").write_text("my readme", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert (created / "MyREADME.md").exists(), "MyREADME.md was incorrectly deleted"


# ---------------------------------------------------------------------------
# 4. Read-only README.md — must not raise an unhandled PermissionError
# ---------------------------------------------------------------------------

class TestReadonlyReadme:
    def test_readonly_readme_does_not_crash_project_creation(
        self, tmp_path: Path
    ) -> None:
        """If a README.md is read-only, project creation must not raise PermissionError.

        The implementation currently only catches FileNotFoundError.  A read-only
        file causes os.unlink to raise PermissionError on Windows, which propagates
        uncaught and crashes the entire create_project() call.

        Expected: either the README is removed (preferred) or the error is swallowed
        gracefully — in no case should PermissionError propagate to the caller.
        """
        tpl = _minimal_template(tmp_path)

        # Make the copied README read-only AFTER template setup
        readme_in_tpl = tpl / "README.md"
        readme_in_tpl.chmod(stat.S_IREAD)  # remove write permission

        dest = tmp_path / "dest"

        try:
            created = _create(tpl, dest)
            # If we get here, no exception was raised — ideal outcome
            # The README.md should be gone or (if skipped) it may still exist
        except PermissionError as exc:
            # Restore permission so pytest cleanup works
            readme_in_dest = dest / "TS-SAE-EdgeTest" / "README.md"
            if readme_in_dest.exists():
                readme_in_dest.chmod(stat.S_IREAD | stat.S_IWRITE)
            pytest.fail(
                f"PermissionError raised when deleting read-only README.md — "
                f"the implementation must also catch PermissionError (or OSError). "
                f"Details: {exc}"
            )
        finally:
            # Always restore write permission for pytest cleanup
            readme_in_tpl.chmod(stat.S_IREAD | stat.S_IWRITE)
            readme_in_dest = dest / "TS-SAE-EdgeTest" / "README.md"
            if readme_in_dest.exists():
                readme_in_dest.chmod(stat.S_IREAD | stat.S_IWRITE)


# ---------------------------------------------------------------------------
# 5. Symlink pointing to README.md or named README.md
# ---------------------------------------------------------------------------

class TestSymlinkReadme:
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Symlink creation requires admin / developer mode on Windows — "
               "skipped in standard CI.",
    )
    def test_symlink_readme_removed(self, tmp_path: Path) -> None:
        """A symlink named README.md must be removed (unlinks symlink, not target)."""
        tpl = _minimal_template(tmp_path, with_readme=False)

        # Real file that the symlink points to
        real_file = tpl / "REAL_CONTENT.md"
        real_file.write_text("real content", encoding="utf-8")

        # Symlink named README.md -> REAL_CONTENT.md
        try:
            (tpl / "README.md").symlink_to(real_file)
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks on this platform/configuration")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        # The symlink README.md should be gone
        readme_link = created / "README.md"
        assert not readme_link.exists() and not readme_link.is_symlink(), (
            "Symlink named README.md was not removed"
        )

        # The real file must still exist (unlink only removes the symlink)
        assert (created / "REAL_CONTENT.md").exists(), (
            "REAL_CONTENT.md (symlink target) was incorrectly removed"
        )

    def test_symlink_readme_windows_skipped_gracefully(
        self, tmp_path: Path
    ) -> None:
        """On Windows, symlink tests are skipped — verify plain README.md still works."""
        if sys.platform != "win32":
            pytest.skip("Windows-specific path only")

        tpl = _minimal_template(tmp_path)
        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        remaining = list(created.rglob("README.md"))
        assert remaining == [], "Regular README.md not removed on Windows"


# ---------------------------------------------------------------------------
# 6. Capitalisation variant: Readme.md (on case-sensitive FS)
# ---------------------------------------------------------------------------

class TestCaseSensitivity:
    def test_readme_md_exact_case_deleted(self, tmp_path: Path) -> None:
        """Only a file named exactly 'README.md' is targeted for deletion."""
        tpl = _minimal_template(tmp_path)

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        # The exact-case README.md must be gone
        assert not (created / "README.md").exists(), (
            "README.md was not deleted when include_readmes=False"
        )

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows has a case-insensitive filesystem; Readme.md and README.md "
               "are the same file, so this test is only meaningful on Linux/macOS.",
    )
    def test_readme_lowercase_variant_survives_on_case_sensitive_fs(
        self, tmp_path: Path
    ) -> None:
        """On case-sensitive filesystems, 'Readme.md' must NOT be deleted."""
        tpl = _minimal_template(tmp_path, with_readme=False)

        # Create the lowercase variant — NOT the exact match
        (tpl / "Readme.md").write_text("not a match", encoding="utf-8")

        dest = tmp_path / "dest"
        created = _create(tpl, dest)

        assert (created / "Readme.md").exists(), (
            "Readme.md was incorrectly deleted (only 'README.md' should be targeted)"
        )
