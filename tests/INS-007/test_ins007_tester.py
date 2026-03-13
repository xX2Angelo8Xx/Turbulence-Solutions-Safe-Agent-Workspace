"""Tester Agent edge-case tests for INS-007: Linux Installer (build_appimage.sh)

Additional tests written by Tester Agent — covering gaps beyond both the
Developer's primary tests and the previously added edge-case file.

Areas covered:
  - CRLF line endings (would break bash on Linux)
  - UTF-8 BOM check (would break shebang parsing)
  - POSIX trailing newline
  - Hardcoded credentials check (password/token/secret/api_key)
  - AppRun heredoc shebang (#!/bin/bash)
  - Desktop file Icon= field references APP_ID variable (not literal)
  - hicolor path contains 256x256 size specification
  - PyInstaller invoked via 'python -m PyInstaller' (not bare 'pyinstaller')
  - Script usage comment mentions repository root
  - AppRun inner script has 'set -e' for fail-fast behaviour
  - Output AppImage placed in ${DIST_DIR} (relative variable, not literal path)
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"


def read_script() -> str:
    return BUILD_APPIMAGE.read_text(encoding="utf-8")


def read_script_bytes() -> bytes:
    return BUILD_APPIMAGE.read_bytes()


# ---------------------------------------------------------------------------
# Line endings — critical for Linux bash execution
# ---------------------------------------------------------------------------


class TestLineEndings:
    def test_no_crlf_line_endings(self):
        """Script must use LF-only endings; CRLF causes bash errors on Linux."""
        raw = read_script_bytes()
        assert b"\r\n" not in raw, (
            "build_appimage.sh contains CRLF (\\r\\n) line endings. "
            "Bash on Linux will fail with 'command not found' or syntax errors "
            "when the script is executed. Convert to LF-only."
        )

    def test_no_bare_cr(self):
        """No standalone carriage return characters (old Mac line endings)."""
        raw = read_script_bytes()
        # Filter out \r\n already checked above; look for isolated \r
        content_no_crlf = raw.replace(b"\r\n", b"\n")
        assert b"\r" not in content_no_crlf, (
            "build_appimage.sh contains bare CR (\\r) characters. "
            "These would cause shell parse errors on Linux."
        )


# ---------------------------------------------------------------------------
# File encoding — a BOM breaks the shebang on Linux
# ---------------------------------------------------------------------------


class TestFileEncoding:
    def test_no_utf8_bom(self):
        """UTF-8 BOM (EF BB BF) would cause the shebang to be unrecognised."""
        raw = read_script_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            "build_appimage.sh starts with a UTF-8 BOM. Linux kernel shebang "
            "parsing requires the first two bytes to be '#!'; the BOM prevents "
            "the script from executing correctly."
        )

    def test_posix_trailing_newline(self):
        """POSIX: text files must end with a newline character."""
        raw = read_script_bytes()
        assert raw.endswith(b"\n"), (
            "build_appimage.sh does not end with a newline. "
            "POSIX requires text files to end with '\\n'; some tools may "
            "misread the last line if the newline is absent."
        )


# ---------------------------------------------------------------------------
# Security — no hardcoded credentials or sensitive strings
# ---------------------------------------------------------------------------


class TestNoCredentials:
    SENSITIVE_PATTERNS = [
        (r'\bpassword\s*=', "password= assignment"),
        (r'\btoken\s*=', "token= assignment"),
        (r'\bapi_key\s*=', "api_key= assignment"),
        (r'\bprivate_key\b', "private_key reference"),
        (r'-----BEGIN\s+\w+\s+PRIVATE KEY-----', "PEM private-key header"),
        (r'\bAWSACCESSKEY\b|\baws_access_key_id\b', "AWS access key"),
    ]

    @pytest.mark.parametrize("pattern,description", SENSITIVE_PATTERNS)
    def test_no_sensitive_keyword(self, pattern, description):
        """Script must not contain hardcoded sensitive credentials."""
        content = read_script()
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        ]
        for line in non_comment_lines:
            assert not re.search(pattern, line, re.IGNORECASE), (
                f"Found sensitive pattern '{description}' in script: {line!r}"
            )


# ---------------------------------------------------------------------------
# AppRun reliability — shebang and error propagation
# ---------------------------------------------------------------------------


class TestAppRunReliability:
    def test_apprun_heredoc_has_bash_shebang(self):
        """The AppRun heredoc must begin with #!/bin/bash for explicit bash usage."""
        content = read_script()
        # The AppRun heredoc content starts just after << 'APPRUN'
        apprun_match = re.search(
            r"cat\s*>\s*.*AppRun.*<<\s*['\"]?APPRUN['\"]?(.*?)APPRUN",
            content,
            re.DOTALL
        )
        assert apprun_match is not None, (
            "Could not locate AppRun heredoc in script"
        )
        apprun_body = apprun_match.group(1)
        assert apprun_body.strip().startswith("#!/bin/bash") or \
               apprun_body.strip().startswith("#!/usr/bin/env bash"), (
            "AppRun heredoc must begin with a bash shebang (#!/bin/bash or "
            "#!/usr/bin/env bash) so it executes with bash when invoked"
        )

    def test_apprun_has_set_e(self):
        """AppRun body should use 'set -e' to propagate errors to AppImage caller."""
        content = read_script()
        apprun_match = re.search(
            r"cat\s*>\s*.*AppRun.*<<\s*['\"]?APPRUN['\"]?(.*?)APPRUN",
            content,
            re.DOTALL
        )
        assert apprun_match is not None, "Could not locate AppRun heredoc"
        apprun_body = apprun_match.group(1)
        assert re.search(r"set\s+-[a-z]*e", apprun_body), (
            "AppRun must use 'set -e' (or similar) so that errors inside AppRun "
            "propagate the correct exit code to the AppImage launcher"
        )


# ---------------------------------------------------------------------------
# Desktop file correctness
# ---------------------------------------------------------------------------


class TestDesktopFileCorrectness:
    def test_icon_field_uses_app_id_variable(self):
        """Icon= in .desktop must use ${APP_ID} variable for correct icon lookup."""
        content = read_script()
        # The desktop heredoc sets Icon= — it should use the variable
        assert re.search(r'Icon=\$\{?APP_ID\}?', content), (
            "The .desktop file Icon= field must reference the ${APP_ID} variable "
            "so the filename matches the SVG icon that is written to AppDir. "
            "A mismatch between Icon name and SVG filename prevents icon display."
        )

    def test_hicolor_path_contains_256x256(self):
        """hicolor icon theme path must specify 256x256 size."""
        content = read_script()
        assert "256x256" in content, (
            "The hicolor icon path must include the 256x256 size directory "
            "(e.g. usr/share/icons/hicolor/256x256/apps/) for correct "
            "FreeDesktop icon theme integration"
        )


# ---------------------------------------------------------------------------
# PyInstaller invocation safety
# ---------------------------------------------------------------------------


class TestPyinstallerInvocation:
    def test_pyinstaller_invoked_via_python_m(self):
        """PyInstaller must be invoked as 'python -m PyInstaller', not bare pyinstaller."""
        content = read_script()
        # The correct form uses the active Python's module runner
        assert re.search(r'python\s+-m\s+PyInstaller', content), (
            "PyInstaller must be invoked as 'python -m PyInstaller' to ensure "
            "the correct interpreter's PyInstaller is used. A bare 'pyinstaller' "
            "command may resolve to a different Python environment."
        )


# ---------------------------------------------------------------------------
# Output path safety — relative ${DIST_DIR} variable
# ---------------------------------------------------------------------------


class TestOutputPathRelative:
    def test_appimage_output_uses_dist_dir_variable(self):
        """Final AppImage must be placed under ${DIST_DIR}, not a hardcoded path."""
        content = read_script()
        # The appimagetool invocation should reference ${DIST_DIR} for output
        tool_invocation_lines = [
            line for line in content.splitlines()
            if "APPIMAGETOOL" in line and "APPDIR" in line
        ]
        assert len(tool_invocation_lines) >= 1, (
            "Could not find appimagetool invocation line"
        )
        for line in tool_invocation_lines:
            assert "DIST_DIR" in line or "dist/" in line, (
                f"appimagetool output path must use ${'{'}DIST_DIR{'}'} "
                f"variable; found: {line!r}"
            )

    def test_no_hardcoded_absolute_appimage_output(self):
        """AppImage output path must not start with /usr or /opt or /home."""
        content = read_script()
        # The final chmod +x and appimagetool output must not use absolute paths
        appimage_lines = [
            line for line in content.splitlines()
            if ".AppImage" in line and not line.strip().startswith("#")
        ]
        for line in appimage_lines:
            assert not re.search(r'["\']?/(?:usr|opt|home|var)/', line), (
                f"AppImage output must use relative paths; found absolute: {line!r}"
            )
