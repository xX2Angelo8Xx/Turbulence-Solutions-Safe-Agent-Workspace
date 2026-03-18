"""SAF-026 — Tests for python -c inline code scanning.

Covers:
1. Safe code is allowed by _scan_python_inline_code
2. Deny-zone path literals are denied (NoAgentZone, .github, .vscode)
3. Path obfuscation/encoding is denied (base64, chr)
4. Network access modules are denied (urllib, socket, requests)
5. Filesystem escape is denied (expanduser, parent traversal, absolute paths)
6. Security infrastructure references are denied (security_gate, update_hashes)
7. Dynamic code execution is denied (eval, exec, __import__)
8. Integration via sanitize_terminal_command
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
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
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"


# ---------------------------------------------------------------------------
# Safe code — should ALLOW
# ---------------------------------------------------------------------------

def test_print_allowed(sg):
    assert sg._scan_python_inline_code("print(42)") is True


def test_math_import_allowed(sg):
    assert sg._scan_python_inline_code("import math; print(math.pi)") is True


def test_json_import_allowed(sg):
    assert sg._scan_python_inline_code("import json; print(json.dumps({'a': 1}))") is True


def test_sys_version_allowed(sg):
    assert sg._scan_python_inline_code("import sys; print(sys.version)") is True


def test_re_compile_allowed(sg):
    # re.compile( should NOT be denied (negative lookbehind)
    assert sg._scan_python_inline_code("import re; re.compile(r'\\d+')") is True


# ---------------------------------------------------------------------------
# Category A — Deny-zone path literals
# ---------------------------------------------------------------------------

def test_noagentzone_denied(sg):
    assert sg._scan_python_inline_code("open('NoAgentZone/README.md').read()") is False


def test_github_denied(sg):
    assert sg._scan_python_inline_code("open('.github/hooks/scripts/security_gate.py').read()") is False


def test_vscode_denied(sg):
    assert sg._scan_python_inline_code("open('.vscode/settings.json').read()") is False


def test_noagentzone_case_insensitive(sg):
    # Case-insensitive: NOAGENTZONE should still be denied
    assert sg._scan_python_inline_code("open('NOAGENTZONE/file.txt').read()") is False


# ---------------------------------------------------------------------------
# Category B — Path obfuscation / encoding
# ---------------------------------------------------------------------------

def test_base64_denied(sg):
    assert sg._scan_python_inline_code("import base64; base64.b64decode('...')") is False


def test_b64decode_denied(sg):
    assert sg._scan_python_inline_code("b64decode(b'aGVsbG8=')") is False


def test_codecs_denied(sg):
    assert sg._scan_python_inline_code("import codecs; codecs.decode('test')") is False


def test_fromhex_denied(sg):
    assert sg._scan_python_inline_code("bytes.fromhex('48656c6c6f')") is False


def test_bytearray_denied(sg):
    assert sg._scan_python_inline_code("bytearray([72, 101, 108])") is False


def test_chr_building_denied(sg):
    assert sg._scan_python_inline_code("''.join(chr(x) for x in [78, 111])") is False


# ---------------------------------------------------------------------------
# Category C — Network access
# ---------------------------------------------------------------------------

def test_urllib_denied(sg):
    assert sg._scan_python_inline_code("import urllib.request; urllib.request.urlopen('http://...')") is False


def test_socket_denied(sg):
    assert sg._scan_python_inline_code("import socket; s = socket.socket()") is False


def test_requests_denied(sg):
    assert sg._scan_python_inline_code("import requests; requests.get('http://...')") is False


def test_http_client_denied(sg):
    assert sg._scan_python_inline_code("import http.client; http.client.HTTPConnection('x')") is False


def test_ftplib_denied(sg):
    assert sg._scan_python_inline_code("import ftplib; ftplib.FTP('host')") is False


def test_smtplib_denied(sg):
    assert sg._scan_python_inline_code("import smtplib") is False


def test_xmlrpc_denied(sg):
    assert sg._scan_python_inline_code("import xmlrpc.client") is False


# ---------------------------------------------------------------------------
# Category D — Filesystem escape
# ---------------------------------------------------------------------------

def test_expanduser_denied(sg):
    assert sg._scan_python_inline_code("os.path.expanduser('~')") is False


def test_expandvars_denied(sg):
    assert sg._scan_python_inline_code("os.path.expandvars('$HOME')") is False


def test_parent_traversal_denied(sg):
    assert sg._scan_python_inline_code("open('../secret.txt').read()") is False


def test_parent_traversal_backslash_denied(sg):
    assert sg._scan_python_inline_code("open('..\\\\secret.txt').read()") is False


def test_absolute_path_unix_denied(sg):
    assert sg._scan_python_inline_code("open('/etc/passwd').read()") is False


def test_absolute_path_unix_home_denied(sg):
    assert sg._scan_python_inline_code("open('/home/user/.ssh/id_rsa').read()") is False


def test_absolute_path_windows_denied(sg):
    assert sg._scan_python_inline_code("open('C:\\\\Users\\\\secret.txt').read()") is False


def test_absolute_path_windows_d_drive_denied(sg):
    assert sg._scan_python_inline_code("open('D:\\\\data\\\\file.txt').read()") is False


# ---------------------------------------------------------------------------
# Category E — Security infrastructure tampering
# ---------------------------------------------------------------------------

def test_security_gate_ref_denied(sg):
    assert sg._scan_python_inline_code("open('security_gate.py').read()") is False


def test_update_hashes_denied(sg):
    assert sg._scan_python_inline_code("exec(open('update_hashes.py').read())") is False


def test_zone_classifier_denied(sg):
    assert sg._scan_python_inline_code("import zone_classifier") is False


def test_require_approval_hyphen_denied(sg):
    assert sg._scan_python_inline_code("open('require-approval.json').read()") is False


def test_require_approval_underscore_denied(sg):
    assert sg._scan_python_inline_code("x = 'require_approval'") is False


# ---------------------------------------------------------------------------
# Category F — Dynamic code execution
# ---------------------------------------------------------------------------

def test_eval_denied(sg):
    assert sg._scan_python_inline_code("eval('open(\"x\").read()')") is False


def test_exec_denied(sg):
    assert sg._scan_python_inline_code("exec('import os')") is False


def test_dunder_import_denied(sg):
    assert sg._scan_python_inline_code("__import__('os').system('ls')") is False


def test_importlib_denied(sg):
    assert sg._scan_python_inline_code("import importlib; importlib.import_module('os')") is False


def test_compile_denied(sg):
    # compile( without re. prefix should be denied
    assert sg._scan_python_inline_code("compile('import os', '', 'exec')") is False


def test_getattr_denied(sg):
    assert sg._scan_python_inline_code("getattr(os, 'system')('ls')") is False


def test_setattr_denied(sg):
    assert sg._scan_python_inline_code("setattr(obj, 'x', 1)") is False


def test_delattr_denied(sg):
    assert sg._scan_python_inline_code("delattr(obj, 'x')") is False


# ---------------------------------------------------------------------------
# Integration tests — full sanitize_terminal_command calls
# ---------------------------------------------------------------------------

def test_full_python_c_safe(sg):
    """python -c "print(42)" should be allowed via sanitize_terminal_command."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            'python -c "print(42)"',
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


def test_full_python_c_noagentzone(sg):
    """python -c "open('NoAgentZone/README.md').read()" should be denied."""
    result, _ = sg.sanitize_terminal_command(
        "python -c \"open('NoAgentZone/README.md').read()\"",
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"


def test_full_python_c_base64(sg):
    """python -c with base64 import should be denied."""
    result, _ = sg.sanitize_terminal_command(
        'python -c "import base64; print(base64.b64decode(b\'aGVsbG8=\'))"',
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"


def test_full_python_c_urllib(sg):
    """python -c with urllib import should be denied."""
    result, _ = sg.sanitize_terminal_command(
        'python -c "import urllib.request"',
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"


def test_full_python3_c_safe(sg):
    """python3 -c "print(42)" should be allowed."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            'python3 -c "print(42)"',
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


def test_full_py_c_safe(sg):
    """py -c "print(42)" should be allowed."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            'py -c "print(42)"',
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


def test_update_hashes_terminal_denied(sg):
    """Direct execution of update_hashes.py via terminal should be denied."""
    result, _ = sg.sanitize_terminal_command(
        "python update_hashes.py",
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"
