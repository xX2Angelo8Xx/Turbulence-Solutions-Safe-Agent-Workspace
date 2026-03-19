"""Additional Tester Agent edge-case tests for INS-007: Linux Installer (build_appimage.sh)

Second tester additions file — covering areas not addressed by the three existing
test files:
  - test_ins007_build_appimage.py  (developer primary tests)
  - test_ins007_edge_cases.py      (developer extra edge cases)
  - test_ins007_tester.py          (first Tester Agent pass)

New areas covered:
  - No sudo usage (CI build scripts must not require elevated privileges)
  - No interactive 'read' command (CI builds must be fully non-interactive)
  - mkdir -p for every AppDir subdirectory (idempotent directory creation)
  - cp -R used to copy PyInstaller onedir bundle recursively into AppDir
  - APPDIR variable is defined relative to DIST_DIR (no independent hardcoded path)
  - APPIMAGE_FILENAME references TARGET_ARCH variable (dynamic, architecture-aware)
  - APPIMAGETOOL binary path includes TARGET_ARCH in filename (avoids binary collision)
  - Success echo (' ==> Done') present at end of script (CI log confirmation)
  - Conditional appimagetool download (skip if binary already cached locally)
  - No --insecure / -k flag in curl (TLS certificate validation must not be bypassed)
  - Desktop file Comment= field present and references product/publisher
  - Script argument-passing guard prevents unquoted injection via $1
"""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"


def read_script() -> str:
    return BUILD_APPIMAGE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Privilege escalation — sudo must not appear in a CI build script
# ---------------------------------------------------------------------------


class TestNoPrivilegeEscalation:
    def test_no_sudo_command(self):
        """sudo must not appear in a CI build script — blocks unattended execution."""
        content = read_script()
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.strip().startswith("#")
        ]
        for line in non_comment_lines:
            assert not re.search(r"\bsudo\b", line), (
                f"Build script must not use sudo — CI pipelines run without interactive "
                f"privilege escalation; found: {line!r}"
            )


# ---------------------------------------------------------------------------
# Non-interactive — must be safe for CI/CD pipelines
# ---------------------------------------------------------------------------


class TestNonInteractive:
    def test_no_read_builtin_command(self):
        """Shell 'read' built-in would block unattended CI execution waiting for input."""
        content = read_script()
        for line in content.splitlines():
            if line.strip().startswith("#"):
                continue
            # 'read' as a standalone command (not 'readlink' which is legitimate)
            assert not re.match(r"^\s*read\s", line), (
                f"Build script must not use the 'read' built-in — it would block "
                f"automated CI execution waiting for keyboard input; found: {line!r}"
            )


# ---------------------------------------------------------------------------
# Idempotent directory creation
# ---------------------------------------------------------------------------


class TestIdempotentDirectoryCreation:
    def test_all_mkdir_calls_use_p_flag(self):
        """Every mkdir call must include -p to prevent failure on existing directories."""
        content = read_script()
        mkdir_lines = [
            line for line in content.splitlines()
            if re.search(r"\bmkdir\b", line) and not line.strip().startswith("#")
        ]
        assert len(mkdir_lines) >= 1, "No mkdir calls found in script"
        for line in mkdir_lines:
            assert re.search(r"mkdir\s+-p\b", line), (
                f"Every mkdir must use -p for idempotent creation; found: {line!r}"
            )


# ---------------------------------------------------------------------------
# PyInstaller output copy strategy
# ---------------------------------------------------------------------------


class TestPyInstallerOutputCopy:
    def test_cp_recursive_flag_used_for_launcher_bundle(self):
        """cp -R (or cp -r) must copy the PyInstaller onedir bundle — plain cp fails on dirs."""
        content = read_script()
        assert re.search(r"\bcp\s+-[Rr]\b", content), (
            "Script must use 'cp -R' or 'cp -r' to recursively copy the PyInstaller "
            "--onedir bundle into AppDir/usr/bin/. A plain 'cp' would fail on directories."
        )


# ---------------------------------------------------------------------------
# Variable-based path definitions — no independent hardcoded paths
# ---------------------------------------------------------------------------


class TestVariableBasedPaths:
    def test_appdir_defined_relative_to_dist_dir_variable(self):
        """APPDIR= must reference ${DIST_DIR} so it follows any DIST_DIR override."""
        content = read_script()
        # The assignment: APPDIR="${DIST_DIR}/AppDir"
        appdir_assign = re.search(r'APPDIR\s*=\s*"?([^"\n]+)"?', content)
        assert appdir_assign is not None, "APPDIR variable assignment not found in script"
        appdir_value = appdir_assign.group(1)
        assert "DIST_DIR" in appdir_value, (
            f"APPDIR must be defined using the ${{DIST_DIR}} variable so it stays "
            f"consistent with the rest of the script; found: {appdir_value!r}"
        )

    def test_appimage_filename_uses_target_arch_variable(self):
        """APPIMAGE_FILENAME= must include $TARGET_ARCH for architecture-specific naming."""
        content = read_script()
        filename_assign = re.search(r'APPIMAGE_FILENAME\s*=\s*"?([^"\n]+)"?', content)
        assert filename_assign is not None, "APPIMAGE_FILENAME assignment not found"
        filename_value = filename_assign.group(1)
        assert "TARGET_ARCH" in filename_value, (
            f"APPIMAGE_FILENAME must incorporate ${{TARGET_ARCH}} so x86_64 and aarch64 "
            f"output files have distinct names; found: {filename_value!r}"
        )

    def test_appimagetool_binary_path_includes_target_arch(self):
        """Local APPIMAGETOOL path must include TARGET_ARCH to avoid binary collision."""
        content = read_script()
        # Assignment: APPIMAGETOOL="./appimagetool-${TARGET_ARCH}.AppImage"
        tool_assign = re.search(r'APPIMAGETOOL\s*=\s*"?([^"\n]+)"?', content)
        assert tool_assign is not None, "APPIMAGETOOL assignment not found"
        tool_value = tool_assign.group(1)
        assert "TARGET_ARCH" in tool_value, (
            f"Local APPIMAGETOOL binary path must include ${{TARGET_ARCH}} to prevent "
            f"a cached x86_64 binary being silently used for an aarch64 build; "
            f"found: {tool_value!r}"
        )


# ---------------------------------------------------------------------------
# Success feedback — CI log confirmation
# ---------------------------------------------------------------------------


class TestSuccessFeedback:
    def test_success_echo_present_at_end_of_script(self):
        """Script must print a '==> Done' message so CI logs confirm build completion."""
        content = read_script()
        # The script ends with: echo "==> Done: ${DIST_DIR}/${APPIMAGE_FILENAME}"
        assert re.search(r"echo.*[Dd]one", content), (
            "Script must print a success/completion echo at the end "
            "(e.g. 'echo \"==> Done: ...\"') so operator and CI logs confirm the "
            "build finished successfully"
        )


# ---------------------------------------------------------------------------
# Conditional appimagetool download (reproducible builds / caching)
# ---------------------------------------------------------------------------


class TestConditionalAppimagetoolDownload:
    def test_download_guarded_by_file_existence_check(self):
        """appimagetool download must be skipped when the binary already exists locally."""
        content = read_script()
        # Pattern: if [ ! -f "${APPIMAGETOOL}" ] — variable is uppercase in script
        assert re.search(r'if\s+\[.*!\s+-f.*appimagetool', content, re.IGNORECASE), (
            "appimagetool download must be guarded with 'if [ ! -f ... ]' to avoid "
            "re-downloading on repeated builds (faster CI, reproducible artefacts)"
        )


# ---------------------------------------------------------------------------
# curl security — no TLS certificate validation bypass
# ---------------------------------------------------------------------------


class TestCurlCertificateSafety:
    def test_no_curl_insecure_long_flag(self):
        """curl --insecure disables TLS cert validation — strictly forbidden."""
        content = read_script()
        curl_lines = [
            line for line in content.splitlines()
            if re.search(r"\bcurl\b", line) and not line.strip().startswith("#")
        ]
        for line in curl_lines:
            assert "--insecure" not in line, (
                f"'curl --insecure' bypasses TLS certificate validation — "
                f"a critical security risk for software downloads; found: {line!r}"
            )

    def test_no_curl_k_short_flag(self):
        """curl -k is the short form of --insecure — must not appear in download lines."""
        content = read_script()
        curl_lines = [
            line for line in content.splitlines()
            if re.search(r"\bcurl\b", line) and not line.strip().startswith("#")
        ]
        for line in curl_lines:
            # Match -k as a standalone flag (not part of -fsSL or similar combined flags
            # where k doesn't appear): check for -k as a separate argument or in a flag
            # group that contains 'k'
            assert not re.search(r"curl\s+[^|&;#\n]*\s-[a-zA-Z]*k[a-zA-Z]*(?:\s|$)", line), (
                f"'curl -k' bypasses TLS certificate validation — "
                f"a critical security risk for software downloads; found: {line!r}"
            )


# ---------------------------------------------------------------------------
# Desktop file completeness — Comment= field
# ---------------------------------------------------------------------------


class TestDesktopFileCompleteness:
    def test_desktop_has_comment_field(self):
        """The .desktop file must include a Comment= field (FreeDesktop recommendation)."""
        content = read_script()
        assert "Comment=" in content, (
            "The .desktop entry must include a Comment= field as recommended by the "
            "FreeDesktop specification for accessible application descriptions"
        )

    def test_desktop_comment_references_product_or_publisher(self):
        """The Comment= value must contain the publisher or product name."""
        content = read_script()
        comment_lines = [
            line for line in content.splitlines()
            if line.strip().startswith("Comment=")
        ]
        assert len(comment_lines) >= 1, "No Comment= line found in .desktop heredoc"
        # In the raw script the heredoc is: Comment=${PUBLISHER} Agent Environment Launcher
        # so the literal text contains either PUBLISHER or Turbulence or Launcher
        assert any(
            "PUBLISHER" in ln or "Turbulence" in ln or "Launcher" in ln
            for ln in comment_lines
        ), (
            f"Comment= field should contain the publisher name or product reference; "
            f"found: {comment_lines}"
        )


# ---------------------------------------------------------------------------
# Argument guard — $1 validated before use (injection prevention)
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    def test_first_arg_validated_before_assignment(self):
        """TARGET_ARCH from $1 must only be assigned after an explicit equality check."""
        content = read_script()
        lines = content.splitlines()
        # Confirm: TARGET_ARCH="${1}" is inside an if/elif block that checks the value
        for i, line in enumerate(lines):
            if re.search(r'TARGET_ARCH\s*=\s*["\']?\$\{?1\}?["\']?', line):
                # Walk backwards to verify we're inside an if/elif condition
                context = "\n".join(lines[max(0, i - 5) : i + 1])
                assert re.search(r'if\s+\[|elif\s+\[', context), (
                    "TARGET_ARCH must only be set from $1 inside a conditional block "
                    "that validates the argument value (injection prevention)"
                )
                return
        pytest.fail("Could not find TARGET_ARCH=$1 assignment in script")
