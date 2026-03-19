"""
FIX-012 Tester Edge-Case Tests

Additional tests beyond the Developer's suite. These verify that:
  - The build_dmg.sh surgical removal of --target-arch did NOT accidentally
    strip adjacent logic (skip guard, TARGET_ARCH DMG naming, uname fallback,
    set -euo pipefail).
  - A related but distinct flag (--target-arch-variant) is also absent.
  - The setup.iss surgical removal of ArchitecturesAllowed/ArchitecturesInstallMode
    did NOT accidentally remove adjacent directives (DefaultGroupName,
    DisableProgramGroupPage).
  - The architecture directives are absent even when searched case-insensitively
    (no mistaken mixed-case reintroduction).
  - Neither file was truncated or otherwise corrupted by the edit.
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"


def read_dmg() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


def read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# build_dmg.sh — collateral-damage guard (BUG-040 fix must be surgical)
# ---------------------------------------------------------------------------

class TestBuildDmgIntegrityAfterFix:
    def test_pyinstaller_skip_guard_present(self):
        """The 'if [ ! -d "${DIST_DIR}/launcher" ]' guard must still be present.

        This guard prevents a redundant PyInstaller run when a cached dist/
        already exists. The BUG-040 fix only removed --target-arch; it must not
        have deleted or damaged this surrounding conditional.
        """
        content = read_dmg()
        assert re.search(r'if\s+\[.*!.*-d.*\$\{?DIST_DIR\}?.*launcher.*\]', content), (
            "build_dmg.sh must still contain the 'if [ ! -d ${DIST_DIR}/launcher ]' "
            "skip guard — it was adjacent to the removed --target-arch line and must "
            "not have been accidentally removed"
        )

    def test_target_arch_used_in_dmg_filename(self):
        """TARGET_ARCH variable must still appear in the DMG filename construction.

        The fix removes --target-arch from the PyInstaller invocation only.
        The TARGET_ARCH variable is still needed to name the output DMG file
        (e.g. AgentEnvironmentLauncher-1.0.0-arm64.dmg).
        """
        content = read_dmg()
        assert re.search(r'DMG_FILENAME.*\$\{?TARGET_ARCH\}?', content), (
            "TARGET_ARCH must still appear in DMG_FILENAME — it drives the output "
            "filename convention. The BUG-040 fix must only remove the flag from "
            "the PyInstaller invocation, not the arch-aware naming logic."
        )

    def test_uname_m_fallback_present(self):
        """uname -m fallback for TARGET_ARCH must still be present.

        The architecture selection block sets TARGET_ARCH from the CLI argument
        or falls back to 'uname -m'. This fallback is what makes the script
        work on ARM runners without any argument.
        """
        content = read_dmg()
        assert "uname -m" in content, (
            "build_dmg.sh must still contain 'uname -m' as the fallback for "
            "TARGET_ARCH. This enables auto-detection on ARM runners without "
            "passing an explicit arch argument."
        )

    def test_set_euo_pipefail_exact_form(self):
        """'set -euo pipefail' must appear verbatim (error handling intact)."""
        content = read_dmg()
        assert "set -euo pipefail" in content, (
            "build_dmg.sh must use the exact 'set -euo pipefail' form. "
            "This ensures -e (exit on error), -u (unbound vars), and -o pipefail "
            "are all active — a surgical edit must not have removed this safety line."
        )

    def test_target_arch_variant_flag_also_absent(self):
        """--target-arch-variant must NOT appear in the PyInstaller invocation.

        This is a related but distinct PyInstaller makespec flag. If anyone
        mistakenly re-introduces it as a workaround for the removed --target-arch,
        it would cause the same CI failure.
        """
        content = read_dmg()
        assert "--target-arch-variant" not in content, (
            "--target-arch-variant must not be passed to PyInstaller — it is also "
            "a makespec-only option that fails when a .spec file is provided"
        )

    def test_build_dmg_file_not_truncated(self):
        """build_dmg.sh must be larger than a reasonable minimum size.

        A truncation during editing would silently lose the hdiutil/DMG creation
        logic. This check guards against accidentally saving a partial file.
        """
        size = BUILD_DMG.stat().st_size
        assert size > 2000, (
            f"build_dmg.sh is only {size} bytes — far smaller than expected. "
            "The file may have been truncated during the BUG-040 fix edit."
        )


# ---------------------------------------------------------------------------
# setup.iss — collateral-damage guard (BUG-041 fix must be surgical)
# ---------------------------------------------------------------------------

class TestSetupIssIntegrityAfterFix:
    def test_default_group_name_present(self):
        """DefaultGroupName must still be present in [Setup].

        This directive was adjacent to the removed ArchitecturesAllowed line.
        The BUG-041 fix must not have disturbed it.
        """
        content = read_iss()
        assert "DefaultGroupName=" in content, (
            "DefaultGroupName directive must still be present in [Setup] section. "
            "It was adjacent to the removed ArchitecturesAllowed line."
        )

    def test_disable_program_group_page_present(self):
        """DisableProgramGroupPage=yes must still be present.

        This directive is part of the standard [Setup] block. Verifying it
        confirms the ArchitecturesAllowed removal did not accidentally eat
        surrounding lines.
        """
        content = read_iss()
        assert re.search(r"^DisableProgramGroupPage=yes$", content, re.MULTILINE), (
            "DisableProgramGroupPage=yes must still be present in [Setup] — "
            "it suppresses the redundant 'Select Start Menu folder' wizard page."
        )

    def test_architectures_allowed_absent_case_insensitive(self):
        """ArchitecturesAllowed must be absent in any capitalisation variant.

        A developer re-introducing the directive with different casing
        (e.g. ArchitecturesAllowed or architecturesallowed) would still break
        the CI Inno Setup build.
        """
        content = read_iss()
        assert "architecturesallowed" not in content.lower(), (
            "ArchitecturesAllowed (any casing) must not appear in setup.iss"
        )

    def test_architectures_install_mode_absent_case_insensitive(self):
        """ArchitecturesInstallMode must be absent in any capitalisation variant."""
        content = read_iss()
        assert "architecturesinstallmode" not in content.lower(), (
            "ArchitecturesInstallMode (any casing) must not appear in setup.iss"
        )

    def test_setup_iss_file_not_truncated(self):
        """setup.iss must be larger than a reasonable minimum size.

        A truncation would silently remove sections like [Files], [Icons],
        or [Run]. This check guards against accidentally saving a partial file.
        """
        size = SETUP_ISS.stat().st_size
        assert size > 500, (
            f"setup.iss is only {size} bytes — far smaller than expected. "
            "The file may have been truncated during the BUG-041 fix edit."
        )

    def test_files_section_present(self):
        """[Files] section must still exist after the edit."""
        content = read_iss()
        assert "[Files]" in content, (
            "[Files] section must still be present in setup.iss — "
            "it defines what gets installed and must not have been removed by the edit."
        )

    def test_run_section_present(self):
        """[Run] section must still exist after the edit."""
        content = read_iss()
        assert "[Run]" in content, (
            "[Run] section must still be present in setup.iss — "
            "it configures the post-install launch option."
        )
