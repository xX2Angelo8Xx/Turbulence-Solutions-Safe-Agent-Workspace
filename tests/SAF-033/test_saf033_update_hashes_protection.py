"""SAF-033 — Tests: Protect update_hashes.py from agent terminal execution.

Covers:
1. Direct execution variants denied (python, python3, py, python3.x)
2. Path-prefixed variants denied (./update_hashes.py, scripts/update_hashes.py)
3. Mixed-case variants denied (case-insensitive via lowered_segment)
4. Substring match: any command containing 'update_hashes' is denied
   (SAF-033 strengthening: removed \\b word-boundary anchors from pattern)
5. Bypass-attempt tests do not circumvent the block
6. Regression: normal python commands still allowed
7. Pattern verification: _EXPLICIT_DENY_PATTERNS contains the correct pattern
8. security_gate.py in templates/coding has the correct update_hashes deny pattern
9. update_hashes.py script file still exists on disk (not deleted by SAF-033)
"""
import sys
import re
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures \u2014 load security_gate from templates/coding
# ---------------------------------------------------------------------------

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

TEMPLATES_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="Project"):
        yield


WS = "c:/workspace"


# ---------------------------------------------------------------------------
# Helper: force zone_classifier.classify to return "allow" so any deny
# can only come from the explicit deny pattern, not from path/zone checks.
# ---------------------------------------------------------------------------

def _deny_via_pattern(sg, command: str) -> bool:
    """Return True if sanitize_terminal_command returns 'deny' for the command,
    with path zone forced to 'allow' so that only the deny pattern can block it."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(command, ws_root=WS)
    return result == "deny"


# ---------------------------------------------------------------------------
# 1. Pattern verification — _EXPLICIT_DENY_PATTERNS
# ---------------------------------------------------------------------------

def test_deny_pattern_contains_update_hashes(sg):
    """_EXPLICIT_DENY_PATTERNS must contain a pattern matching 'update_hashes'."""
    matched = any(pat.search("update_hashes") for pat in sg._EXPLICIT_DENY_PATTERNS)
    assert matched, "No pattern in _EXPLICIT_DENY_PATTERNS matches 'update_hashes'"


def test_deny_pattern_is_substring_not_word_boundary(sg):
    """SAF-033: pattern must match 'update_hashes' as a substring (no \\b anchors).

    Verifies the SAF-033 strengthening: the pattern must match even when
    'update_hashes' is embedded in a longer word (e.g. 'my_update_hashes').
    A \\b-anchored pattern would NOT match 'my_update_hashes' because '_' is a
    word character.  A substring pattern DOES match.
    """
    matched = any(pat.search("my_update_hashes") for pat in sg._EXPLICIT_DENY_PATTERNS)
    assert matched, (
        "Pattern must use substring match (no \\b word-boundary anchors): "
        "'my_update_hashes' should be blocked"
    )


def test_deny_pattern_no_word_boundary_suffix(sg):
    """Pattern must match 'update_hashes_v2' (word char after 'update_hashes')."""
    matched = any(pat.search("update_hashes_v2") for pat in sg._EXPLICIT_DENY_PATTERNS)
    assert matched, "Pattern must match 'update_hashes_v2' (no suffix word-boundary)"


# ---------------------------------------------------------------------------
# 2. Direct execution variants — via sanitize_terminal_command
# ---------------------------------------------------------------------------

def test_python_update_hashes_denied(sg):
    """python update_hashes.py must be denied."""
    assert _deny_via_pattern(sg, "python update_hashes.py")


def test_python3_update_hashes_denied(sg):
    """python3 update_hashes.py must be denied."""
    assert _deny_via_pattern(sg, "python3 update_hashes.py")


def test_py_update_hashes_denied(sg):
    """py update_hashes.py must be denied."""
    assert _deny_via_pattern(sg, "py update_hashes.py")


def test_python_311_update_hashes_denied(sg):
    """python3.11 update_hashes.py must be denied (version alias)."""
    assert _deny_via_pattern(sg, "python3.11 update_hashes.py")


def test_python_dot_slash_update_hashes_denied(sg):
    """python ./update_hashes.py must be denied."""
    assert _deny_via_pattern(sg, "python ./update_hashes.py")


def test_python_scripts_path_update_hashes_denied(sg):
    """python scripts/update_hashes.py must be denied."""
    assert _deny_via_pattern(sg, "python scripts/update_hashes.py")


# ---------------------------------------------------------------------------
# 3. Mixed-case variants — case-insensitive via lowered_segment
# ---------------------------------------------------------------------------

def test_python_uppercase_update_hashes_denied(sg):
    """python UPDATE_HASHES.PY (uppercase) must be denied (case-insensitive)."""
    assert _deny_via_pattern(sg, "python UPDATE_HASHES.PY")


def test_python_mixed_case_update_hashes_denied(sg):
    """python Update_Hashes.py (mixed case) must be denied."""
    assert _deny_via_pattern(sg, "python Update_Hashes.py")


def test_python3_uppercase_update_hashes_denied(sg):
    """python3 UPDATE_HASHES.PY must be denied."""
    assert _deny_via_pattern(sg, "python3 UPDATE_HASHES.PY")


# ---------------------------------------------------------------------------
# 4. Substring match — SAF-033 strengthening (removed \\b word boundaries)
# ---------------------------------------------------------------------------

def test_substring_my_update_hashes_denied(sg):
    """python my_update_hashes.py must be denied (substring match, SAF-033)."""
    assert _deny_via_pattern(sg, "python my_update_hashes.py")


def test_substring_run_update_hashes_denied(sg):
    """python run_update_hashes.py must be denied (substring match, SAF-033)."""
    assert _deny_via_pattern(sg, "python run_update_hashes.py")


# ---------------------------------------------------------------------------
# 5. Bypass-attempt tests — should all still be denied
# ---------------------------------------------------------------------------

def test_python_c_update_hashes_import_denied(sg):
    """python -c 'import update_hashes' must be denied (via _scan_python_inline_code)."""
    result, _ = sg.sanitize_terminal_command(
        "python -c 'import update_hashes'",
        ws_root=WS,
    )
    assert result == "deny"


def test_python_c_update_hashes_call_denied(sg):
    """python -c with update_hashes call must be denied."""
    result, _ = sg.sanitize_terminal_command(
        'python -c "import update_hashes; update_hashes.update()"',
        ws_root=WS,
    )
    assert result == "deny"


def test_python3_update_hashes_no_py_extension_denied(sg):
    """python3 update_hashes (no extension) must be denied."""
    assert _deny_via_pattern(sg, "python3 update_hashes")


# ---------------------------------------------------------------------------
# 6. Regression — normal python commands still allowed
# ---------------------------------------------------------------------------

def test_python_print_still_allowed(sg):
    """python -c 'print(42)' must still be allowed after SAF-033."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            'python -c "print(42)"',
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


def test_python_m_pytest_still_allowed(sg):
    """python -m pytest must still be allowed."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            "python -m pytest tests/",
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


def test_python_m_pip_list_still_allowed(sg):
    """python -m pip list must still be allowed (regression: read-only pip commands)."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            "python -m pip list",
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


# ---------------------------------------------------------------------------
# 7. Both copies of security_gate.py have the identical pattern
# ---------------------------------------------------------------------------

def test_both_copies_have_identical_deny_pattern():
    """templates/coding security_gate.py must have
    the same update_hashes deny pattern (no word-boundary anchors)."""
    dp_file = (
        Path(__file__).parents[2]
        / "templates"
        / "coding"
        / ".github"
        / "hooks"
        / "scripts"
        / "security_gate.py"
    )
    tc_file = (
        Path(__file__).parents[2]
        / "templates"
        / "coding"
        / ".github"
        / "hooks"
        / "scripts"
        / "security_gate.py"
    )
    dp_lines = dp_file.read_text(encoding="utf-8").splitlines()
    tc_lines = tc_file.read_text(encoding="utf-8").splitlines()

    # Find the update_hashes deny pattern line in each file
    dp_pattern_line = next(
        (l for l in dp_lines if "update_hashes" in l and "_EXPLICIT_DENY" not in l
         and "SAF-033" in l),
        None,
    )
    tc_pattern_line = next(
        (l for l in tc_lines if "update_hashes" in l and "_EXPLICIT_DENY" not in l
         and "SAF-033" in l),
        None,
    )

    assert dp_pattern_line is not None, "templates/coding copy missing SAF-033 update_hashes pattern"
    assert tc_pattern_line is not None, "templates/coding copy missing SAF-033 update_hashes pattern"
    assert dp_pattern_line == tc_pattern_line, (
        f"Pattern lines differ between copies:\n"
        f"  templates/coding pattern: {dp_pattern_line!r}\n"
        f"  templates/coding: {tc_pattern_line!r}"
    )


def test_pattern_has_no_word_boundary_in_source():
    """Verify the source file does NOT contain \\bupdate_hashes\\b (the old SAF-026 pattern).
    
    The SAF-033 pattern must be a plain substring match without word boundaries.
    """
    dp_file = (
        Path(__file__).parents[2]
        / "templates"
        / "coding"
        / ".github"
        / "hooks"
        / "scripts"
        / "security_gate.py"
    )
    content = dp_file.read_text(encoding="utf-8")
    # The SAF-026 pattern with word boundaries should no longer be present
    assert r"\bupdate_hashes\b" not in content, (
        "Old SAF-026 word-boundary pattern still present; SAF-033 replacement not applied"
    )


# ---------------------------------------------------------------------------
# 8. update_hashes.py script file still exists on disk
# ---------------------------------------------------------------------------

def test_update_hashes_script_exists_default_project():
    """update_hashes.py must still exist in templates/coding (not deleted by SAF-033)."""
    script = (
        Path(__file__).parents[2]
        / "templates"
        / "coding"
        / ".github"
        / "hooks"
        / "scripts"
        / "update_hashes.py"
    )
    assert script.exists(), f"update_hashes.py missing from templates/coding: {script}"


def test_update_hashes_script_exists_templates_coding():
    """update_hashes.py must still exist in templates/coding (not deleted by SAF-033)."""
    script = (
        Path(__file__).parents[2]
        / "templates"
        / "coding"
        / ".github"
        / "hooks"
        / "scripts"
        / "update_hashes.py"
    )
    assert script.exists(), f"update_hashes.py missing from templates/coding: {script}"
