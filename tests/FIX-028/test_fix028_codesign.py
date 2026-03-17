"""
FIX-028 — Tests for ad-hoc code signing step in build_dmg.sh

Verifies:
- codesign invocation is present in the script
- --deep flag is present
- --sign - (ad-hoc signing) is present
- codesign --verify step is present
- The signing step appears before hdiutil (DMG creation)
- No CRLF line endings (LF-only)
"""
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "src" / "installer" / "macos" / "build_dmg.sh"


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Presence tests
# ---------------------------------------------------------------------------

def test_script_exists():
    """build_dmg.sh must exist at the expected path."""
    assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"


def test_codesign_invocation_present():
    """build_dmg.sh must contain a codesign signing invocation."""
    text = _script_text()
    assert "codesign" in text, "codesign command not found in build_dmg.sh"


def test_deep_flag_present():
    """The --deep flag must be present in the codesign signing command."""
    text = _script_text()
    # Must appear in a codesign line that is NOT the verify-only line
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert sign_lines, "No codesign --sign line found"
    assert any("--deep" in line for line in sign_lines), (
        "--deep flag not found in codesign signing command"
    )


def test_adhoc_sign_flag_present():
    """The --sign - (ad-hoc signing) flag must be used."""
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert sign_lines, "No codesign --sign line found"
    # --sign - or --sign=- is the ad-hoc identity
    assert any(re.search(r'--sign\s+-(?:\s|$)', line) or "--sign=-" in line
               for line in sign_lines), (
        "Ad-hoc signing flag '--sign -' not found in codesign command"
    )


def test_force_flag_present():
    """The --force flag must be present so re-signing always works."""
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert any("--force" in line for line in sign_lines), (
        "--force flag not found in codesign signing command"
    )


def test_verification_step_present():
    """A codesign --verify step must be present to catch signing failures."""
    text = _script_text()
    verify_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--verify" in line
    ]
    assert verify_lines, "codesign --verify step not found in build_dmg.sh"


def test_verify_uses_deep_strict():
    """The verification step must use --deep --strict for thorough checking."""
    text = _script_text()
    verify_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--verify" in line
    ]
    assert any("--deep" in line for line in verify_lines), (
        "--deep not found in codesign --verify command"
    )
    assert any("--strict" in line for line in verify_lines), (
        "--strict not found in codesign --verify command"
    )


# ---------------------------------------------------------------------------
# Ordering test — signing must come before hdiutil
# ---------------------------------------------------------------------------

def test_codesign_before_hdiutil():
    """The codesign signing step must appear before the hdiutil DMG creation."""
    text = _script_text()
    lines = text.splitlines()

    sign_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--sign" in line
    ]
    hdiutil_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("hdiutil")
    ]

    assert sign_indices, "No codesign --sign line found"
    assert hdiutil_indices, "No hdiutil line found"

    # The last signing line must come before the first hdiutil line
    assert max(sign_indices) < min(hdiutil_indices), (
        "codesign signing must appear before hdiutil create "
        f"(sign at lines {sign_indices}, hdiutil at lines {hdiutil_indices})"
    )


def test_verify_before_hdiutil():
    """The codesign --verify step must appear before hdiutil (so failures halt the build)."""
    text = _script_text()
    lines = text.splitlines()

    verify_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--verify" in line
    ]
    hdiutil_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("hdiutil")
    ]

    assert verify_indices, "No codesign --verify line found"
    assert hdiutil_indices, "No hdiutil line found"

    assert max(verify_indices) < min(hdiutil_indices), (
        "codesign --verify must appear before hdiutil create"
    )


# ---------------------------------------------------------------------------
# CRLF hygiene
# ---------------------------------------------------------------------------

def test_no_crlf_line_endings():
    """build_dmg.sh must use LF-only line endings (no CRLF)."""
    raw = SCRIPT_PATH.read_bytes()
    assert b"\r\n" not in raw, (
        "build_dmg.sh contains CRLF line endings — must be LF only"
    )


# ---------------------------------------------------------------------------
# APP_BUNDLE variable used in codesign
# ---------------------------------------------------------------------------

def test_app_bundle_variable_used_in_codesign():
    """codesign must reference the APP_BUNDLE variable, not a hard-coded path."""
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert any("APP_BUNDLE" in line or "${APP_BUNDLE}" in line
               for line in sign_lines), (
        "codesign signing command should reference the APP_BUNDLE variable"
    )


def test_step_35_label_present():
    """Script should label the new step as Step 3.5 for clarity."""
    text = _script_text()
    assert "3.5" in text, "Step 3.5 label not found in build_dmg.sh"
