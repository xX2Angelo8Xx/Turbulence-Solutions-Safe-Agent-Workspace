"""
FIX-028 — Tests for ad-hoc code signing step in build_dmg.sh

Verifies:
- codesign invocation is present in the script
- --deep flag is present for Python.framework (but NOT on the final .app bundle)
- --sign - (ad-hoc signing) is present
- codesign --verify step is present
- The signing step appears before hdiutil (DMG creation)
- No CRLF line endings (LF-only)

Updated for FIX-031 bottom-up signing pattern.
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
    """--deep must be present for Python.framework signing (valid nested bundle).
    The final .app bundle signing must NOT use --deep (avoids python3.11 dir issue).
    """
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert sign_lines, "No codesign --sign line found"
    # Python.framework signing must use --deep — it IS a valid nested bundle
    assert any("--deep" in line and "Python.framework" in line for line in sign_lines), (
        "--deep flag not found in Python.framework codesign signing command"
    )
    # The final .app bundle signing must NOT use --deep
    app_bundle_lines = [
        line for line in sign_lines
        if line.rstrip().endswith('"${APP_BUNDLE}"')
    ]
    if app_bundle_lines:
        assert not any("--deep" in line for line in app_bundle_lines), (
            "--deep must NOT be present when signing the final .app bundle "
            "(use bottom-up signing to avoid python3.11 directory issue)"
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
    """The verification step must use --deep for thorough Python.framework checking.
    Note: --strict is intentionally omitted per FIX-038 (component-level signing,
    not whole-bundle --deep --strict verification).
    """
    text = _script_text()
    verify_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--verify" in line
    ]
    assert any("--deep" in line for line in verify_lines), (
        "--deep not found in any codesign --verify command (expected for Python.framework)"
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


# ---------------------------------------------------------------------------
# Tester edge-case additions
# ---------------------------------------------------------------------------

def test_verify_comes_after_sign():
    """codesign --verify must appear AFTER codesign --sign (not before)."""
    text = _script_text()
    lines = text.splitlines()

    sign_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--sign" in line
    ]
    verify_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--verify" in line
    ]

    assert sign_indices, "No codesign --sign line found"
    assert verify_indices, "No codesign --verify line found"

    assert max(sign_indices) < min(verify_indices), (
        "codesign --verify must appear AFTER codesign --sign "
        f"(sign at lines {sign_indices}, verify at lines {verify_indices})"
    )


def test_no_hardcoded_credentials():
    """No Apple Developer ID, certificate name, TEAM_ID, APPLE_ID, or keychain
    references should appear in the codesign command — only '-' for ad-hoc."""
    text = _script_text()
    # Collect all codesign lines
    codesign_lines = [
        line for line in text.splitlines()
        if "codesign" in line.lower()
    ]
    combined = " ".join(codesign_lines).lower()

    # These strings indicate a real Apple Developer identity is referenced
    forbidden_patterns = [
        "developer id",
        "apple development",
        "apple distribution",
        "team_id",
        "teamid",
        "apple_id",
        "appleid",
        "certificate",
        "keychain",
        "p12",
        ".cer",
        ".p12",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in combined, (
            f"Forbidden credential reference '{pattern}' found in codesign "
            "command — use ad-hoc '-' only, no Apple Developer credentials"
        )


def test_app_bundle_quoted_in_codesign():
    """APP_BUNDLE must be double-quoted in the codesign command context.
    Updated for multi-line command format: checks that APP_BUNDLE appears quoted
    anywhere in the script signing context.
    """
    text = _script_text()
    # APP_BUNDLE is used in multi-line signing commands; check it appears quoted
    # either as "${APP_BUNDLE}" or as part of a quoted path "${APP_BUNDLE}/..."
    assert '"${APP_BUNDLE}"' in text or '"${APP_BUNDLE}/' in text, (
        'APP_BUNDLE must be double-quoted: "${APP_BUNDLE}" in codesign command'
    )


def test_verify_app_bundle_quoted():
    """APP_BUNDLE must be double-quoted in the codesign --verify command."""
    text = _script_text()
    verify_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--verify" in line
    ]
    assert verify_lines, "No codesign --verify line found"
    assert any('"${APP_BUNDLE}"' in line or '"$APP_BUNDLE"' in line
               for line in verify_lines), (
        'APP_BUNDLE must be double-quoted: "${APP_BUNDLE}" in codesign --verify command'
    )


def test_sign_identity_is_exactly_adhoc():
    """The sign identity must be exactly '-' (ad-hoc), not a certificate name."""
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert sign_lines, "No codesign --sign line found"
    # --sign - must be present with a dash as the identity token
    # Ensure no --sign 'Developer ID...' or --sign "cert name" is used instead
    import re as _re
    for line in sign_lines:
        match = _re.search(r'--sign\s+(\S+)', line)
        if match:
            identity = match.group(1).strip('"\'')
            assert identity == "-", (
                f"Sign identity must be '-' for ad-hoc signing, got: '{identity}'"
            )


def test_pipefail_set_in_script():
    """Script must use 'set -euo pipefail' so codesign failures abort the build."""
    text = _script_text()
    assert "pipefail" in text, (
        "'set -euo pipefail' not found — codesign failures may be silently ignored"
    )


def test_codesign_step_between_infoplist_and_hdiutil():
    """Step 3.5 codesign must come AFTER Info.plist write (Step 3) and BEFORE
    hdiutil (Step 4). Confirms the bundle is fully assembled before signing."""
    text = _script_text()
    lines = text.splitlines()

    plist_indices = [
        i for i, line in enumerate(lines)
        if "Info.plist" in line or "PLIST" in line
    ]
    sign_indices = [
        i for i, line in enumerate(lines)
        if "codesign" in line and "--sign" in line
    ]
    hdiutil_indices = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("hdiutil")
    ]

    assert plist_indices, "No Info.plist reference found"
    assert sign_indices, "No codesign --sign line found"
    assert hdiutil_indices, "No hdiutil line found"

    assert max(plist_indices) < min(sign_indices), (
        "codesign signing must come AFTER the Info.plist block is written "
        f"(plist refs at lines {plist_indices}, sign at lines {sign_indices})"
    )
    assert max(sign_indices) < min(hdiutil_indices), (
        "codesign signing must come BEFORE hdiutil create "
        f"(sign at lines {sign_indices}, hdiutil at lines {hdiutil_indices})"
    )


# ---------------------------------------------------------------------------
# FIX-031 bottom-up signing pattern tests (added for updated signing approach)
# ---------------------------------------------------------------------------

def test_find_dylib_signing_present():
    """build_dmg.sh must use find to sign .dylib files before signing the bundle."""
    text = _script_text()
    lines = text.splitlines()
    assert any(
        "find" in line and "*.dylib" in line and "codesign" in line
        for line in lines
    ), "find ... *.dylib ... codesign pattern not found in build_dmg.sh"


def test_find_so_signing_present():
    """build_dmg.sh must use find to sign .so files before signing the bundle."""
    text = _script_text()
    lines = text.splitlines()
    assert any(
        "find" in line and "*.so" in line and "codesign" in line
        for line in lines
    ), "find ... *.so ... codesign pattern not found in build_dmg.sh"


def test_python_framework_signing_uses_deep():
    """Python.framework must be signed with --deep (it is a valid nested bundle)."""
    text = _script_text()
    sign_lines = [
        line for line in text.splitlines()
        if "codesign" in line and "--sign" in line
    ]
    assert any(
        "--deep" in line and "Python.framework" in line
        for line in sign_lines
    ), "--deep not found on Python.framework codesign line"
