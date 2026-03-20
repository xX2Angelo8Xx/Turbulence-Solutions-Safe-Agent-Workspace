"""
Tests for FIX-062 — Fix macOS codesign TS-Logo.png failure

Regression tests that verify build_dmg.sh contains the correct Step 3.2
resource-relocation block, including:
  - Presence of the relocation step
  - Correct mv and ln -s commands
  - Correct relative symlink path (../../Resources/<filename>)
  - Step ordering (3.2 appears after 3.1 and before 3.5)
  - LF line endings (no CRLF introduced)
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


def test_step_32_header_present():
    """Step 3.2 header comment must be present in the script."""
    content = _read_script()
    assert "Step 3.2" in content, "Step 3.2 header comment not found in build_dmg.sh"


def test_step_32_moves_png():
    """Step 3.2 must move TS-Logo.png to Contents/Resources/."""
    content = _read_script()
    assert "TS-Logo.png" in content, "TS-Logo.png not mentioned in Step 3.2"
    # The mv command uses the loop variable ${f}; it must move from _internal/ to Resources/
    assert re.search(
        r'mv\s+.*_internal.*\$\{f\}.*Contents/Resources',
        content
    ), "mv ..._internal/${f} -> Contents/Resources/${f} pattern not found"


def test_step_32_moves_ico():
    """Step 3.2 must move TS-Logo.ico to Contents/Resources/."""
    content = _read_script()
    assert "TS-Logo.ico" in content, "TS-Logo.ico not mentioned in Step 3.2"


def test_step_32_symlink_command_present():
    """Step 3.2 must create a symlink via ln -s."""
    content = _read_script()
    assert "ln -s" in content, "ln -s symlink command not found in build_dmg.sh"


def test_step_32_symlink_relative_path():
    """Symlink target must use the correct relative path ../../Resources/<filename>."""
    content = _read_script()
    assert re.search(
        r'ln\s+-s\s+"?\.\.\/\.\.\/Resources\/',
        content
    ), "Symlink does not use relative path ../../Resources/"


def test_step_32_symlink_points_to_png():
    """Symlink for TS-Logo.png must point to ../../Resources/TS-Logo.png."""
    content = _read_script()
    # The ln -s line must reference ../../Resources/${f} or ../../Resources/TS-Logo.png
    assert re.search(
        r'ln\s+-s\s+"?\.\./\.\./Resources/.*"?\s+.*_internal/',
        content
    ), "ln -s for Resources/<filename> -> _internal/<filename> pattern not found"


def test_step_32_loop_over_files():
    """Step 3.2 must use a loop covering both TS-Logo.png and TS-Logo.ico."""
    content = _read_script()
    # The loop variable 'f' should iterate over both files
    loop_match = re.search(
        r'for\s+f\s+in\s+TS-Logo\.png\s+TS-Logo\.ico',
        content
    )
    assert loop_match, "Loop 'for f in TS-Logo.png TS-Logo.ico' not found in Step 3.2"


def test_step_32_guarded_by_file_check():
    """Each relocation must be guarded by [ -f ... ] to avoid errors on missing files."""
    content = _read_script()
    assert re.search(
        r'\[\s+-f\s+.*_internal.*\$\{f\}',
        content
    ), "File-existence guard '[ -f .../${f} ]' not found in Step 3.2"


def test_step_ordering_31_before_32_before_35():
    """Step 3.1 must appear before Step 3.2 which must appear before Step 3.5."""
    content = _read_script()
    pos_31 = content.find("Step 3.1")
    pos_32 = content.find("Step 3.2")
    pos_35 = content.find("Step 3.5")
    assert pos_31 != -1, "Step 3.1 not found"
    assert pos_32 != -1, "Step 3.2 not found"
    assert pos_35 != -1, "Step 3.5 not found"
    assert pos_31 < pos_32, "Step 3.1 must appear before Step 3.2"
    assert pos_32 < pos_35, "Step 3.2 must appear before Step 3.5"


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

def _extract_step32_block(content: str) -> str:
    """Return the text slice between 'Step 3.2' and 'Step 3.5' headers."""
    start = content.find("Step 3.2")
    end = content.find("Step 3.5")
    assert start != -1, "Step 3.2 marker not found"
    assert end != -1, "Step 3.5 marker not found"
    return content[start:end]


def test_for_loop_has_done():
    """The for loop in Step 3.2 must be closed with 'done' (syntax correctness)."""
    block = _extract_step32_block(_read_script())
    assert re.search(r'\bdone\b', block), \
        "for loop in Step 3.2 is not closed with 'done' — script would fail with syntax error"


def test_if_block_has_fi():
    """The if block inside the Step 3.2 loop must be closed with 'fi'."""
    block = _extract_step32_block(_read_script())
    if_count = len(re.findall(r'\bif\b', block))
    fi_count = len(re.findall(r'\bfi\b', block))
    assert fi_count >= 1, "No 'fi' found to close the if block in Step 3.2"
    assert if_count == fi_count, \
        f"Unmatched if/fi in Step 3.2: {if_count} 'if' but {fi_count} 'fi'"


def test_step_32_uses_app_bundle_variable():
    """All path references in Step 3.2 must use ${APP_BUNDLE}, not hardcoded paths."""
    block = _extract_step32_block(_read_script())
    assert "${APP_BUNDLE}" in block, \
        "Step 3.2 mv/ln commands must use ${APP_BUNDLE}, not hardcoded paths"


def test_echo_diagnostic_message_in_step_32():
    """Step 3.2 must produce a diagnostic echo so CI logs show what was relocated."""
    block = _extract_step32_block(_read_script())
    assert "echo" in block, \
        "Step 3.2 should include at least one diagnostic echo message for CI traceability"


def test_symlink_depth_exactly_two_levels():
    """The relative symlink must traverse exactly two directory levels up (../../).

    From Contents/MacOS/_internal/:
      .. -> Contents/MacOS/
      ../.. -> Contents/
    So ../../Resources/<file> correctly resolves to Contents/Resources/<file>.
    A depth of 1 (../Resources/) or 3 (../../../Resources/) would be wrong.
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
            assert dotdot_count == 2, (
                f"Expected exactly 2 '..' segments in symlink path (needed for "
                f"Contents/MacOS/_internal/ -> Contents/Resources/), "
                f"got {dotdot_count}: {line}"
            )


def test_loop_guard_prevents_abort_on_single_missing_file():
    """The [ -f ... ] guard ensures the loop doesn't error when only one file is present.

    If TS-Logo.ico is absent but TS-Logo.png is present (or vice versa), the
    script must continue without error. The guard must be inside the loop body,
    not wrapping the entire loop.
    """
    block = _extract_step32_block(_read_script())
    # The for-loop line and the if-guard must both be present inside the block
    loop_match = re.search(r'for\s+f\s+in\s+TS-Logo\.png\s+TS-Logo\.ico', block)
    guard_match = re.search(r'\[\s+-f\s+.*\$\{f\}', block)
    assert loop_match, "for f in TS-Logo.png TS-Logo.ico loop not found in Step 3.2"
    assert guard_match, "[ -f ...${f} ] guard not found inside Step 3.2 loop"
    # The guard must appear AFTER the for-loop line (i.e., inside the loop body)
    assert block.find(guard_match.group(0)) > block.find(loop_match.group(0)), \
        "[ -f ] guard must appear inside the for loop body, not before it"


def test_loop_handles_neither_file_present():
    """When neither TS-Logo.png nor TS-Logo.ico exists the loop must not fail.

    This is ensured by the [ -f ] guard combined with 'set -euo pipefail' at the
    top of the script: if the guard always fires, mv/ln are never called on missing
    files. Verify the script does NOT have a mandatory-exit clause for missing files
    outside of the guard.
    """
    block = _extract_step32_block(_read_script())
    # There must be no unconditional 'exit 1' or '|| exit 1' outside an if block
    lines_with_exit = [
        ln.strip() for ln in block.splitlines()
        if re.search(r'exit\s+1', ln) and "if" not in ln
    ]
    assert not lines_with_exit, (
        f"Step 3.2 has unconditional exit statements that would abort "
        f"when files are absent: {lines_with_exit}"
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


def test_no_crlf_in_step32_block():
    """Step 3.2 lines must not contain carriage-return characters (CRLF check)."""
    with open(BUILD_SCRIPT, "rb") as f:
        raw = f.read()
    # Find the byte range for Step 3.2
    step32_pos = raw.find(b"Step 3.2")
    step35_pos = raw.find(b"Step 3.5")
    assert step32_pos != -1
    assert step35_pos != -1
    step32_bytes = raw[step32_pos:step35_pos]
    assert b"\r\n" not in step32_bytes, \
        "Step 3.2 block contains CRLF line endings — must be LF only"
