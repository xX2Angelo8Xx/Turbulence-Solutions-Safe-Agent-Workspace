"""FIX-022 — Tests for project-folder relative path fallback.

Verifies that read/execute verbs can resolve relative paths like
``src/app.py`` against the project folder (not just the workspace root),
while destructive verbs (rm, del, remove-item) are still denied.
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
        "templates", "coding", ".github", "hooks", "scripts",
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
# python with relative project paths — should ALLOW
# ===========================================================================

def test_python_src_app_allow():
    """TST-1691: python src/app.py with project fallback -> allow."""
    assert allow("python src/app.py")


def test_python3_src_app_allow():
    """TST-1692: python3 src/app.py -> allow."""
    assert allow("python3 src/app.py")


def test_python_m_pytest_tests_allow():
    """TST-1693: python -m pytest tests/ -> allow."""
    assert allow("python -m pytest tests/")


def test_python_dot_slash_src_app_allow():
    """TST-1694: python ./src/app.py -> allow."""
    assert allow("python ./src/app.py")


# ===========================================================================
# cat / type with relative project paths — should ALLOW
# ===========================================================================

def test_cat_src_app_allow():
    """TST-1695: cat src/app.py -> allow via project fallback."""
    assert allow("cat src/app.py")


def test_type_src_app_allow():
    """TST-1696: type src/app.py -> allow via project fallback."""
    assert allow("type src/app.py")


def test_type_dot_subdir_file_allow():
    """TST-1697: type ./src/file.txt -> allow via project fallback (2+ segments)."""
    assert allow("type ./src/file.txt")


def test_type_dot_bare_file_deny():
    """TST-1697b: type ./file.txt -> deny (single-segment, ambiguous root path)."""
    assert deny("type ./file.txt")


def test_ls_trailing_slash_src_allow():
    """TST-1697c: ls src/ -> allow (trailing slash = directory ref, fallback OK)."""
    assert allow("ls src/")


def test_python_tests_trailing_slash_allow():
    """TST-1697d: python -m pytest tests/ -> allow (trailing slash directory)."""
    assert allow("python -m pytest tests/")


# ===========================================================================
# ls / dir with relative project paths — should ALLOW
# ===========================================================================

def test_ls_src_allow():
    """TST-1698: ls src/ -> allow via project fallback."""
    assert allow("ls src/")


def test_dir_src_allow():
    """TST-1699: dir src/ -> allow."""
    assert allow("dir src/")


def test_get_content_src_app_allow():
    """TST-1700: get-content src/app.py -> allow."""
    assert allow("get-content src/app.py")


# ===========================================================================
# Destructive commands — MUST DENY (no fallback)
# ===========================================================================

def test_rm_src_app_deny():
    """TST-1701: rm src/app.py -> deny (rm not in fallback verbs)."""
    assert deny("rm src/app.py")


def test_rm_dot_deny():
    """TST-1702: rm . -> deny."""
    assert deny("rm .")


def test_rm_dot_slash_root_config_deny():
    """TST-1703: rm ./root_config.json -> deny."""
    assert deny("rm ./root_config.json")


def test_del_src_app_deny():
    """TST-1704: del src/app.py -> deny (del not in fallback verbs)."""
    assert deny("del src/app.py")


def test_remove_item_src_app_deny():
    """TST-1705: remove-item src/app.py -> deny (not in fallback verbs)."""
    assert deny("remove-item src/app.py")


def test_rm_rf_dot_deny():
    """TST-1706: rm -rf . -> deny."""
    assert deny("rm -rf .")


def test_rm_home_deny():
    """TST-1707: rm ~/ -> deny."""
    assert deny("rm ~/")


# ===========================================================================
# Direct project path still works (no fallback needed)
# ===========================================================================

def test_python_project_src_app_allow():
    """TST-1708: python project/src/app.py -> allow (direct)."""
    assert allow("python project/src/app.py")


def test_cat_project_src_app_allow():
    """TST-1709: cat project/src/app.py -> allow (direct)."""
    assert allow("cat project/src/app.py")


# ===========================================================================
# Deny-zone paths never get fallback
# ===========================================================================

def test_python_github_deny():
    """TST-1710: python .github/hooks/script.py -> deny."""
    assert deny("python .github/hooks/script.py")


def test_cat_vscode_deny():
    """TST-1711: cat .vscode/settings.json -> deny."""
    assert deny("cat .vscode/settings.json")


def test_cat_noagentzone_deny():
    """TST-1712: cat noagentzone/secret.txt -> deny."""
    assert deny("cat noagentzone/secret.txt")


# ===========================================================================
# Chained commands — safe verb + destructive verb
# ===========================================================================

def test_chain_python_and_rm_deny():
    """TST-1713: python src/app.py; rm src/app.py -> deny."""
    assert deny("python src/app.py; rm src/app.py")


# ===========================================================================
# _try_project_fallback unit tests
# ===========================================================================

def test_try_project_fallback_relative_allow():
    """TST-1714: _try_project_fallback with valid relative path -> True."""
    assert sg._try_project_fallback("src/app.py", WS) is True


def test_try_project_fallback_absolute_deny():
    """TST-1715: _try_project_fallback with absolute path -> False."""
    assert sg._try_project_fallback("c:/workspace/src/app.py", WS) is False


def test_try_project_fallback_tilde_deny():
    """TST-1716: _try_project_fallback with ~ -> False."""
    assert sg._try_project_fallback("~/secret", WS) is False


def test_try_project_fallback_deny_zone():
    """TST-1717: _try_project_fallback with deny zone -> False."""
    assert sg._try_project_fallback(".github/hooks/evil.py", WS) is False


def test_try_project_fallback_empty():
    """TST-1718: _try_project_fallback with empty/dot -> False."""
    assert sg._try_project_fallback(".", WS) is False
    assert sg._try_project_fallback("..", WS) is False
    assert sg._try_project_fallback("", WS) is False


def test_try_project_fallback_linux_absolute():
    """TST-1719: _try_project_fallback with /etc/passwd -> False."""
    assert sg._try_project_fallback("/etc/passwd", WS) is False
