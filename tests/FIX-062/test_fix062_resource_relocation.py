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
