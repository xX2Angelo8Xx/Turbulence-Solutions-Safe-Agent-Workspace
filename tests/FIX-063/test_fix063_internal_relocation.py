"""
Tests for FIX-063: Move _internal/ to Contents/Resources/ with symlink for codesign.

Verifies that build_dmg.sh:
  - Moves Contents/MacOS/_internal to Contents/Resources/_internal (mv command)
  - Creates a symlink Contents/MacOS/_internal -> ../Resources/_internal
  - Updates Step 3.1 .dist-info removal to target Contents/Resources/_internal
  - Removes the FIX-062 per-file TS-Logo relocation loop (Step 3.2)
  - Updates all Step 3.5 signing paths to Contents/Resources/_internal
  - Updates Python.framework verification path to Contents/Resources/_internal
  - No signing/verification step references Contents/MacOS/_internal
  - File uses LF line endings throughout (no CRLF)
"""

import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[2] / "src" / "installer" / "macos" / "build_dmg.sh"


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _script_bytes() -> bytes:
    return SCRIPT_PATH.read_bytes()


# ---------------------------------------------------------------------------
# Basic sanity
# ---------------------------------------------------------------------------

def test_script_exists():
    assert SCRIPT_PATH.exists(), f"build_dmg.sh not found at {SCRIPT_PATH}"


def test_no_crlf_line_endings():
    data = _script_bytes()
    crlf_count = data.count(b"\r\n")
    assert crlf_count == 0, (
        f"build_dmg.sh contains {crlf_count} CRLF sequences — must use LF only"
    )


# ---------------------------------------------------------------------------
# Step 2.1 — mv + symlink
# ---------------------------------------------------------------------------

def test_step21_mv_command():
    text = _script_text()
    assert 'mv "${APP_BUNDLE}/Contents/MacOS/_internal" "${APP_BUNDLE}/Contents/Resources/_internal"' in text, (
        "Step 2.1 must move _internal from Contents/MacOS/ to Contents/Resources/"
    )


def test_step21_symlink_command():
    text = _script_text()
    assert 'ln -s "../Resources/_internal" "${APP_BUNDLE}/Contents/MacOS/_internal"' in text, (
        "Step 2.1 must create symlink Contents/MacOS/_internal -> ../Resources/_internal"
    )


def test_step21_symlink_target():
    text = _script_text()
    # Symlink target must be ../Resources/_internal (relative, one level up)
    assert '"../Resources/_internal"' in text, (
        "Symlink target must be ../Resources/_internal (relative to Contents/MacOS/)"
    )


def test_step21_symlink_relative_not_absolute():
    text = _script_text()
    # ln -s line must NOT use an absolute path as target
    ln_lines = [line for line in text.splitlines() if line.strip().startswith("ln -s")]
    for line in ln_lines:
        if "_internal" in line:
            # extract the first argument to ln -s
            parts = line.strip().split()
            # parts: ["ln", "-s", "<target>", "<link>"]
            if len(parts) >= 3:
                target = parts[2].strip('"')
                assert not target.startswith("/"), (
                    f"Symlink target must be relative, got absolute: {target!r}"
                )


# ---------------------------------------------------------------------------
# Step 3.1 — .dist-info removal path
# ---------------------------------------------------------------------------

def test_step31_uses_resources_path():
    text = _script_text()
    assert 'find "${APP_BUNDLE}/Contents/Resources/_internal" -type d -name "*.dist-info"' in text, (
        "Step 3.1 find command must target Contents/Resources/_internal"
    )


def test_step31_no_macos_path():
    text = _script_text()
    # The dist-info removal must NOT reference MacOS/_internal
    dist_info_pattern = re.compile(
        r'find\s+"?\$\{APP_BUNDLE\}/Contents/MacOS/_internal"?.*dist-info'
    )
    assert not dist_info_pattern.search(text), (
        "Step 3.1 .dist-info removal must NOT reference Contents/MacOS/_internal"
    )


# ---------------------------------------------------------------------------
# Step 3.2 — removed
# ---------------------------------------------------------------------------

def test_step32_removed():
    text = _script_text()
    assert "Step 3.2" not in text, (
        "Step 3.2 (FIX-062 per-file relocation block) must be removed entirely"
    )


def test_step32_ts_logo_loop_gone():
    text = _script_text()
    # The for-loop over TS-Logo files should not exist
    assert "for f in TS-Logo.png TS-Logo.ico" not in text, (
        "FIX-062 per-file TS-Logo loop must be removed"
    )


# ---------------------------------------------------------------------------
# Step 3.5 — signing paths use Contents/Resources/_internal
# ---------------------------------------------------------------------------

def test_step35_dylib_signs_resources():
    text = _script_text()
    assert 'find "${APP_BUNDLE}/Contents/Resources/_internal" -name "*.dylib"' in text, (
        "Step 3.5 must sign .dylib files from Contents/Resources/_internal"
    )


def test_step35_so_signs_resources():
    text = _script_text()
    assert 'find "${APP_BUNDLE}/Contents/Resources/_internal" -name "*.so"' in text, (
        "Step 3.5 must sign .so files from Contents/Resources/_internal"
    )


def test_step35_framework_condition_resources():
    text = _script_text()
    assert '[ -d "${APP_BUNDLE}/Contents/Resources/_internal/Python.framework" ]' in text, (
        "Python.framework existence check must reference Contents/Resources/_internal"
    )


def test_step35_framework_sign_resources():
    text = _script_text()
    assert '"${APP_BUNDLE}/Contents/Resources/_internal/Python.framework"' in text, (
        "Python.framework signing path must reference Contents/Resources/_internal"
    )


# ---------------------------------------------------------------------------
# Verification step — Contents/Resources/_internal
# ---------------------------------------------------------------------------

def test_verify_framework_resources():
    text = _script_text()
    # The verification codesign --verify --deep line must use Resources path
    verify_pattern = re.compile(
        r'codesign\s+--verify\s+--deep\s+"?\$\{APP_BUNDLE\}/Contents/Resources/_internal/Python\.framework"?'
    )
    assert verify_pattern.search(text), (
        "Python.framework verification must reference Contents/Resources/_internal"
    )


# ---------------------------------------------------------------------------
# Comprehensive: no signing/verify step references MacOS/_internal
# ---------------------------------------------------------------------------

def test_no_signing_path_macos_internal():
    text = _script_text()
    lines = text.splitlines()

    # Signing/verification keywords
    signing_keywords = ("codesign", "find", "--sign", "--verify")

    forbidden: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        is_signing_line = any(kw in stripped for kw in signing_keywords)
        has_macos_internal = "Contents/MacOS/_internal" in line
        # The mv and ln -s lines are allowed to reference MacOS/_internal
        is_relocation_line = stripped.startswith("mv ") or stripped.startswith("ln -s ")
        if is_signing_line and has_macos_internal and not is_relocation_line:
            forbidden.append(f"  Line {lineno}: {line.rstrip()}")

    assert not forbidden, (
        "Signing/verification steps must NOT reference Contents/MacOS/_internal:\n"
        + "\n".join(forbidden)
    )
