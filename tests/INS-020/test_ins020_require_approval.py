"""
INS-020: Tests for require-approval.json template update (ts-python shim).

Verifies that templates/coding/.github/hooks/require-approval.json uses
ts-python instead of bare python for the security gate command.
"""

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REQUIRE_APPROVAL_PATH = (
    REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "require-approval.json"
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


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------


def test_file_encoding_no_bom():
    """File must be UTF-8 without BOM (BOMs break JSON parsers in some tools)."""
    raw = REQUIRE_APPROVAL_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), (
        "require-approval.json must not have a UTF-8 BOM"
    )
    # Ensure the bytes are valid UTF-8
    raw.decode("utf-8")


def test_command_and_windows_fields_are_identical():
    """The 'command' and 'windows' fields must be exactly the same string.

    Both platforms should invoke the security gate with identical arguments.
    """
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    assert hook["command"] == hook["windows"], (
        f"'command' and 'windows' fields differ:\n"
        f"  command: {hook['command']!r}\n"
        f"  windows: {hook['windows']!r}"
    )


def test_pretooluse_has_exactly_one_hook():
    """PreToolUse list must contain exactly one hook entry (no duplicates, no gaps)."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    entries = data["hooks"]["PreToolUse"]
    assert isinstance(entries, list), "PreToolUse must be a list"
    assert len(entries) == 1, (
        f"Expected exactly 1 PreToolUse hook, found {len(entries)}"
    )


def test_ts_python_command_is_lowercase():
    """ts-python in both fields must be exactly lowercase — no mixed-case variants."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    for field in ("command", "windows"):
        assert hook[field].startswith("ts-python "), (
            f"Field '{field}' must start with lowercase 'ts-python ': {hook[field]!r}"
        )


def test_no_trailing_whitespace_in_command_fields():
    """Command fields must not have leading or trailing whitespace."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    for field in ("command", "windows"):
        assert hook[field] == hook[field].strip(), (
            f"Field '{field}' has unexpected leading/trailing whitespace: {hook[field]!r}"
        )


def test_hook_has_required_fields():
    """Hook entry must contain all four required fields: type, command, windows, timeout."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    required = {"type", "command", "windows", "timeout"}
    missing = required - hook.keys()
    assert not missing, f"Hook is missing required fields: {missing}"


def test_hook_has_no_unexpected_fields():
    """Hook entry must not contain fields beyond the four expected ones."""
    data = json.loads(REQUIRE_APPROVAL_PATH.read_text(encoding="utf-8"))
    hook = data["hooks"]["PreToolUse"][0]
    allowed = {"type", "command", "windows", "timeout"}
    extra = set(hook.keys()) - allowed
    assert not extra, f"Hook has unexpected extra fields: {extra}"
