"""Tests for INS-007: Linux Installer (build_appimage.sh)

All tests parse the shell script as plain text — no execution is required.
This means the tests run on Windows, macOS, and Linux without any
platform-specific tooling (appimagetool, bash, etc.).
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"


def read_script() -> str:
    return BUILD_APPIMAGE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


class TestFileExists:
    def test_file_exists(self):
        assert BUILD_APPIMAGE.exists(), (
            f"build_appimage.sh not found at {BUILD_APPIMAGE}"
        )

    def test_file_is_non_empty(self):
        assert BUILD_APPIMAGE.stat().st_size > 0, (
            "build_appimage.sh must not be empty"
        )


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
        has_pipefail = "pipefail" in content
        has_sete = re.search(r"set\s+-[a-z]*e[a-z]*", content) is not None
        assert has_pipefail and has_sete, (
            "Script must use 'set -euo pipefail' (or equivalent) for safe error handling"
        )


# ---------------------------------------------------------------------------
# Architecture support
# ---------------------------------------------------------------------------


class TestArchitectureSupport:
    def test_x86_64_arch_referenced(self):
        content = read_script()
        assert "x86_64" in content, (
            "Script must explicitly reference the x86_64 architecture"
        )

    def test_aarch64_arch_referenced(self):
        content = read_script()
        assert "aarch64" in content, (
            "Script must explicitly reference the aarch64 architecture"
        )

    def test_uname_m_fallback(self):
        content = read_script()
        assert "uname -m" in content, (
            "Script must use 'uname -m' as fallback for architecture auto-detection"
        )


# ---------------------------------------------------------------------------
# AppDir structure
# ---------------------------------------------------------------------------


class TestAppDirStructure:
    def test_appdir_usr_bin_created(self):
        content = read_script()
        assert "AppDir/usr/bin" in content, (
            "Script must create AppDir/usr/bin/ to hold the PyInstaller output"
        )

    def test_appdir_usr_share_applications_created(self):
        content = read_script()
        assert "usr/share/applications" in content, (
            "Script must create AppDir/usr/share/applications/ for the .desktop file"
        )

    def test_apprun_created(self):
        content = read_script()
        assert "AppRun" in content, (
            "Script must create the AppRun entry point as required by the AppImage spec"
        )

    def test_apprun_made_executable(self):
        content = read_script()
        # chmod +x must be applied to AppRun
        assert re.search(r'chmod\s+\+x.*AppRun', content), (
            "Script must make AppRun executable with 'chmod +x'"
        )


# ---------------------------------------------------------------------------
# .desktop file
# ---------------------------------------------------------------------------


class TestDesktopFile:
    def test_desktop_file_created_in_applications(self):
        content = read_script()
        assert "usr/share/applications" in content and ".desktop" in content, (
            "Script must write a .desktop file inside usr/share/applications/"
        )

    def test_desktop_file_copied_to_appdir_root(self):
        content = read_script()
        # A copy operation moves the .desktop to AppDir root
        # Script uses ${APPDIR} variable (expands to dist/AppDir)
        lines = content.splitlines()
        cp_desktop_lines = [
            line for line in lines
            if "cp" in line and ".desktop" in line and ("APPDIR" in line or "AppDir" in line)
        ]
        assert len(cp_desktop_lines) >= 1, (
            "Script must copy the .desktop file to the AppDir root "
            "(required by AppImage spec)"
        )

    def test_desktop_entry_name(self):
        content = read_script()
        assert "Name=" in content, (
            "The .desktop file must contain a Name= field"
        )

    def test_desktop_entry_exec(self):
        content = read_script()
        assert "Exec=launcher" in content, (
            "The .desktop Exec field must reference the 'launcher' binary"
        )

    def test_desktop_entry_type(self):
        content = read_script()
        assert "Type=Application" in content, (
            "The .desktop file must set Type=Application"
        )


# ---------------------------------------------------------------------------
# Icon file
# ---------------------------------------------------------------------------


class TestIconFile:
    def test_icon_at_appdir_root(self):
        content = read_script()
        # Icon file must be placed directly inside AppDir/
        assert ".svg" in content or ".png" in content, (
            "Script must place an icon file at the AppDir root "
            "(AppImage spec requirement)"
        )

    def test_icon_uses_brand_colors(self):
        content = read_script()
        # Company primary colours from config.py
        assert "#0A1D4E" in content, (
            "The placeholder icon SVG must use the company primary colour #0A1D4E"
        )
        assert "#5BC5F2" in content, (
            "The placeholder icon SVG must use the company secondary colour #5BC5F2"
        )

    def test_icon_in_hicolor_dir(self):
        content = read_script()
        assert "hicolor" in content, (
            "Icon must also be placed in the hicolor icon theme directory "
            "for desktop integration"
        )


# ---------------------------------------------------------------------------
# AppRun content
# ---------------------------------------------------------------------------


class TestAppRunContent:
    def test_apprun_uses_readlink(self):
        content = read_script()
        assert "readlink -f" in content, (
            "AppRun must use 'readlink -f' to resolve its own install location "
            "for relocatability"
        )

    def test_apprun_execs_launcher(self):
        content = read_script()
        # exec pattern — must call the launcher binary
        assert re.search(r'exec.*launcher', content), (
            "AppRun must use 'exec' to hand control to the launcher binary"
        )


# ---------------------------------------------------------------------------
# appimagetool
# ---------------------------------------------------------------------------


class TestAppImageTool:
    def test_references_appimagetool(self):
        content = read_script()
        assert "appimagetool" in content, (
            "Script must reference the appimagetool command to produce the AppImage"
        )

    def test_appimagetool_download_uses_https(self):
        content = read_script()
        # Check download URLs only on lines containing curl (the download command)
        # SVG xmlns namespaces (http://www.w3.org/...) are not download URLs
        curl_lines = [line for line in content.splitlines() if "curl" in line]
        assert len(curl_lines) > 0, "Script must contain curl download command"
        for line in curl_lines:
            urls = re.findall(r'https?://\S+', line)
            for url in urls:
                assert url.startswith("https://"), (
                    f"All curl download URLs must use HTTPS; found: {url!r}"
                )

    def test_appimagetool_download_no_plain_http(self):
        content = read_script()
        # No bare http:// URLs in download commands (curl/wget lines)
        # SVG xmlns namespaces (http://www.w3.org/...) are not download URLs
        download_lines = [
            line for line in content.splitlines()
            if re.search(r'\bcurl\b|\bwget\b', line)
        ]
        for line in download_lines:
            assert not re.search(r'\bhttp://(?!www\.w3\.org)', line), (
                f"Download commands must not use plain HTTP; found in: {line!r}"
            )

    def test_appimagetool_download_uses_curl(self):
        content = read_script()
        assert "curl" in content, (
            "Script must use 'curl' to download appimagetool"
        )

    def test_download_uses_tlsv12(self):
        content = read_script()
        assert "--tlsv1.2" in content, (
            "curl download must enforce TLS 1.2 minimum via '--tlsv1.2'"
        )


# ---------------------------------------------------------------------------
# AppImage output
# ---------------------------------------------------------------------------


class TestAppImageOutput:
    def test_appimage_filename_contains_appbundlename(self):
        content = read_script()
        assert "TurbulenceSolutionsLauncher" in content, (
            "The output .AppImage filename must contain 'TurbulenceSolutionsLauncher'"
        )

    def test_appimage_chmod_executable(self):
        content = read_script()
        # chmod +x must be applied to the final .AppImage file
        assert re.search(r'chmod\s+\+x.*AppImage', content) or \
               re.search(r'chmod\s+\+x.*\$\{DIST_DIR\}', content), (
            "Script must make the final .AppImage executable with 'chmod +x'"
        )


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


class TestSecurity:
    def test_no_eval_or_unsafe_constructs(self):
        content = read_script()
        # eval is forbidden per security rules
        assert not re.search(r'\beval\b', content), (
            "Script must not use 'eval' — it is an unsafe code-execution construct"
        )

    def test_no_hardcoded_home_path(self):
        content = read_script()
        assert "/home/" not in content, (
            "Script must not hardcode paths under /home/"
        )

    def test_no_hardcoded_absolute_dist_path(self):
        content = read_script()
        # dist/ should be referenced as a relative path, not an absolute one
        assert not re.search(r'["\']?/[a-zA-Z].*?/dist["\']?', content), (
            "dist/ directory must be referenced as a relative path, not an absolute one"
        )

    def test_pyinstaller_output_validated(self):
        content = read_script()
        # Script must check that the PyInstaller output exists before proceeding
        assert re.search(r'if\s+\[.*dist.*launcher', content) or \
               re.search(r'if.*DIST_DIR.*launcher', content), (
            "Script must validate that PyInstaller output exists before building AppDir"
        )


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_app_version_embedded(self):
        content = read_script()
        assert "1.0.2" in content, "Script must embed version 1.0.2"

    def test_publisher_referenced(self):
        content = read_script()
        assert "Turbulence Solutions" in content, (
            "Script must reference publisher 'Turbulence Solutions'"
        )

    def test_references_launcher_spec(self):
        content = read_script()
        assert "launcher.spec" in content, (
            "Script must reference launcher.spec for the PyInstaller build"
        )
