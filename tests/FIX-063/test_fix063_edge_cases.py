"""
FIX-063 edge-case tests — Added by Tester Agent.

Verifies additional correctness properties of the _internal/ relocation:
  - Step 2.1 mv comes AFTER cp -R (bundle must exist first)
  - Step 2.1 mv comes BEFORE Step 3.1 (dist-info removal)
  - Step 2.1 mv comes BEFORE Step 3.5 (signing)
  - mkdir -p Contents/Resources precedes mv _internal (target dir must exist)
  - Symlink uses exactly 1 ".." segment (correct depth from Contents/MacOS/)
  - No Contents/MacOS/_internal reference outside mv + ln -s lines (comprehensive)
  - Diagnostic echo exists near Step 2.1 block
  - Python.framework existence guard uses Resources path
  - set -euo pipefail still set (mv failure would abort the script)
  - No TS-Logo.png or TS-Logo.ico references anywhere (fully superseded by dir relocation)
"""

import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[2] / "src" / "installer" / "macos" / "build_dmg.sh"


def _text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _lines():
    return _text().splitlines()


# ---------------------------------------------------------------------------
# Step ordering: cp -R → mv → Step 3.1 → Step 3.5
# ---------------------------------------------------------------------------

def test_step21_mv_after_cp_r():
    """mv _internal must appear AFTER the cp -R that populates Contents/MacOS/."""
    lines = _lines()
    cp_r_indices = [
        i for i, l in enumerate(lines)
        if l.strip().startswith("cp -R") and "MacOS" in l
    ]
    mv_indices = [
        i for i, l in enumerate(lines)
        if l.strip().startswith("mv ") and "_internal" in l
    ]
    assert cp_r_indices, "cp -R ... MacOS/ command not found"
    assert mv_indices, "mv _internal command not found"
    assert min(mv_indices) > min(cp_r_indices), (
        "Step 2.1 mv must come AFTER the cp -R that populates Contents/MacOS/"
    )


def test_step21_mv_before_step31():
    """mv _internal (Step 2.1) must appear BEFORE Step 3.1 (.dist-info removal)."""
    text = _text()
    mv_pos = text.find('mv "${APP_BUNDLE}/Contents/MacOS/_internal"')
    step31_pos = text.find("Step 3.1")
    assert mv_pos != -1, "mv _internal command not found"
    assert step31_pos != -1, "Step 3.1 not found"
    assert mv_pos < step31_pos, (
        "mv _internal must appear before Step 3.1"
    )


def test_step21_mv_before_step35():
    """mv _internal (Step 2.1) must appear BEFORE Step 3.5 (signing)."""
    text = _text()
    mv_pos = text.find('mv "${APP_BUNDLE}/Contents/MacOS/_internal"')
    step35_pos = text.find("Step 3.5")
    assert mv_pos != -1, "mv _internal command not found"
    assert step35_pos != -1, "Step 3.5 not found"
    assert mv_pos < step35_pos, (
        "mv _internal must appear before Step 3.5 (signing)"
    )


# ---------------------------------------------------------------------------
# Target directory must exist before mv
# ---------------------------------------------------------------------------

def test_mkdir_resources_before_mv_internal():
    """mkdir -p .../Contents/Resources must appear before the mv _internal command.
    If Resources/ doesn't exist, mv will fail."""
    lines = _lines()
    mkdir_indices = [
        i for i, l in enumerate(lines)
        if "mkdir" in l and "Contents/Resources" in l
    ]
    mv_indices = [
        i for i, l in enumerate(lines)
        if l.strip().startswith("mv ") and "_internal" in l
    ]
    assert mkdir_indices, "mkdir .../Contents/Resources not found — required before mv"
    assert mv_indices, "mv _internal command not found"
    assert min(mkdir_indices) < min(mv_indices), (
        "mkdir -p .../Contents/Resources must precede mv _internal "
        f"(mkdir at line(s) {mkdir_indices}, mv at line(s) {mv_indices})"
    )


# ---------------------------------------------------------------------------
# Symlink path depth: exactly 1 ".." from Contents/MacOS/ to Contents/
# ---------------------------------------------------------------------------

def test_symlink_one_dotdot_from_macos_dir():
    """The _internal symlink target ../Resources/_internal uses exactly 1 '..'
    segment — correct because MacOS/ is one level below Contents/.

    From Contents/MacOS/:
        ../  → Contents/
        ../Resources/_internal → Contents/Resources/_internal (correct)

    Two '..' would resolve to the parent of Contents/, which is wrong.
    """
    text = _text()
    ln_lines = [
        l.strip() for l in text.splitlines()
        if l.strip().startswith("ln -s") and "_internal" in l
    ]
    assert ln_lines, "No 'ln -s ... _internal' line found"
    for line in ln_lines:
        parts = line.split()
        # Expected: ["ln", "-s", '"../Resources/_internal"', '"${APP_BUNDLE}/.../_internal"']
        if len(parts) >= 3:
            target = parts[2].strip('"')
            dotdot_count = target.count("../")
            assert dotdot_count == 1, (
                f"Symlink target must have exactly 1 '../' segment (Contents/MacOS/ "
                f"is ONE level below Contents/). Got {dotdot_count} in: {line!r}"
            )


# ---------------------------------------------------------------------------
# Comprehensive: no Contents/MacOS/_internal outside mv + ln -s
# ---------------------------------------------------------------------------

def test_no_macos_internal_outside_relocation():
    """No line referencing Contents/MacOS/_internal should exist outside the
    mv and ln -s relocation commands in Step 2.1.

    All paths in signing/verification/dist-info steps must use Contents/Resources/.
    """
    lines = _lines()
    violations: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if "Contents/MacOS/_internal" not in line:
            continue
        stripped = line.strip()
        # Only the mv and ln -s lines are allowed to reference MacOS/_internal
        if stripped.startswith("mv ") or stripped.startswith("ln -s "):
            continue
        # Comment lines are informational — still flag because code in comments
        # could mislead future editors and should be accurate
        if stripped.startswith("#"):
            continue
        violations.append(f"  Line {lineno}: {line.rstrip()}")
    assert not violations, (
        "Contents/MacOS/_internal referenced outside the Step 2.1 relocation block:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Diagnostic echo in Step 2.1 block
# ---------------------------------------------------------------------------

def test_echo_in_step21_region():
    """At least one 'echo' diagnostic must be present in the Step 2.1 region
    so CI logs show the relocation happened."""
    text = _text()
    mv_pos = text.find('mv "${APP_BUNDLE}/Contents/MacOS/_internal"')
    # Search 800 chars around the mv command for an echo
    region_start = max(0, mv_pos - 200)
    region_end = min(len(text), mv_pos + 600)
    region = text[region_start:region_end]
    assert "echo" in region, (
        "No 'echo' diagnostic found near the Step 2.1 mv command — "
        "CI logs should confirm the relocation occurred"
    )


# ---------------------------------------------------------------------------
# set -euo pipefail still active
# ---------------------------------------------------------------------------

def test_pipefail_still_active():
    """'set -euo pipefail' must be present — if mv fails (e.g. _internal is
    missing), the build must abort rather than silently producing a broken bundle."""
    text = _text()
    assert "pipefail" in text, (
        "'set -euo pipefail' not found — a failed mv would silently continue, "
        "producing a broken .app bundle with _internal in the wrong location"
    )


# ---------------------------------------------------------------------------
# TS-Logo.png and TS-Logo.ico no longer referenced (FIX-062 superseded)
# ---------------------------------------------------------------------------

def test_ts_logo_png_not_referenced():
    """TS-Logo.png must NOT be referenced in build_dmg.sh.
    FIX-063 supersedes FIX-062: the entire _internal/ dir is moved, so there
    is no need to handle individual logo files separately."""
    text = _text()
    assert "TS-Logo.png" not in text, (
        "TS-Logo.png is still referenced in build_dmg.sh — "
        "FIX-063 should have eliminated per-file relocation entirely"
    )


def test_ts_logo_ico_not_referenced():
    """TS-Logo.ico must NOT be referenced in build_dmg.sh (same reason as above)."""
    text = _text()
    assert "TS-Logo.ico" not in text, (
        "TS-Logo.ico is still referenced in build_dmg.sh — "
        "FIX-063 should have eliminated per-file relocation entirely"
    )


# ---------------------------------------------------------------------------
# Python.framework existence guard uses Resources path (not MacOS/_internal)
# ---------------------------------------------------------------------------

def test_python_framework_sign_guard_resources():
    """The [ -d ... Python.framework ] signing guard must reference
    Contents/Resources/_internal, NOT Contents/MacOS/_internal."""
    text = _text()
    # Find all [ -d ... ] checks referencing Python.framework
    framework_guards = re.findall(
        r'\[\s+-d\s+"[^"]*Python\.framework"[^]]*\]',
        text
    )
    assert framework_guards, "No [ -d ... Python.framework ] guard found"
    for guard in framework_guards:
        assert "Contents/Resources/_internal" in guard, (
            f"Python.framework guard must reference Contents/Resources/_internal: {guard!r}"
        )
        assert "Contents/MacOS/_internal" not in guard, (
            f"Python.framework guard must NOT reference Contents/MacOS/_internal: {guard!r}"
        )


def test_python_framework_verify_guard_resources():
    """The [ -d ... Python.framework ] verify guard must reference
    Contents/Resources/_internal."""
    text = _text()
    lines = _lines()
    verify_block_start = text.find("Verify code signatures")
    assert verify_block_start != -1, "Verify block not found"
    verify_block = text[verify_block_start:]
    framework_guards = re.findall(
        r'\[\s+-d\s+"[^"]*Python\.framework"[^]]*\]',
        verify_block
    )
    assert framework_guards, "No [ -d ... Python.framework ] guard found in verify block"
    for guard in framework_guards:
        assert "Contents/Resources/_internal" in guard, (
            f"Python.framework verify guard must use Contents/Resources/_internal: {guard!r}"
        )
