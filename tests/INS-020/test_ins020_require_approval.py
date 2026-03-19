"""
INS-020: Tests for require-approval.json template update (ts-python shim).

Verifies that templates/coding/.github/hooks/require-approval.json uses
ts-python instead of bare python for the security gate command.
"""

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REQUIRE_APPROVAL_PATH = (
    REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "require-approval.json"
)


def test_file_exists():
    """require-approval.json must exist in the templates/coding tree."""
    assert REQUIRE_APPROVAL_PATH.exists(), (
        f"require-approval.json not found at {REQUIRE_APPROVAL_PATH}"
    )


def test_json_is_valid():
    """require-approval.json must be valid JSON."""
    content = REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict)


def test_command_field_uses_ts_python():
    """The 'command' field must reference ts-python, not bare python."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    assert hook["command"].startswith("ts-python "), (
        f"Expected 'command' to start with 'ts-python', got: {hook['command']!r}"
    )


def test_windows_field_uses_ts_python():
    """The 'windows' field must reference ts-python, not bare python."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    assert hook["windows"].startswith("ts-python "), (
        f"Expected 'windows' to start with 'ts-python', got: {hook['windows']!r}"
    )


def test_no_bare_python_references():
    """No bare 'python .github/hooks/scripts/security_gate.py' references remain.

    Uses a word-boundary check so that 'ts-python ...' does not trigger a false
    positive (since it contains 'python' as a substring).
    """
    import re
    content = REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8")
    # Match 'python ...' only when NOT preceded by 'ts-'
    assert not re.search(r'(?<!ts-)python\s+\.github/hooks/scripts/security_gate\.py', content), (
        "Found bare 'python' reference in require-approval.json — must use ts-python"
    )


def test_command_points_to_security_gate():
    """Both command fields must still reference the security_gate.py script."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    expected_suffix = ".github/hooks/scripts/security_gate.py"
    assert hook["command"].endswith(expected_suffix), (
        f"'command' field does not point to security_gate.py: {hook['command']!r}"
    )
    assert hook["windows"].endswith(expected_suffix), (
        f"'windows' field does not point to security_gate.py: {hook['windows']!r}"
    )


def test_hook_type_is_command():
    """Hook type must remain 'command'."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    assert hook["type"] == "command"


def test_timeout_preserved():
    """Timeout value must still be 15 (unchanged)."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    assert hook["timeout"] == 15
