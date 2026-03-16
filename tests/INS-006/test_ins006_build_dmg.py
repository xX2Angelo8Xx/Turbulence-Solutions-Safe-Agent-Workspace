"""Tests for INS-006: macOS Installer (build_dmg.sh)

All tests parse the shell script as plain text — no execution is required.
This means the tests run on Windows, macOS, and Linux without any
platform-specific tooling (hdiutil, bash, etc.).
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"


def read_script() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


class TestFileExists:
    def test_file_exists(self):
        assert BUILD_DMG.exists(), f"build_dmg.sh not found at {BUILD_DMG}"

    def test_file_is_non_empty(self):
        assert BUILD_DMG.stat().st_size > 0, "build_dmg.sh must not be empty"


# ---------------------------------------------------------------------------
# Shebang and shell safety
# ---------------------------------------------------------------------------


class TestShebangAndSafety:
    def test_shebang_line(self):
        content = read_script()
        first_line = content.splitlines()[0]
        assert first_line == "#!/usr/bin/env bash", (
            f"Expected shebang '#!/usr/bin/env bash', got: {first_line!r}"
        )

    def test_set_pipefail(self):
        content = read_script()
        # Accept any combination of -e, -u, -o pipefail on one or more lines
        has_pipefail = "pipefail" in content
        has_sete = re.search(r"set\s+-[a-z]*e[a-z]*", content) is not None
        assert has_pipefail and has_sete, (
            "Script must use 'set -euo pipefail' (or equivalent) for safe error handling"
        )


# ---------------------------------------------------------------------------
# hdiutil usage
# ---------------------------------------------------------------------------


class TestHdiutil:
    def test_references_hdiutil(self):
        content = read_script()
        assert "hdiutil" in content, "Script must reference the hdiutil command"

    def test_hdiutil_create_subcommand(self):
        content = read_script()
        assert "hdiutil create" in content, (
            "Script must call 'hdiutil create' to produce the DMG"
        )

    def test_hdiutil_compressed_format(self):
        content = read_script()
        assert "UDZO" in content, (
            "hdiutil should use -format UDZO (compressed DMG)"
        )

    def test_hdiutil_volname(self):
        content = read_script()
        assert "-volname" in content, "hdiutil create should set -volname"


# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------


class TestAppMetadata:
    def test_app_name(self):
        content = read_script()
        assert "Agent Environment Launcher" in content, (
            "Script must reference the canonical app name 'Agent Environment Launcher'"
        )

    def test_app_version(self):
        content = read_script()
        assert "1.0.2" in content, "Script must embed version 1.0.2"

    def test_publisher(self):
        content = read_script()
        assert "Turbulence Solutions" in content, (
            "Script must reference publisher 'Turbulence Solutions'"
        )


# ---------------------------------------------------------------------------
# Architecture support
# ---------------------------------------------------------------------------


class TestArchitectureSupport:
    def test_intel_arch_referenced(self):
        content = read_script()
        assert "x86_64" in content, (
            "Script must explicitly reference the Intel architecture x86_64"
        )

    def test_arm_arch_referenced(self):
        content = read_script()
        assert "arm64" in content, (
            "Script must explicitly reference the ARM architecture arm64"
        )

    def test_target_arch_not_passed_to_pyinstaller(self):
        """--target-arch must NOT be passed — not allowed when a .spec file is given (BUG-040)."""
        content = read_script()
        assert "--target-arch" not in content, (
            "--target-arch must not be passed to PyInstaller when using a .spec file (BUG-040)"
        )


# ---------------------------------------------------------------------------
# Security: no hardcoded absolute paths
# ---------------------------------------------------------------------------


class TestNoHardcodedPaths:
    def test_no_users_path(self):
        content = read_script()
        # Allow /usr/ (system binaries) but not /Users/ (macOS home directories)
        assert "/Users/" not in content, (
            "Script must not hardcode paths under /Users/"
        )

    def test_no_home_path(self):
        content = read_script()
        assert "/home/" not in content, (
            "Script must not hardcode paths under /home/"
        )

    def test_no_absolute_dist_path(self):
        content = read_script()
        # dist/ should be referenced as a relative path, not an absolute one
        assert not re.search(r'["\']?/[a-zA-Z].*?/dist["\']?', content), (
            "dist/ directory must be referenced as a relative path, not an absolute one"
        )


# ---------------------------------------------------------------------------
# .app bundle structure
# ---------------------------------------------------------------------------


class TestAppBundleStructure:
    def test_contents_macos_created(self):
        content = read_script()
        assert "Contents/MacOS" in content, (
            "Script must create the Contents/MacOS directory inside the .app bundle"
        )

    def test_contents_resources_created(self):
        content = read_script()
        assert "Contents/Resources" in content, (
            "Script must create the Contents/Resources directory inside the .app bundle"
        )

    def test_info_plist_written(self):
        content = read_script()
        assert "Info.plist" in content, (
            "Script must write an Info.plist into the .app bundle"
        )


# ---------------------------------------------------------------------------
# Info.plist keys
# ---------------------------------------------------------------------------


class TestInfoPlistKeys:
    @pytest.mark.parametrize("key", [
        "CFBundleName",
        "CFBundleDisplayName",
        "CFBundleIdentifier",
        "CFBundleVersion",
        "CFBundleShortVersionString",
        "CFBundleExecutable",
        "CFBundlePackageType",
        "NSHighResolutionCapable",
        "LSMinimumSystemVersion",
        "NSHumanReadableCopyright",
    ])
    def test_plist_key_present(self, key: str):
        content = read_script()
        assert key in content, f"Info.plist must include key: {key}"


# ---------------------------------------------------------------------------
# PyInstaller integration
# ---------------------------------------------------------------------------


class TestPyInstallerIntegration:
    def test_references_launcher_spec(self):
        content = read_script()
        assert "launcher.spec" in content, (
            "Script must reference launcher.spec for the PyInstaller build"
        )

    def test_references_dist_launcher_output(self):
        content = read_script()
        assert "dist/launcher" in content or r"dist\launcher" in content, (
            "Script must reference the PyInstaller --onedir output directory dist/launcher"
        )
