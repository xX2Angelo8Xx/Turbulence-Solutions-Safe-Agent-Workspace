"""FIX-034 — Tests for venv activation in project folder.

Verifies that:
- Standard venv activation forms are ALLOWED when the .venv/venv directory
  is inside the project folder.
- Activation outside the project folder is DENIED.
- No false positives from obfuscation patterns (P-22 source, P-23 dot-source)
  on legitimate venv activation commands.
- The PowerShell call-operator form (& .venv/Scripts/Activate.ps1) is allowed.
- Chaining with malicious commands is still denied.
- `deactivate` shell builtin is allowed.

Addresses audit findings L8, L9 from Security Audit V2.0.0.
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
# TST-2001 to TST-2010: source form (bash / POSIX) — ALLOW
# ===========================================================================

def test_source_venv_project_relative():
    """TST-2001: source project/.venv/bin/activate -> allow."""
    assert allow("source project/.venv/bin/activate")


def test_source_venv_relative():
    """TST-2002: source .venv/bin/activate (relative, project fallback) -> allow."""
    assert allow("source .venv/bin/activate")


def test_source_venv_no_dot():
    """TST-2003: source venv/bin/activate -> allow via project fallback."""
    assert allow("source venv/bin/activate")


def test_source_dotless_venv_project_prefix():
    """TST-2004: source project/venv/bin/activate -> allow."""
    assert allow("source project/venv/bin/activate")


# ===========================================================================
# TST-2011 to TST-2020: PowerShell call-operator form — ALLOW
# ===========================================================================

def test_ampersand_activate_ps1_project():
    """TST-2011: & project/.venv/Scripts/Activate.ps1 -> allow."""
    assert allow("& project/.venv/Scripts/Activate.ps1")


def test_ampersand_activate_ps1_relative():
    """TST-2012: & .venv/Scripts/Activate.ps1 -> allow via fallback."""
    assert allow("& .venv/Scripts/Activate.ps1")


def test_ampersand_activate_ps1_backslash():
    """TST-2013: & project\\.venv\\Scripts\\Activate.ps1 (backslash) -> allow."""
    assert allow("& project\\.venv\\Scripts\\Activate.ps1")


def test_ampersand_activate_no_dot_venv():
    """TST-2014: & venv/Scripts/Activate.ps1 -> allow via fallback."""
    assert allow("& venv/Scripts/Activate.ps1")


def test_ampersand_activate_bat():
    """TST-2015: & .venv/Scripts/activate.bat -> allow."""
    assert allow("& .venv/Scripts/activate.bat")


def test_ampersand_activate_unix():
    """TST-2016: & .venv/bin/activate -> allow."""
    assert allow("& .venv/bin/activate")


# ===========================================================================
# TST-2021 to TST-2030: POSIX dot-source form — ALLOW
# ===========================================================================

def test_dot_source_with_space_activate():
    """TST-2021: '. .venv/Scripts/activate' (POSIX dot with space) -> allow."""
    assert allow(". .venv/Scripts/activate")


def test_dot_source_with_space_bin_activate():
    """TST-2022: '. .venv/bin/activate' -> allow."""
    assert allow(". .venv/bin/activate")


def test_dot_source_project_prefix():
    """TST-2023: '. project/.venv/bin/activate' -> allow."""
    assert allow(". project/.venv/bin/activate")


# ===========================================================================
# TST-2031 to TST-2040: Direct execution form — ALLOW
# ===========================================================================

def test_direct_activate_ps1_project():
    """TST-2031: project/.venv/Scripts/Activate.ps1 (direct) -> allow."""
    assert allow("project/.venv/Scripts/Activate.ps1")


def test_direct_activate_ps1_relative():
    """TST-2032: .venv/Scripts/Activate.ps1 -> allow via fallback."""
    assert allow(".venv/Scripts/Activate.ps1")


def test_direct_activate_bat_project():
    """TST-2033: project/.venv/Scripts/activate.bat -> allow."""
    assert allow("project/.venv/Scripts/activate.bat")


def test_direct_activate_bat_relative():
    """TST-2034: .venv/Scripts/activate.bat -> allow via fallback."""
    assert allow(".venv/Scripts/activate.bat")


def test_direct_activate_unix_project():
    """TST-2035: project/.venv/bin/activate -> allow."""
    assert allow("project/.venv/bin/activate")


def test_direct_activate_unix_relative():
    """TST-2036: .venv/bin/activate -> allow via fallback."""
    assert allow(".venv/bin/activate")


def test_direct_activate_backslash():
    """TST-2037: .\\Project\\.venv\\Scripts\\activate -> allow via project fallback."""
    assert allow(".\\Project\\.venv\\Scripts\\activate")


def test_direct_activate_case_insensitive():
    """TST-2038: project/.VENV/SCRIPTS/ACTIVATE.PS1 (uppercase) -> allow."""
    assert allow("project/.VENV/SCRIPTS/ACTIVATE.PS1")


# ===========================================================================
# TST-2041 to TST-2050: Activation OUTSIDE project folder — DENY
# ===========================================================================

def test_source_absolute_outside_deny():
    """TST-2041: source /outside/.venv/bin/activate -> deny."""
    assert deny("source /outside/.venv/bin/activate")


def test_ampersand_absolute_outside_deny():
    """TST-2042: & c:/evil/.venv/Scripts/Activate.ps1 -> deny."""
    assert deny("& c:/evil/.venv/Scripts/Activate.ps1")


def test_direct_absolute_outside_deny():
    """TST-2043: c:/evil/venv/Scripts/activate.bat -> deny."""
    assert deny("c:/evil/venv/Scripts/activate.bat")


def test_source_absolute_no_venv_outside_deny():
    """TST-2044: source /etc/passwd -> deny (not venv, P-22 fires)."""
    assert deny("source /etc/passwd")


# ===========================================================================
# TST-2051 to TST-2060: No false positives from obfuscation patterns
# ===========================================================================

def test_no_false_positive_p22_source():
    """TST-2051: source .venv/bin/activate must not be blocked by P-22 (source)."""
    # P-22: re.compile(r'\bsource\s+') would block this without FIX-034
    assert allow("source .venv/bin/activate")


def test_no_false_positive_p23_dot_source():
    """TST-2052: '. .venv/Scripts/activate' must not be blocked by P-23."""
    # P-23: re.compile(r'\.\s+\S') would block this without FIX-034
    assert allow(". .venv/Scripts/activate")


def test_no_false_positive_ampersand_not_blocked():
    """TST-2053: '& .venv/Scripts/Activate.ps1' must not be denied by unknown-verb path."""
    # Without FIX-034, verb '&' is not in allowlist → deny
    assert allow("& .venv/Scripts/Activate.ps1")


# ===========================================================================
# TST-2061 to TST-2070: Security — chaining with malicious commands
# ===========================================================================

def test_chained_venv_then_malicious_source_denied():
    """TST-2061: 'source .venv/bin/activate; source /etc/passwd' -> deny.
    The second segment's source(/etc/passwd) still triggers P-22."""
    assert deny("source .venv/bin/activate; source /etc/passwd")


def test_chained_venv_then_iex_denied():
    """TST-2062: venv activation then IEX -> deny (P-11 catches iex)."""
    assert deny("source .venv/bin/activate; iex(New-Object Net.WebClient)")


def test_chained_venv_then_python_allowed():
    """TST-2063: venv activation then python project command -> allow."""
    assert allow("source .venv/bin/activate; python project/app.py")


def test_chained_venv_activations_allowed():
    """TST-2064: Two chained activations (unusual but valid) -> allow."""
    assert allow("source .venv/bin/activate; & .venv/Scripts/Activate.ps1")


# ===========================================================================
# TST-2071 to TST-2080: deactivate command
# ===========================================================================

def test_deactivate_allowed():
    """TST-2071: 'deactivate' shell builtin -> allow."""
    assert allow("deactivate")


# ===========================================================================
# TST-2081 to TST-2090: Path separator variants
# ===========================================================================

def test_mixed_separators_allow():
    """TST-2081: project/.venv\\Scripts\\activate (mixed separators) -> allow."""
    assert allow("project/.venv\\Scripts\\activate")


def test_forward_slash_only_allow():
    """TST-2082: project/.venv/Scripts/activate.bat (forward slashes) -> allow."""
    assert allow("project/.venv/Scripts/activate.bat")


def test_backslash_only_relative():
    """TST-2083: .venv\\Scripts\\activate.bat -> allow via fallback."""
    assert allow(".venv\\Scripts\\activate.bat")


# ===========================================================================
# TST-2091: Verify regex constant is present
# ===========================================================================

def test_venv_activation_regex_exists():
    """TST-2091: _VENV_ACTIVATION_SEG_RE constant must exist in security_gate."""
    assert hasattr(sg, "_VENV_ACTIVATION_SEG_RE")
    import re
    assert isinstance(sg._VENV_ACTIVATION_SEG_RE, type(re.compile("")))


def test_venv_activation_regex_matches_source_form():
    """TST-2092: Regex matches 'source project/.venv/bin/activate'."""
    m = sg._VENV_ACTIVATION_SEG_RE.match("source project/.venv/bin/activate")
    assert m is not None
    assert "venv" in m.group("path").lower()


def test_venv_activation_regex_matches_ampersand_form():
    """TST-2093: Regex matches '& .venv/Scripts/Activate.ps1'."""
    m = sg._VENV_ACTIVATION_SEG_RE.match("& .venv/Scripts/Activate.ps1")
    assert m is not None


def test_venv_activation_regex_no_match_arbitrary():
    """TST-2094: Regex does NOT match 'source /etc/passwd'."""
    m = sg._VENV_ACTIVATION_SEG_RE.match("source /etc/passwd")
    assert m is None
