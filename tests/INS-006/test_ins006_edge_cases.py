"""Edge-case tests for INS-006: macOS DMG build script (Tester Agent)

All tests analyse build_dmg.sh as plain text — no execution required.
Tests cover cross-platform safety, XML validity, version consistency,
temp-dir hygiene, and additional security checks the Developer did not include.
"""

import pathlib
import re
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def read_script() -> str:
    return BUILD_DMG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Line-ending safety (critical for macOS bash execution)
# ---------------------------------------------------------------------------


class TestLineEndings:
    """CRLF line endings cause 'bad interpreter' errors on macOS/Linux."""

    def test_no_crlf_line_endings(self):
        raw = BUILD_DMG.read_bytes()
        assert b"\r\n" not in raw, (
            "build_dmg.sh contains Windows CRLF line endings. "
            "Bash on macOS will fail with 'bad interpreter' if CRLF is present."
        )

    def test_no_bare_cr(self):
        raw = BUILD_DMG.read_bytes()
        assert b"\r" not in raw, (
            "build_dmg.sh contains bare CR characters. "
            "This will cause unexpected behaviour in bash."
        )


# ---------------------------------------------------------------------------
# Script encoding
# ---------------------------------------------------------------------------


class TestEncoding:
    def test_no_utf8_bom(self):
        raw = BUILD_DMG.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            "build_dmg.sh must not have a UTF-8 BOM — Bash ignores the "
            "shebang line when a BOM is present."
        )

    def test_script_ends_with_newline(self):
        content = read_script()
        assert content.endswith("\n"), (
            "build_dmg.sh must end with a trailing newline (POSIX requirement)."
        )


# ---------------------------------------------------------------------------
# Version cross-validation against pyproject.toml
# ---------------------------------------------------------------------------


class TestVersionConsistency:
    def test_version_matches_pyproject_toml(self):
        """APP_VERSION constant must match the canonical version in pyproject.toml."""
        with PYPROJECT.open("rb") as fh:
            pyproject = tomllib.load(fh)
        canonical = pyproject["project"]["version"]
        content = read_script()
        assert f'APP_VERSION="{canonical}"' in content or \
               f"APP_VERSION='{canonical}'" in content or \
               f"APP_VERSION={canonical}" in content, (
            f"build_dmg.sh APP_VERSION does not match pyproject.toml version "
            f"({canonical!r}). Update APP_VERSION to stay in sync."
        )


# ---------------------------------------------------------------------------
# Info.plist XML structure
# ---------------------------------------------------------------------------


class TestPlistXMLStructure:
    def test_plist_xml_declaration(self):
        content = read_script()
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content, (
            "Info.plist must begin with the XML declaration: "
            "'<?xml version=\"1.0\" encoding=\"UTF-8\"?>'"
        )

    def test_plist_doctype_present(self):
        content = read_script()
        assert "<!DOCTYPE plist" in content, (
            "Info.plist must include the Apple DTD DOCTYPE declaration."
        )

    def test_plist_root_element_opening(self):
        content = read_script()
        assert '<plist version="1.0">' in content, (
            "Info.plist must have a <plist version=\"1.0\"> root element."
        )

    def test_plist_root_element_closing(self):
        content = read_script()
        assert "</plist>" in content, (
            "Info.plist must have a closing </plist> root element."
        )

    def test_plist_dict_element_present(self):
        content = read_script()
        assert "<dict>" in content and "</dict>" in content, (
            "Info.plist must wrap keys in a <dict>...</dict> element."
        )


# ---------------------------------------------------------------------------
# CFBundleIdentifier format
# ---------------------------------------------------------------------------


class TestBundleIdentifier:
    def test_bundle_id_reverse_domain_format(self):
        """APP_ID constant must use reverse-domain notation (at least one dot)."""
        content = read_script()
        # Extract the APP_ID constant assignment (not the plist interpolation)
        match = re.search(r'APP_ID=["\']?([A-Za-z0-9._-]+)["\']?', content)
        assert match, "APP_ID constant assignment not found in script"
        bundle_id = match.group(1)
        assert "." in bundle_id and bundle_id.startswith("com."), (
            f"APP_ID {bundle_id!r} must use reverse-domain notation starting "
            f"with 'com.' (e.g. com.example.app)."
        )

    def test_bundle_id_references_variable_not_hardcoded(self):
        """Bundle ID value must use the APP_ID variable, not hardcoded differently."""
        content = read_script()
        # The bundle identifier string in the plist must reference ${APP_ID}
        assert "${APP_ID}" in content, (
            "CFBundleIdentifier must be set via the ${APP_ID} variable to avoid "
            "accidental drift between the constant and the plist value."
        )


# ---------------------------------------------------------------------------
# Temp directory hygiene
# ---------------------------------------------------------------------------


class TestTempDirHygiene:
    def test_mktemp_used_for_staging(self):
        content = read_script()
        assert "mktemp" in content, (
            "Script must use mktemp to create a temporary staging directory. "
            "A fixed temp path would cause race conditions and path injection risk."
        )

    def test_staging_dir_cleaned_up(self):
        content = read_script()
        # rm -rf of the staging dir must be present
        assert re.search(r"rm\s+-rf\s+", content), (
            "Script must clean up the temporary staging directory with 'rm -rf' "
            "after DMG creation."
        )

    def test_staging_dir_variable_used_in_rm(self):
        """The rm -rf must apply to the STAGING_DIR variable, not a hardcoded path."""
        content = read_script()
        assert re.search(r'rm\s+-rf\s+["\$].*STAGING', content), (
            "rm -rf must target the \\$STAGING_DIR variable, not a hardcoded path."
        )


# ---------------------------------------------------------------------------
# hdiutil flags
# ---------------------------------------------------------------------------


class TestHdiutilFlags:
    def test_hdiutil_ov_flag(self):
        """Without -ov hdiutil fails if the DMG already exists from a previous run."""
        content = read_script()
        assert "-ov" in content, (
            "hdiutil create must include the -ov flag (overwrite existing file). "
            "Without it, the script fails on a second run."
        )

    def test_hdiutil_srcfolder_flag(self):
        content = read_script()
        assert "-srcfolder" in content, (
            "hdiutil create must use -srcfolder to specify the source directory."
        )

    def test_hdiutil_output_goes_to_dist(self):
        """The -o output path must be under the dist/ directory."""
        content = read_script()
        # -o should reference DIST_DIR or dist/
        assert re.search(r"-o\s+[\"']?\$\{?DIST_DIR\}?", content) or \
               re.search(r"-o\s+[\"']?dist/", content), (
            "hdiutil create -o output must target the dist/ directory."
        )


# ---------------------------------------------------------------------------
# Security: no credentials or sensitive data
# ---------------------------------------------------------------------------


class TestNoCredentials:
    @pytest.mark.parametrize("pattern", [
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "private_key", "-----BEGIN", "aws_access",
    ])
    def test_no_credential_keyword(self, pattern: str):
        content = read_script().lower()
        assert pattern.lower() not in content, (
            f"build_dmg.sh appears to contain the sensitive keyword {pattern!r}. "
            "Credentials must never be embedded in installer scripts."
        )


# ---------------------------------------------------------------------------
# DMG filename composition
# ---------------------------------------------------------------------------


class TestDmgFilename:
    def test_dmg_filename_uses_version_variable(self):
        """DMG filename must be dynamic (uses ${APP_VERSION}), not hardcoded."""
        content = read_script()
        assert "${APP_VERSION}" in content, (
            "DMG_FILENAME must interpolate \\${APP_VERSION} so it changes "
            "automatically when the version constant is updated."
        )

    def test_dmg_filename_uses_arch_variable(self):
        """DMG filename must embed architecture so Intel and ARM outputs differ."""
        content = read_script()
        assert "${TARGET_ARCH}" in content, (
            "DMG_FILENAME must interpolate \\${TARGET_ARCH} so Intel and ARM "
            "builds produce distinct output filenames."
        )

    def test_dmg_extension_is_dmg(self):
        content = read_script()
        assert ".dmg" in content, (
            "Output file must have .dmg extension."
        )


# ---------------------------------------------------------------------------
# Arch fallback: uname -m default
# ---------------------------------------------------------------------------


class TestArchFallback:
    def test_uname_m_fallback(self):
        """When no arch argument is supplied, the script must detect the host arch."""
        content = read_script()
        assert "uname -m" in content or "uname" in content, (
            "Script must use 'uname -m' to detect host architecture when no "
            "TARGET_ARCH argument is supplied."
        )
