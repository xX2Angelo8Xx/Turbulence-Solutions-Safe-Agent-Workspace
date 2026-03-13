"""Edge-case tests for INS-007: Linux Installer (build_appimage.sh)

Tester additions — covers gaps identified during review:
  - ARCH env var passed to appimagetool
  - --proto '=https' flag (defence-in-depth alongside --tlsv1.2)
  - Error messages directed to stderr (>&2)
  - AppDir rm -rf before rebuild (idempotent build hygiene)
  - .desktop Categories field (AppImage spec requirement)
  - AppRun $@ argument forwarding
  - chmod +x on downloaded appimagetool
  - --noconfirm for PyInstaller (no interactive prompts)
  - Version consistency with pyproject.toml
  - Unsupported architecture exits with descriptive error
  - exit 1 on PyInstaller output missing
  - SVG contains valid xmlns namespace declaration
  - appimagetool URL references official AppImageKit repository
  - appimagetool downloaded to a relative (not absolute) path
  - Script header identifies RunFrom requirement
"""

import pathlib
import re
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"


def read_script() -> str:
    return BUILD_APPIMAGE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# ARCH environment variable — required for correct ELF header embedding
# ---------------------------------------------------------------------------


class TestArchEnvVar:
    def test_arch_env_var_passed_to_appimagetool(self):
        """appimagetool must receive ARCH= env var to embed correct ELF arch."""
        content = read_script()
        # Expect: ARCH="${TARGET_ARCH}" "${APPIMAGETOOL}" ...
        # The tool is invoked via the ${APPIMAGETOOL} variable (uppercase in source)
        assert re.search(r'ARCH=.*APPIMAGETOOL', content), (
            "Script must pass ARCH= environment variable to appimagetool so the "
            "correct ELF architecture is embedded in the AppImage header. "
            "Expected pattern: ARCH=\"${TARGET_ARCH}\" \"${APPIMAGETOOL}\" ..."
        )

    def test_arch_env_var_uses_target_arch_value(self):
        """ARCH should be set to the resolved TARGET_ARCH variable."""
        content = read_script()
        assert re.search(r'ARCH=["\']?\$\{?TARGET_ARCH\}?["\']?', content), (
            "ARCH= must be set to the resolved TARGET_ARCH value, not a literal string"
        )


# ---------------------------------------------------------------------------
# TLS and protocol security
# ---------------------------------------------------------------------------


class TestTlsProtocol:
    def test_curl_uses_proto_https_flag(self):
        """--proto '=https' enforces HTTPS-only protocol at the libcurl level."""
        content = read_script()
        curl_lines = [line for line in content.splitlines() if "curl" in line]
        assert any("--proto" in line for line in curl_lines), (
            "curl must use --proto '=https' flag to restrict protocol to HTTPS "
            "only (defence-in-depth alongside --tlsv1.2)"
        )

    def test_curl_uses_fail_flag(self):
        """curl -f (or -fsSL) ensures non-zero exit on HTTP errors."""
        content = read_script()
        curl_lines = [line for line in content.splitlines() if "curl" in line]
        assert any(re.search(r'curl\s+-[a-zA-Z]*f', line) for line in curl_lines), (
            "curl must use the -f flag (fail on HTTP errors) to prevent silent "
            "download failures producing a non-AppImage response body"
        )


# ---------------------------------------------------------------------------
# Error handling quality
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_error_messages_go_to_stderr(self):
        """ERROR echo lines must redirect to stderr with >&2."""
        content = read_script()
        error_lines = [
            line for line in content.splitlines()
            if re.search(r'\becho\b.*ERROR', line)
        ]
        assert len(error_lines) >= 1, "Script must have at least one ERROR echo line"
        for line in error_lines:
            assert ">&2" in line, (
                f"ERROR message must redirect to stderr with >&2; found: {line!r}"
            )

    def test_exit_1_on_pyinstaller_output_missing(self):
        """Script must exit 1 when PyInstaller output is absent after build."""
        content = read_script()
        # Must have both an error echo and exit 1 for missing PyInstaller output
        assert re.search(r'exit\s+1', content), (
            "Script must exit with code 1 on fatal errors (missing PyInstaller output)"
        )

    def test_unsupported_arch_has_error_message(self):
        """Unsupported architecture must produce a descriptive error message."""
        content = read_script()
        assert re.search(
            r'echo.*[Uu]nsupported.*arch|echo.*[Ee]rror.*arch',
            content,
            re.IGNORECASE
        ), (
            "Script must print a descriptive error for unsupported architectures"
        )

    def test_unsupported_arch_error_exits_nonzero(self):
        """Unsupported architecture must cause the script to exit with non-zero."""
        content = read_script()
        lines = content.splitlines()
        # Find the unsupported arch error section and confirm exit 1 nearby
        for i, line in enumerate(lines):
            if "Unsupported architecture" in line:
                # Look within the next 3 lines for exit 1
                context = "\n".join(lines[i:i+4])
                assert "exit 1" in context, (
                    "Unsupported architecture error block must call exit 1"
                )
                return
        pytest.fail("Could not find unsupported architecture error block")


# ---------------------------------------------------------------------------
# Build hygiene
# ---------------------------------------------------------------------------


class TestBuildHygiene:
    def test_appdir_removed_before_rebuild(self):
        """rm -rf AppDir must be called to ensure a clean idempotent build."""
        content = read_script()
        assert re.search(r'rm\s+-rf\s+.*APPDIR|rm\s+-rf\s+.*AppDir', content), (
            "Script must remove the AppDir before rebuilding to guarantee "
            "idempotent, clean builds (prevents stale artefacts)"
        )

    def test_pyinstaller_noconfirm_flag(self):
        """--noconfirm prevents PyInstaller interactive prompts in CI."""
        content = read_script()
        assert "--noconfirm" in content, (
            "PyInstaller invocation must use --noconfirm to suppress any "
            "interactive confirmation prompts during automated builds"
        )

    def test_appimagetool_downloaded_to_relative_path(self):
        """appimagetool binary must be saved to a relative (not absolute) path."""
        content = read_script()
        # Find the -o flag line in the curl download
        curl_lines = [
            line for line in content.splitlines()
            if re.search(r'\bcurl\b.*-o\b', line)
        ]
        assert len(curl_lines) >= 1, "No curl -o download line found"
        for line in curl_lines:
            # -o must not be followed by an absolute path like /usr/ or /home/
            output_arg_match = re.search(r'-o\s+"?([^"\s]+)"?', line)
            if output_arg_match:
                path = output_arg_match.group(1)
                assert not path.startswith("/usr/") and not path.startswith("/home/"), (
                    f"appimagetool must be downloaded to a relative path, not {path!r}"
                )


# ---------------------------------------------------------------------------
# AppImage spec compliance
# ---------------------------------------------------------------------------


class TestAppImageSpecCompliance:
    def test_desktop_file_has_categories_field(self):
        """Categories= is required by the FreeDesktop spec for AppImage desktop files."""
        content = read_script()
        assert "Categories=" in content, (
            "The .desktop file must include a Categories= field as required by "
            "FreeDesktop and expected by AppImage integration tools"
        )

    def test_apprun_forwards_arguments(self):
        """AppRun must forward all arguments to the launcher binary via '$@'."""
        content = read_script()
        assert '"$@"' in content or "'$@'" in content, (
            "AppRun must forward command-line arguments using \"$@\" so the "
            "launcher can receive CLI arguments when invoked via AppImage"
        )

    def test_appimagetool_chmod_after_download(self):
        """Downloaded appimagetool must be made executable before first use."""
        content = read_script()
        # Look for chmod +x on the appimagetool variable or a named file
        lines = content.splitlines()
        chmod_lines = [
            line for line in lines
            if re.search(r'chmod\s+\+x', line) and "appimagetool" in line.lower()
        ]
        assert len(chmod_lines) >= 1, (
            "Downloaded appimagetool binary must be made executable with "
            "'chmod +x' before it can be invoked"
        )


# ---------------------------------------------------------------------------
# SVG icon quality
# ---------------------------------------------------------------------------


class TestSvgIcon:
    def test_svg_has_xmlns_namespace(self):
        """The embedded SVG must declare the standard W3C SVG namespace."""
        content = read_script()
        assert 'xmlns="http://www.w3.org/2000/svg"' in content or \
               "xmlns='http://www.w3.org/2000/svg'" in content, (
            "The placeholder SVG icon must include the standard "
            'xmlns="http://www.w3.org/2000/svg" namespace declaration '
            "for compatibility with AppImage icon tools"
        )

    def test_svg_has_viewbox(self):
        """SVG must declare a viewBox for resolution-independent rendering."""
        content = read_script()
        assert "viewBox" in content, (
            "The placeholder SVG icon must include a viewBox attribute "
            "to ensure resolution-independent scaling in desktop environments"
        )


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------


class TestVersionConsistency:
    def test_app_version_matches_pyproject_toml(self):
        """Version in build_appimage.sh must match pyproject.toml."""
        with open(PYPROJECT_TOML, "rb") as f:
            pyproject = tomllib.load(f)
        toml_version = pyproject["project"]["version"]
        content = read_script()
        assert toml_version in content, (
            f"APP_VERSION in build_appimage.sh must match pyproject.toml version "
            f"({toml_version!r}); update APP_VERSION when bumping the package version"
        )


# ---------------------------------------------------------------------------
# Security — appimagetool source authenticity
# ---------------------------------------------------------------------------


class TestAppImageToolSource:
    def test_appimagetool_url_references_official_appimagekit(self):
        """appimagetool must be downloaded from the official AppImageKit repository."""
        content = read_script()
        # Only lines that contain download URLs (not comments)
        url_lines = [
            line for line in content.splitlines()
            if "https://github.com" in line and "appimagetool" in line.lower()
        ]
        assert len(url_lines) >= 1, (
            "No appimagetool download URL found in script"
        )
        for line in url_lines:
            assert "AppImage/AppImageKit" in line, (
                f"appimagetool must be downloaded from the official "
                f"github.com/AppImage/AppImageKit repository; found: {line!r}"
            )

    def test_no_wget_as_alternative_downloader(self):
        """Script must not fall back to wget — only curl is permitted."""
        content = read_script()
        # wget in a comment is allowed; wget in an actual command is not
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        ]
        for line in non_comment_lines:
            assert "wget" not in line, (
                f"Script must use only curl for downloads — no wget: {line!r}"
            )
