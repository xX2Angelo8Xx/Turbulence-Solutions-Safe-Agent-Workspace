"""
Tests for FIX-062 — Fix macOS codesign TS-Logo.png failure

Updated after FIX-063 superseded Step 3.2:
  FIX-063 moves the entire _internal/ directory to Contents/Resources/ (Step 2.1).
  Step 3.2 (per-file TS-Logo relocation loop) was therefore removed entirely.

These tests now verify the ABSENCE of Step 3.2 and its associated constructs,
and verify that the FIX-063 Step 2.1 block is correctly in place.
"""

import os
import re

BUILD_SCRIPT = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "src", "installer", "macos", "build_dmg.sh"
)


def _read_script() -> str:
    with open(BUILD_SCRIPT, "r", encoding="utf-8", newline="") as f:
        return f.read()


def test_script_exists():
    """build_dmg.sh must exist at the expected path."""
    assert os.path.isfile(BUILD_SCRIPT), f"Expected script at {BUILD_SCRIPT}"


def test_no_crlf_line_endings():
    """build_dmg.sh must use LF line endings only (no CRLF)."""
    with open(BUILD_SCRIPT, "rb") as f:
        content = f.read()
    assert b"\r\n" not in content, "build_dmg.sh contains CRLF line endings"


def test_step_32_header_absent():
    """Step 3.2 header comment must NOT be present — superseded by FIX-063 Step 2.1."""
    content = _read_script()
    assert "Step 3.2" not in content, "Step 3.2 header comment still present in build_dmg.sh — should have been removed by FIX-063"


def test_step_32_moves_png_absent():
    """TS-Logo.png per-file mv must NOT be present — FIX-063 moves the whole _internal/ dir."""
    content = _read_script()
    assert "TS-Logo.png" not in content, (
        "TS-Logo.png still referenced in build_dmg.sh — FIX-063 should have removed the "
        "per-file relocation loop (Step 3.2)"
    )
    assert not re.search(
        r'mv\s+.*_internal.*\$\{f\}.*Contents/Resources',
        content
    ), "FIX-062 per-file mv ..._internal/${f} pattern must not exist after FIX-063"


def test_step_32_moves_ico_absent():
    """TS-Logo.ico per-file mv must NOT be present — FIX-063 removes the per-file loop."""
    content = _read_script()
    assert "TS-Logo.ico" not in content, (
        "TS-Logo.ico still referenced in build_dmg.sh — FIX-063 should have removed the "
        "per-file relocation loop (Step 3.2)"
    )


def test_step_32_symlink_command_present():
    """Step 3.2 must create a symlink via ln -s."""
    content = _read_script()
    assert "ln -s" in content, "ln -s symlink command not found in build_dmg.sh"


def test_step21_symlink_relative_path():
    """FIX-063 symlink target must use ../Resources/_internal (1 level up from MacOS/).

    The old FIX-062 path ../../Resources/<file> (2 levels up from _internal/) must
    not exist — FIX-063 symlinks the entire _internal/ directory from MacOS/ directly.
    """
    content = _read_script()
    # Old FIX-062 path (../../) must be absent
    assert not re.search(
        r'ln\s+-s\s+"?\.\.\/\.\.\/Resources\/',
        content
    ), "Old FIX-062 symlink path ../../Resources/ must not exist after FIX-063"
    # New FIX-063 path (../Resources/_internal) must be present
    assert re.search(
        r'ln\s+-s\s+"?\.\.\/Resources/_internal',
        content
    ), "FIX-063 symlink target ../Resources/_internal not found in build_dmg.sh"


def test_step_32_symlink_points_to_png_absent():
    """No symlink should point to a per-file TS-Logo path — removed by FIX-063."""
    content = _read_script()
    assert not re.search(
        r'ln\s+-s\s+"?\.\.\./\.\.\./Resources/.*"?\s+.*_internal/',
        content
    ), (
        "FIX-062 per-file symlink pattern (../../Resources/<file> -> _internal/<file>) "
        "must not exist after FIX-063"
    )


def test_step_32_loop_over_files_absent():
    """The FIX-062 per-file loop must NOT exist — removed by FIX-063."""
    content = _read_script()
    loop_match = re.search(
        r'for\s+f\s+in\s+TS-Logo\.png\s+TS-Logo\.ico',
        content
    )
    assert not loop_match, (
        "Loop 'for f in TS-Logo.png TS-Logo.ico' still found in build_dmg.sh — "
        "must be removed by FIX-063"
    )


def test_step_32_file_guard_absent():
    """The FIX-062 per-file [ -f .../${f} ] guard must NOT exist — removed by FIX-063."""
    content = _read_script()
    assert not re.search(
        r'\[\s+-f\s+.*_internal.*\$\{f\}',
        content
    ), (
        "FIX-062 file guard '[ -f .../${f}]' still present in build_dmg.sh — "
        "must be removed by FIX-063"
    )


def test_step_ordering_31_before_35():
    """Step 3.1 must appear before Step 3.5.  Step 3.2 must be absent (removed by FIX-063)."""
    content = _read_script()
    pos_31 = content.find("Step 3.1")
    pos_32 = content.find("Step 3.2")
    pos_35 = content.find("Step 3.5")
    assert pos_31 != -1, "Step 3.1 not found"
    assert pos_32 == -1, "Step 3.2 must not exist — it was removed by FIX-063"
    assert pos_35 != -1, "Step 3.5 not found"
    assert pos_31 < pos_35, "Step 3.1 must appear before Step 3.5"


def test_step_32_resources_dir_pre_exists():
    """The Resources directory is created in Step 2 (mkdir -p); Step 3.2 must not
    create it again (avoiding duplicate mkdir calls that could mask errors)."""
    content = _read_script()
    # Verify Contents/Resources is created in Step 2
    assert re.search(
        r'mkdir\s+-p\s+.*Contents/Resources',
        content
    ), "mkdir -p .../Contents/Resources not found — required before relocation"


def test_no_absolute_symlink_path():
    """Symlinks must use relative paths, not absolute paths starting with /."""
    content = _read_script()
    # Find all ln -s lines and verify none use an absolute path target
    ln_lines = [line for line in content.splitlines() if "ln -s" in line]
    for line in ln_lines:
        # Extract target (first argument after ln -s)
        m = re.search(r'ln\s+-s\s+"?(/[^"]+)', line)
        assert not m, f"Absolute symlink path found: {line.strip()}"


# ---------------------------------------------------------------------------
# Edge-case tests added by Tester Agent
# ---------------------------------------------------------------------------

def _extract_step21_block(content: str) -> str:
    """Return the text slice for the Step 2.1 section (FIX-063 _internal/ relocation)."""
    start = content.find("Step 2.1")
    # FIX-056 block immediately follows Step 2.1 in the script
    end = content.find("FIX-056")
    assert start != -1, "Step 2.1 marker not found"
    assert end != -1, "Section boundary after Step 2.1 (FIX-056 comment) not found"
    return content[start:end]


def test_for_loop_absent():
    """The FIX-062 TS-Logo for loop must no longer exist anywhere in the script."""
    content = _read_script()
    assert not re.search(r'for\s+f\s+in\s+TS-Logo', content), (
        "FIX-062 for-loop over TS-Logo files still present — must be removed by FIX-063"
    )


def test_ts_logo_if_guard_absent():
    """The FIX-062 if-guard for TS-Logo files must not exist in the script."""
    content = _read_script()
    # The guard checked for -f ...TS-Logo or the loop variable ${f}
    assert not re.search(r'\[\s+-f.*TS-Logo', content), (
        "FIX-062 '[ -f ...TS-Logo ]' guard still present — must be removed by FIX-063"
    )


def test_step21_uses_app_bundle_variable():
    """All path references in Step 2.1 (FIX-063) must use ${APP_BUNDLE}, not hardcoded paths."""
    block = _extract_step21_block(_read_script())
    assert "${APP_BUNDLE}" in block, \
        "Step 2.1 mv/ln commands must use ${APP_BUNDLE}, not hardcoded paths"


def test_echo_diagnostic_message_in_step21():
    """Step 2.1 (FIX-063) must produce a diagnostic echo so CI logs show what was relocated."""
    block = _extract_step21_block(_read_script())
    assert "echo" in block, \
        "Step 2.1 should include at least one diagnostic echo message for CI traceability"


def test_symlink_depth_exactly_one_level():
    """The FIX-063 _internal symlink must traverse exactly one directory level up (..).

    The symlink is placed at Contents/MacOS/_internal and points to ../Resources/_internal.
    From Contents/MacOS/:
      .. -> Contents/
    So ../Resources/_internal correctly resolves to Contents/Resources/_internal.
    A depth of 2 (../../Resources/) would be wrong — that was FIX-062's per-file path.
    """
    content = _read_script()
    ln_lines = [line.strip() for line in content.splitlines() if "ln -s" in line]
    assert ln_lines, "No ln -s lines found in build_dmg.sh"
    for line in ln_lines:
        m = re.search(r'ln\s+-s\s+"?([\./][^"\s]+)', line)
        if m:
            path = m.group(1)
            segments = path.split("/")
            dotdot_count = sum(1 for s in segments if s == "..")
            assert dotdot_count == 1, (
                f"Expected exactly 1 '..' segment in symlink path (FIX-063: "
                f"Contents/MacOS/ -> Contents/Resources/_internal), "
                f"got {dotdot_count}: {line}"
            )


def test_ts_logo_loop_and_guard_absent():
    """The FIX-062 TS-Logo loop and its [ -f ] guard must not exist — removed by FIX-063.

    FIX-063 moves the entire _internal/ directory so there is no need for a
    per-file loop or a missing-file guard for TS-Logo.png / TS-Logo.ico.
    """
    content = _read_script()
    loop_match = re.search(r'for\s+f\s+in\s+TS-Logo\.png\s+TS-Logo\.ico', content)
    guard_match = re.search(r'\[\s+-f\s+.*\$\{f\}', content)
    assert not loop_match, (
        "FIX-062 'for f in TS-Logo.png TS-Logo.ico' loop must be absent after FIX-063"
    )
    assert not guard_match, (
        "FIX-062 '[ -f ...${f}]' guard must be absent after FIX-063"
    )


def test_ts_logo_references_entirely_absent():
    """No TS-Logo.png or TS-Logo.ico reference must remain anywhere in the script.

    FIX-063 eliminates the need for per-file handling by relocating the whole
    _internal/ directory.  Any lingering TS-Logo reference would indicate an
    incomplete cleanup.
    """
    content = _read_script()
    assert "TS-Logo.png" not in content, (
        "TS-Logo.png reference still present in build_dmg.sh after FIX-063"
    )
    assert "TS-Logo.ico" not in content, (
        "TS-Logo.ico reference still present in build_dmg.sh after FIX-063"
    )


def test_mv_target_is_resources_dir():
    """The mv command must target the Resources/ directory, not MacOS/ or elsewhere."""
    content = _read_script()
    mv_matches = re.findall(r'mv\s+\S+\s+(\S+)', content)
    for target in mv_matches:
        # Only check mv targets that involve our relocated files
        if "Contents" in target:
            assert "Resources" in target, \
                f"mv target '{target}' does not place file in Contents/Resources/"


def test_step32_absent_in_raw_bytes():
    """Step 3.2 must not appear anywhere in the raw bytes of build_dmg.sh."""
    with open(BUILD_SCRIPT, "rb") as f:
        raw = f.read()
    assert b"Step 3.2" not in raw, (
        "Raw bytes of build_dmg.sh still contain 'Step 3.2' — must be removed by FIX-063"
    )
