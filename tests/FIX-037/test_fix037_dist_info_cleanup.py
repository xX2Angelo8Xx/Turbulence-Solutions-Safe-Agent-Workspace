"""
Tests for FIX-037: Remove .dist-info dirs from macOS bundle before signing.

Verifies that build_dmg.sh contains the correct cleanup step to remove
.dist-info directories before code signing, addressing BUG-070.
"""

import re
from pathlib import Path

BUILD_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "src" / "installer" / "macos" / "build_dmg.sh"
)


def _read_script() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


def test_script_contains_dist_info_find_command():
    """build_dmg.sh must contain a find command that targets *.dist-info directories."""
    content = _read_script()
    assert re.search(r'find\b.*\*\.dist-info', content), (
        "build_dmg.sh must contain a find command targeting *.dist-info directories"
    )


def test_dist_info_removal_before_codesign():
    """The .dist-info cleanup step must appear BEFORE the Step 3.5 code signing section."""
    content = _read_script()
    dist_info_match = re.search(r'find\b.*\*\.dist-info', content)
    codesign_step_match = re.search(r'Step 3\.5', content)

    assert dist_info_match is not None, "find *.dist-info command not found in script"
    assert codesign_step_match is not None, "Step 3.5 code signing section not found in script"
    assert dist_info_match.start() < codesign_step_match.start(), (
        ".dist-info removal must appear before Step 3.5 code signing, "
        f"but removal is at position {dist_info_match.start()} and "
        f"codesign step is at position {codesign_step_match.start()}"
    )


def test_removal_targets_internal_directory():
    """The find command must specifically target the _internal directory."""
    content = _read_script()
    # The cleanup command must reference _internal in the find path
    assert re.search(r'find\b[^;]*_internal[^;]*\*\.dist-info', content), (
        "find command must target the _internal directory for .dist-info removal"
    )


def test_removal_uses_rm_rf():
    """The cleanup command must use rm -rf for directory removal."""
    content = _read_script()
    # The find ... -exec rm -rf pattern must be present near the dist-info find
    dist_info_section = re.search(
        r'find\b[^\n]*_internal[^\n]*\*\.dist-info[^\n]*(?:\\\n[^\n]*)*',
        content
    )
    assert dist_info_section is not None, "find *.dist-info command not found"
    # Check that rm -rf appears in the find command invocation
    assert 'rm -rf' in dist_info_section.group(0), (
        "The .dist-info cleanup must use rm -rf for directory deletion"
    )


def test_codesign_steps_still_present():
    """All existing code signing steps must still be present (regression check)."""
    content = _read_script()

    expected_patterns = [
        r'codesign.*--sign\s+-',           # ad-hoc signing
        r'find.*\.dylib.*codesign',        # sign .dylib files
        r'find.*\.so.*codesign',           # sign .so files
        r'Python\.framework',              # Python.framework signing
        r'codesign.*--verify.*--deep.*--strict',  # verification step
    ]

    for pattern in expected_patterns:
        assert re.search(pattern, content), (
            f"Regression: expected pattern '{pattern}' not found in build_dmg.sh"
        )


def test_error_suppression_present():
    """The .dist-info cleanup must use 2>/dev/null || true for safe error suppression."""
    content = _read_script()
    # Find the line containing the dist-info find command
    for line in content.splitlines():
        if '*.dist-info' in line and 'find' in line:
            assert '2>/dev/null' in line, (
                "The .dist-info cleanup command must redirect stderr to /dev/null"
            )
            assert '|| true' in line, (
                "The .dist-info cleanup command must use || true to suppress errors"
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")
