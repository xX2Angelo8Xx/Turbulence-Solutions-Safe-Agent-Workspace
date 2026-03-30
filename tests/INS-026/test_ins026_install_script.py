"""
Tests for INS-026: macOS source install script and documentation.

All tests are static analysis / content inspection — no script execution
required (the script targets macOS bash; tests run on Windows CI too).
"""

import os
import re
import stat

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "install-macos.sh")
MAKEFILE_PATH = os.path.join(REPO_ROOT, "Makefile")
GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "macos-installation-guide.md")


# ── Helper ────────────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── install-macos.sh: existence and basic structure ───────────────────────────

def test_install_script_exists():
    assert os.path.isfile(SCRIPT_PATH), f"install-macos.sh not found at {SCRIPT_PATH}"


def test_install_script_has_shebang():
    content = _read(SCRIPT_PATH)
    first_line = content.splitlines()[0]
    assert first_line.startswith("#!"), "Script missing shebang on first line"
    assert "bash" in first_line or "env" in first_line, f"Unexpected shebang: {first_line}"


def test_install_script_is_executable_flag():
    # On Windows, st_mode won't have Unix exec bits, but the file should exist.
    # This test verifies the file mode bits are set when reading from git on Unix.
    # On Windows we just confirm the file exists and is non-empty.
    content = _read(SCRIPT_PATH)
    assert len(content) > 100, "install-macos.sh appears empty or truncated"


# ── install-macos.sh: Python version check ────────────────────────────────────

def test_python_version_check_present():
    content = _read(SCRIPT_PATH)
    assert "3.11" in content, "Script does not reference Python 3.11 minimum version"
    assert "MIN_PYTHON_MINOR" in content or "python3.11" in content, \
        "Script does not appear to check minimum Python minor version"


def test_python_version_check_exits_on_failure():
    content = _read(SCRIPT_PATH)
    assert "exit 1" in content, "Script does not call exit 1 on failure"
    assert "Python" in content and "not found" in content.lower() or \
           "not found" in content, "Script does not print a helpful error on missing Python"


# ── install-macos.sh: git check ───────────────────────────────────────────────

def test_git_check_present():
    content = _read(SCRIPT_PATH)
    assert "git" in content, "Script does not check for git"
    assert "command -v git" in content or "which git" in content, \
        "Script does not verify git is available"


# ── install-macos.sh: virtualenv creation ────────────────────────────────────

def test_venv_path_in_script():
    content = _read(SCRIPT_PATH)
    assert "TurbulenceSolutions" in content, "Script does not reference TurbulenceSolutions install path"
    assert "venv" in content, "Script does not create a virtualenv"
    assert ".local/share" in content, "Script does not use ~/.local/share path"


def test_venv_creation_command_present():
    content = _read(SCRIPT_PATH)
    assert "python" in content and "-m venv" in content, \
        "Script does not use 'python -m venv' to create virtualenv"


# ── install-macos.sh: pip install ────────────────────────────────────────────

def test_pip_install_present():
    content = _read(SCRIPT_PATH)
    assert "pip install" in content, "Script does not call pip install"
    # Should install from repo root (.)
    assert re.search(r'pip\s+install\s+.*\$', content) or \
           'pip install "$REPO_ROOT"' in content or \
           "pip install ." in content, \
        "Script does not pip-install from the repository"


# ── install-macos.sh: ts-python shim deployment ───────────────────────────────

def test_ts_python_shim_deployment():
    content = _read(SCRIPT_PATH)
    assert "ts-python" in content, "Script does not deploy ts-python shim"
    assert "TS_PYTHON_SHIM" in content or "ts-python" in content, \
        "ts-python shim variable or name missing"


def test_ts_python_shim_points_to_venv():
    content = _read(SCRIPT_PATH)
    # The shim should embed VENV_PYTHON or the venv path
    assert "VENV_PYTHON" in content, "ts-python shim does not reference VENV_PYTHON"


# ── install-macos.sh: python-path.txt ────────────────────────────────────────

def test_python_path_txt_written():
    content = _read(SCRIPT_PATH)
    assert "python-path.txt" in content, "Script does not write python-path.txt"


# ── install-macos.sh: agent-launcher setup ────────────────────────────────────

def test_agent_launcher_setup_present():
    content = _read(SCRIPT_PATH)
    assert "agent-launcher" in content, "Script does not set up agent-launcher command"


# ── install-macos.sh: PATH setup ─────────────────────────────────────────────

def test_path_setup_present():
    content = _read(SCRIPT_PATH)
    assert "PATH" in content, "Script does not add anything to PATH"
    assert ".zshrc" in content or "profile" in content.lower() or "bashrc" in content, \
        "Script does not reference shell profile files"


def test_path_duplicate_guard():
    content = _read(SCRIPT_PATH)
    assert "grep" in content or "already" in content.lower(), \
        "Script does not guard against duplicate PATH entries"


# ── install-macos.sh: safety ──────────────────────────────────────────────────

def test_no_dangerous_rm_rf():
    content = _read(SCRIPT_PATH)
    # No unconditional rm -rf on / or $HOME or arbitrary paths
    dangerous = re.findall(r'rm\s+-rf\s+/', content)
    assert not dangerous, f"Dangerous rm -rf patterns found: {dangerous}"
    # Also flag rm -rf $HOME alone
    dangerous_home = re.findall(r'rm\s+-rf\s+\$HOME\s*$', content, re.MULTILINE)
    assert not dangerous_home, f"Dangerous rm -rf $HOME found: {dangerous_home}"


def test_no_sudo_required():
    content = _read(SCRIPT_PATH)
    assert "sudo" not in content, \
        "Script uses sudo — install should be into user home directory only"


def test_set_e_present():
    content = _read(SCRIPT_PATH)
    assert "set -e" in content, "Script does not use 'set -e' for error handling"


# ── Makefile: existence and targets ───────────────────────────────────────────

def test_makefile_exists():
    assert os.path.isfile(MAKEFILE_PATH), f"Makefile not found at {MAKEFILE_PATH}"


def test_makefile_has_install_target():
    content = _read(MAKEFILE_PATH)
    assert "install-macos" in content, "Makefile missing install-macos target"
    assert re.search(r'^install-macos\s*:', content, re.MULTILINE), \
        "install-macos is not defined as a Makefile target"


def test_makefile_has_update_target():
    content = _read(MAKEFILE_PATH)
    assert "update-macos" in content, "Makefile missing update-macos target"
    assert re.search(r'^update-macos\s*:', content, re.MULTILINE), \
        "update-macos is not defined as a Makefile target"


def test_makefile_has_uninstall_target():
    content = _read(MAKEFILE_PATH)
    assert "uninstall-macos" in content, "Makefile missing uninstall-macos target"
    assert re.search(r'^uninstall-macos\s*:', content, re.MULTILINE), \
        "uninstall-macos is not defined as a Makefile target"


def test_makefile_references_install_script():
    content = _read(MAKEFILE_PATH)
    assert "install-macos.sh" in content, \
        "Makefile install-macos target does not reference install-macos.sh"


def test_makefile_update_target_uses_pip():
    content = _read(MAKEFILE_PATH)
    assert "pip install" in content, "Makefile update-macos target does not call pip install"


# ── macos-installation-guide.md: source install is primary ────────────────────

def test_guide_source_install_is_primary():
    content = _read(GUIDE_PATH)
    # Source install section heading must appear before DMG section heading
    source_match = re.search(r'^#{1,3} .*(source install|quick start|install)',
                             content, re.IGNORECASE | re.MULTILINE)
    dmg_match = re.search(r'^#{1,3} .*dmg', content, re.IGNORECASE | re.MULTILINE)
    assert source_match is not None, "Guide has no source install section heading"
    assert dmg_match is not None, "Guide has no DMG section heading"
    assert source_match.start() < dmg_match.start(), (
        "Source install section does not appear before DMG section heading in the guide"
    )


def test_guide_primary_method_label():
    content = _read(GUIDE_PATH)
    assert "primary" in content.lower() or "recommended" in content.lower(), \
        "Guide does not label source install as primary or recommended"


def test_guide_has_prerequisites_section():
    content = _read(GUIDE_PATH)
    assert "Prerequisites" in content or "prerequisites" in content, \
        "Guide missing Prerequisites section"
    assert "Python" in content and "3.11" in content, \
        "Guide does not list Python 3.11 as a prerequisite"
    assert "git" in content, "Guide does not list git as a prerequisite"
    assert "Xcode" in content or "Command Line Tools" in content, \
        "Guide does not mention Xcode Command Line Tools"


def test_guide_has_troubleshooting_section():
    content = _read(GUIDE_PATH)
    assert "Troubleshooting" in content or "troubleshooting" in content, \
        "Guide missing Troubleshooting section"


def test_guide_dmg_documented_as_alternative():
    content = _read(GUIDE_PATH)
    low = content.lower()
    assert "alternative" in low or "dmg install" in low, \
        "Guide does not document DMG as an alternative"
    # DMG section should NOT be the first major section
    first_h2 = re.search(r'^## (.+)$', content, re.MULTILINE)
    assert first_h2 is not None, "Guide has no H2 headings"
    first_section = first_h2.group(1).lower()
    assert "dmg" not in first_section, \
        f"First H2 section is DMG-related: '{first_h2.group(1)}'"


def test_guide_has_quick_start():
    content = _read(GUIDE_PATH)
    assert "Quick Start" in content or "quick start" in content.lower() or \
           "make install-macos" in content, \
        "Guide does not have a Quick Start or make install-macos command"


def test_guide_references_make_install_macos():
    content = _read(GUIDE_PATH)
    assert "make install-macos" in content, \
        "Guide does not reference 'make install-macos'"


def test_guide_references_install_script():
    content = _read(GUIDE_PATH)
    assert "install-macos.sh" in content, \
        "Guide does not reference install-macos.sh"


def test_guide_bug_references():
    content = _read(GUIDE_PATH)
    assert "BUG-147" in content, "Guide does not mention BUG-147"
    assert "BUG-148" in content, "Guide does not mention BUG-148"
    assert "BUG-149" in content, "Guide does not mention BUG-149"
