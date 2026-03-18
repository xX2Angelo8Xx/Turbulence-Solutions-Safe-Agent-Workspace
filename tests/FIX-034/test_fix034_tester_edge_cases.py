"""FIX-034 — Tester edge-case tests.

Security and boundary cases not covered by the Developer's test suite (TST-2001
to TST-2094).  Each test targets a distinct bypass vector or edge condition
identified during Tester security review.

Test IDs: TST-2095 to TST-2110
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "Default-Project", ".github", "hooks", "scripts",
    )
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

WS = "c:/workspace"


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


def allow(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ===========================================================================
# TST-2095: Chain — venv ALLOW + rm -rf / DENY
# Verifies that the venv bypass only whitelist the activation segment; the
# subsequent destructive command is still zone-denied by Stage 4.
# ===========================================================================

def test_chained_venv_then_rm_rf_root_denied():
    """TST-2095: source .venv/bin/activate ; rm -rf / → deny (/ is outside project)."""
    assert deny("source .venv/bin/activate ; rm -rf /")


# ===========================================================================
# TST-2096: Chain — venv ALLOW + Invoke-Expression DENY
# Invoke-Expression (P-12) is the long-form of iex; distinct from TST-2062
# which only tested the short-form `iex`.
# ===========================================================================

def test_chained_venv_then_invoke_expression_denied():
    """TST-2096: & .venv/Scripts/Activate.ps1 ; Invoke-Expression 'malicious' → deny."""
    assert deny('& .venv/Scripts/Activate.ps1 ; Invoke-Expression "malicious"')


# ===========================================================================
# TST-2097: Path traversal — ../../ prefix escapes workspace root
# The venv regex matches ../../.venv/bin/activate (regex allows any non-
# whitespace directory prefix).  Zone classifier resolves the traversal to
# outside the workspace and must deny.
# ===========================================================================

def test_path_traversal_double_dotdot_denied():
    """TST-2097: source ../../.venv/bin/activate → deny (traversal escapes workspace)."""
    assert deny("source ../../.venv/bin/activate")


def test_path_traversal_double_dotdot_ampersand_denied():
    """TST-2097b: & ../../.venv/Scripts/Activate.ps1 → deny (traversal, PS form)."""
    assert deny("& ../../.venv/Scripts/Activate.ps1")


# ===========================================================================
# TST-2098: Unicode right-to-left override in venv path
# U+202E (RLO) inserted after .venv breaks the regex separator match so the
# segment falls through to Stage 3 where P-22 (source\s+) fires.
# ===========================================================================

def test_unicode_rlo_in_venv_path_denied():
    """TST-2098: source .venv\u202e/bin/activate → deny (RLO breaks regex, P-22 fires)."""
    assert deny("source .venv\u202e/bin/activate")


# ===========================================================================
# TST-2099: Whitespace padding around the activation command
# The code strips each segment before regex matching; the regex uses \s+ for
# the prefix gap, so extra internal spaces must also be tolerated.
# ===========================================================================

def test_leading_trailing_whitespace_allowed():
    """TST-2099a: '  source .venv/bin/activate  ' → allow (strip normalises)."""
    assert allow("  source .venv/bin/activate  ")


def test_multiple_internal_spaces_allowed():
    """TST-2099b: 'source   .venv/bin/activate' (3 spaces) → allow (\\s+ matches)."""
    assert allow("source   .venv/bin/activate")


# ===========================================================================
# TST-2100: Non-venv .ps1 — & ./malicious.ps1 must NOT be whitelisted
# The regex requires the literal string 'venv' (with optional leading dot) in
# the path; an arbitrary .ps1 file must not slip through.
# ===========================================================================

def test_non_venv_arbitrary_ps1_denied():
    """TST-2100: & ./malicious.ps1 → deny (not matched by venv regex; & not in allowlist)."""
    assert deny("& ./malicious.ps1")


def test_non_venv_scripts_arbitrary_ps1_denied():
    """TST-2100b: & project/scripts/setup.ps1 → deny (not a venv path)."""
    assert deny("& project/scripts/setup.ps1")


# ===========================================================================
# TST-2101: bin/activate.ps1 — wrong file extension for POSIX path
# The regex pattern for bin/ only allows bare 'activate' (no extension).
# source .venv/bin/activate.ps1 must NOT be whitelisted; P-22 must fire.
# ===========================================================================

def test_bin_activate_ps1_not_whitelisted_denied():
    """TST-2101: source .venv/bin/activate.ps1 → deny (not valid venv path; P-22 fires)."""
    assert deny("source .venv/bin/activate.ps1")


# ===========================================================================
# TST-2102: Double same-form activation
# When both segments are identical 'source .venv/bin/activate', the
# _venv_seg_indices set covers all segments → immediate allow.
# ===========================================================================

def test_double_same_form_activation_allowed():
    """TST-2102: source .venv/bin/activate ; source .venv/bin/activate → allow."""
    assert allow("source .venv/bin/activate ; source .venv/bin/activate")


# ===========================================================================
# TST-2103: Pipe to Invoke-Expression (single pipe, not a chain separator)
# _split_segments only splits on ;, &&, ||.  A bare | is NOT a segment
# separator.  Therefore '& .venv/Scripts/Activate.ps1 | Invoke-Expression'
# is ONE segment, the venv regex fails (trailing | ... text breaks \s*$),
# and Stage 3 obfuscation scan catches Invoke-Expression (P-12).
# ===========================================================================

def test_pipe_invoke_expression_after_venv_denied():
    """TST-2103: '& .venv/Scripts/Activate.ps1 | Invoke-Expression' → deny (P-12 via Stage 3)."""
    assert deny("& .venv/Scripts/Activate.ps1 | Invoke-Expression")


# ===========================================================================
# TST-2104: Null byte injected into venv path
# Zero-byte (\x00) inside a path has no valid use.  Normalize_path strips
# C0 control characters (\x00-\x1f), so .venv\x00/bin/activate becomes
# .venv/bin/activate after stripping — NOT before — the regex sees it raw.
# The raw regex match fails (\x00 is not [/\\]) so P-22 fires via Stage 3.
# ===========================================================================

def test_null_byte_in_venv_path_denied():
    """TST-2104: source .venv\\x00/bin/activate → deny (null byte breaks separator in regex)."""
    assert deny("source .venv\x00/bin/activate")


# ===========================================================================
# TST-2105: Venv-like name with extra suffix — venv2, .venv_project
# The regex requires the literal word 'venv' immediately followed by a
# separator; 'venv2' or '.venv_project' must NOT be matched.
# ===========================================================================

def test_venv_with_numeric_suffix_not_whitelisted():
    """TST-2105a: source .venv2/bin/activate → deny (venv2 not matched by \\.?venv[/\\\\])."""
    assert deny("source .venv2/bin/activate")


def test_venv_with_underscore_suffix_not_whitelisted():
    """TST-2105b: source .venv_project/bin/activate → deny."""
    assert deny("source .venv_project/bin/activate")


# ===========================================================================
# TST-2106: Activation outside project — absolute Windows-style path
# Even when the path follows the venv naming convention exactly, activation
# from outside the workspace root must be denied.
# ===========================================================================

def test_absolute_windows_path_outside_workspace_denied():
    """TST-2106: & C:/evil/.venv/Scripts/Activate.ps1 → deny (outside workspace)."""
    assert deny("& C:/evil/.venv/Scripts/Activate.ps1")


# ===========================================================================
# TST-2107: Venv regex does NOT match — confirm no false-positive for
# 'source' used on a regular file (P-22 must fire as intended).
# ===========================================================================

def test_source_regular_file_p22_fires():
    """TST-2107: source project/setup.sh → deny (P-22 fires; not a venv activation)."""
    assert deny("source project/setup.sh")
