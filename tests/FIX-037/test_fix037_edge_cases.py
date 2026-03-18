"""
Edge-case tests for FIX-037 — Tester additions.

Covers scenarios beyond the Developer's 6 baseline tests:
  - Multiple .dist-info directories handled via batch '+' form
  - .egg-info directories intentionally NOT targeted (out of scope)
  - Glob precision: '*.dist-info' must not match bare '.info' suffixes
  - -type d flag present (only directories, not files named *.dist-info)
  - Echo log statement present for CI visibility
  - APP_BUNDLE variable used (no hardcoded path)
  - Step 3.1 comment label present
  - Non-dist-info files in _internal/ are preserved by scope restriction
"""

import re
from pathlib import Path

BUILD_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "src" / "installer" / "macos" / "build_dmg.sh"
)


def _read_script() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Edge case 1: Batch '+' form handles multiple .dist-info dirs efficiently
# ---------------------------------------------------------------------------

def test_find_uses_batch_plus_form():
    """find must use '-exec rm -rf {} +' (batch form) not '{} \\;' (sequential).

    The '+' form passes all matching paths to a single rm invocation, making it
    safe and efficient when multiple .dist-info directories exist (e.g. after
    building a project with many pip-installed editable packages).
    """
    content = _read_script()
    # The dist-info find command must use + (batch) not \; (sequential)
    # Search in the relevant area of the script
    lines = content.splitlines()
    for line in lines:
        if '*.dist-info' in line and 'find' in line:
            assert '-exec rm -rf {} +' in line, (
                "find .dist-info must use '-exec rm -rf {} +' (batch form) for "
                "handling multiple directories; found in: " + line
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")


# ---------------------------------------------------------------------------
# Edge case 2: .egg-info directories explicitly NOT in scope of this fix
# ---------------------------------------------------------------------------

def test_egg_info_dirs_not_targeted_by_fix():
    """fix is scoped to .dist-info only — .egg-info must NOT be in the cleanup.

    .egg-info directories may exist for legacy packages; they are not part of
    BUG-070's scope. This test confirms the cleanup is intentionally narrow.
    Should .egg-info become a problem, a separate WP must be created.
    """
    content = _read_script()
    # Ensure the dist-info cleanup block does not reference .egg-info
    dist_info_section_start = content.find('Step 3.1')
    codesign_section_start = content.find('Step 3.5')

    assert dist_info_section_start != -1, "Step 3.1 section not found"
    assert codesign_section_start != -1, "Step 3.5 section not found"

    step_3_1_block = content[dist_info_section_start:codesign_section_start]
    assert '.egg-info' not in step_3_1_block, (
        "Step 3.1 cleanup block must not target .egg-info directories — "
        "those are out of scope for FIX-037 / BUG-070. Create a separate WP."
    )


# ---------------------------------------------------------------------------
# Edge case 3: Glob precision — '*.dist-info' must not match bare '.info'
# ---------------------------------------------------------------------------

def test_glob_is_precise_dist_info_not_bare_info():
    """The glob pattern '*.dist-info' correctly distinguishes from '*.info'.

    A pattern like '*.info' would be too broad and could match unrelated
    directories. The pattern must include the full '.dist-info' suffix.
    Confirmed by verifying the literal string '*.dist-info' appears in the
    find command (not '*.info' as a standalone pattern).
    """
    content = _read_script()
    lines = content.splitlines()
    for line in lines:
        if '*.dist-info' in line and 'find' in line:
            # Confirm the full pattern is used — not a shorter glob
            assert '"*.dist-info"' in line or "'*.dist-info'" in line, (
                "The .dist-info glob must be quoted: '*.dist-info' or \"*.dist-info\". "
                "Found in: " + line
            )
            # Confirm there is no bare *.info pattern beside it
            assert re.search(r'-name\s+"?\*\.dist-info"?', line) or \
                   re.search(r"-name\s+'?\*\.dist-info'?", line), (
                "find must use -name '*.dist-info' precisely. Found: " + line
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")


# ---------------------------------------------------------------------------
# Edge case 4: -type d flag ensures only DIRECTORIES are removed
# ---------------------------------------------------------------------------

def test_find_restricts_to_directories_only():
    """-type d flag must be present so only directories are matched.

    Without -type d, if a file were ever named 'something.dist-info', rm -rf
    would still work, but adding -type d makes the intent explicit and prevents
    unexpected matches against files.
    """
    content = _read_script()
    lines = content.splitlines()
    for line in lines:
        if '*.dist-info' in line and 'find' in line:
            assert '-type d' in line, (
                "find command must include '-type d' to restrict matches "
                "to directories only. Found: " + line
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")


# ---------------------------------------------------------------------------
# Edge case 5: Echo/log statement for CI visibility
# ---------------------------------------------------------------------------

def test_echo_statement_precedes_cleanup():
    """An echo statement must appear before or alongside the dist-info cleanup.

    CI logs must show explicit progress. The Developer added
    'echo \"==> Removing .dist-info directories from bundle...\"' which
    satisfies this requirement.
    """
    content = _read_script()
    dist_info_section_start = content.find('Step 3.1')
    codesign_section_start = content.find('Step 3.5')

    assert dist_info_section_start != -1, "Step 3.1 section not found"
    assert codesign_section_start != -1, "Step 3.5 section not found"

    step_3_1_block = content[dist_info_section_start:codesign_section_start]
    assert 'echo' in step_3_1_block and 'dist-info' in step_3_1_block.lower(), (
        "Step 3.1 block must contain an echo statement mentioning dist-info "
        "for CI log visibility"
    )


# ---------------------------------------------------------------------------
# Edge case 6: APP_BUNDLE variable used — no hardcoded path
# ---------------------------------------------------------------------------

def test_cleanup_uses_app_bundle_variable_not_hardcoded_path():
    """The find command must use the $APP_BUNDLE variable, not a hardcoded path.

    Hardcoded paths like 'dist/AgentEnvironmentLauncher.app/...' would break
    if APP_BUNDLE_NAME or DIST_DIR is ever changed. Using the variable ensures
    the cleanup always targets the correct bundle regardless of naming.
    """
    content = _read_script()
    lines = content.splitlines()
    for line in lines:
        if '*.dist-info' in line and 'find' in line:
            assert 'APP_BUNDLE' in line, (
                "find .dist-info command must reference the $APP_BUNDLE "
                "variable, not a hardcoded bundle path. Found: " + line
            )
            # Confirm it is NOT using a hardcoded 'dist/' path in the find
            assert not re.match(r'\s*find\s+"dist/', line.strip()), (
                "find command must not start with a hardcoded 'dist/' path. "
                "Use $APP_BUNDLE instead. Found: " + line
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")


# ---------------------------------------------------------------------------
# Edge case 7: Step 3.1 comment label present in the script
# ---------------------------------------------------------------------------

def test_step_3_1_comment_label_present():
    """The cleanup step must be labeled 'Step 3.1' in a comment.

    Consistent step numbering makes it clear to future developers that this
    step falls between Info.plist creation (Step 3) and code signing (Step 3.5).
    """
    content = _read_script()
    assert 'Step 3.1' in content, (
        "build_dmg.sh must contain a 'Step 3.1' comment label for the "
        ".dist-info cleanup step to maintain consistent step numbering"
    )


# ---------------------------------------------------------------------------
# Edge case 8: Placement relative to Info.plist (must be AFTER Step 3)
# ---------------------------------------------------------------------------

def test_cleanup_is_after_info_plist_step():
    """The .dist-info cleanup must appear AFTER the Info.plist write (Step 3).

    Removing .dist-info before the bundle is fully assembled could fail because
    _internal/ may not yet exist. The correct order is:
    Step 3 (write Info.plist) → Step 3.1 (remove .dist-info) → Step 3.5 (sign).
    """
    content = _read_script()
    info_plist_match = re.search(r'Step 3:', content)
    dist_info_match = re.search(r'find\b.*\*\.dist-info', content)
    codesign_match = re.search(r'Step 3\.5', content)

    assert info_plist_match is not None, "Step 3 (Info.plist) section not found"
    assert dist_info_match is not None, "find *.dist-info command not found"
    assert codesign_match is not None, "Step 3.5 (code signing) section not found"

    assert info_plist_match.start() < dist_info_match.start() < codesign_match.start(), (
        "Step ordering must be: Step 3 (Info.plist) < Step 3.1 (dist-info removal) "
        f"< Step 3.5 (codesign). Got positions: "
        f"Step3={info_plist_match.start()}, "
        f"dist-info={dist_info_match.start()}, "
        f"Step3.5={codesign_match.start()}"
    )


# ---------------------------------------------------------------------------
# Edge case 9: The cleanup does not affect the DMG creation step (Step 4)
# ---------------------------------------------------------------------------

def test_cleanup_does_not_reference_staging_dir():
    """The dist-info cleanup must target APP_BUNDLE, never the STAGING_DIR.

    STAGING_DIR is created as a clean copy for hdiutil; by the time hdiutil
    runs, the cleanup has already happened at the APP_BUNDLE level. This test
    verifies the find command does NOT target STAGING_DIR (which would be a
    timing bug — STAGING_DIR doesn't exist yet when Step 3.1 runs).
    """
    content = _read_script()
    lines = content.splitlines()
    for line in lines:
        if '*.dist-info' in line and 'find' in line:
            assert 'STAGING_DIR' not in line, (
                "The .dist-info cleanup must NOT target STAGING_DIR — it "
                "runs before STAGING_DIR is created. Use APP_BUNDLE instead. "
                "Found: " + line
            )
            return
    raise AssertionError("find *.dist-info command not found in build_dmg.sh")


# ---------------------------------------------------------------------------
# Edge case 10: Script set -euo pipefail is still present (safety regression)
# ---------------------------------------------------------------------------

def test_strict_mode_still_active():
    """set -euo pipefail must remain active after the FIX-037 changes.

    The '|| true' on the dist-info find is intentional (handles no-match case).
    But the enclosing script's strict mode must not have been accidentally
    removed or weakened.
    """
    content = _read_script()
    assert 'set -euo pipefail' in content, (
        "build_dmg.sh must retain 'set -euo pipefail' strict mode; "
        "FIX-037 changes must not have accidentally removed it"
    )
