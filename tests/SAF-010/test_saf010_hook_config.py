"""
Tests for SAF-010 — Hook Integration Config

Verifies that templates/coding/.github/hooks/require-approval.json:
  - Exists at the correct path
  - Is well-formed JSON
  - Has the correct VS Code hook structure
  - References security_gate.py for PreToolUse events on all platforms
  - The referenced script path actually resolves to an existing file
  - Covers ALL tool types (no tool-type filtering)
"""

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "require-approval.json"
_SCRIPTS_DIR = _REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts"
_SETTINGS_PATH = _REPO_ROOT / "templates" / "coding" / ".vscode" / "settings.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def config() -> dict:
    """Load and parse require-approval.json once for the module."""
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# File existence and validity
# ---------------------------------------------------------------------------

def test_config_file_exists() -> None:
    """require-approval.json must exist at the correct path."""
    assert _CONFIG_PATH.exists(), (
        f"require-approval.json not found at {_CONFIG_PATH}"
    )


def test_config_is_valid_json() -> None:
    """require-approval.json must be well-formed JSON."""
    try:
        json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"require-approval.json is not valid JSON: {exc}")


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

def test_hooks_key_present(config: dict) -> None:
    """Top-level 'hooks' key must be present."""
    assert "hooks" in config, "Missing top-level 'hooks' key"


def test_pretooluse_key_present(config: dict) -> None:
    """'PreToolUse' key must exist under 'hooks'."""
    assert "PreToolUse" in config["hooks"], (
        "Missing 'PreToolUse' key under 'hooks'"
    )


def test_pretooluse_is_non_empty_list(config: dict) -> None:
    """PreToolUse must be a non-empty list."""
    entries = config["hooks"]["PreToolUse"]
    assert isinstance(entries, list), "PreToolUse must be a list"
    assert len(entries) >= 1, "PreToolUse list must not be empty"


def test_entry_type_is_command(config: dict) -> None:
    """First PreToolUse entry must have type 'command'."""
    entry = config["hooks"]["PreToolUse"][0]
    assert entry.get("type") == "command", (
        f"Expected type='command', got {entry.get('type')!r}"
    )


# ---------------------------------------------------------------------------
# Script reference — Unix/macOS command
# ---------------------------------------------------------------------------

def test_command_references_security_gate(config: dict) -> None:
    """The 'command' field must reference security_gate.py."""
    command: str = config["hooks"]["PreToolUse"][0].get("command", "")
    assert "security_gate.py" in command, (
        f"'command' does not reference security_gate.py: {command!r}"
    )


def test_command_does_not_reference_legacy_sh(config: dict) -> None:
    """The 'command' field must NOT reference the old shell script."""
    command: str = config["hooks"]["PreToolUse"][0].get("command", "")
    assert "require-approval.sh" not in command, (
        f"'command' still references legacy shell script: {command!r}"
    )


def test_command_uses_python(config: dict) -> None:
    """The Unix 'command' must invoke python or python3 (not bash/sh)."""
    command: str = config["hooks"]["PreToolUse"][0].get("command", "")
    assert command.startswith("python"), (
        f"'command' should start with 'python' or 'python3', got: {command!r}"
    )


# ---------------------------------------------------------------------------
# Script reference — Windows command
# ---------------------------------------------------------------------------

def test_windows_field_present(config: dict) -> None:
    """A 'windows' override field must be present for Windows compatibility."""
    entry = config["hooks"]["PreToolUse"][0]
    assert "windows" in entry, "Missing 'windows' override field in PreToolUse entry"


def test_windows_command_references_security_gate(config: dict) -> None:
    """The 'windows' command must reference security_gate.py."""
    windows_cmd: str = config["hooks"]["PreToolUse"][0].get("windows", "")
    assert "security_gate.py" in windows_cmd, (
        f"'windows' command does not reference security_gate.py: {windows_cmd!r}"
    )


def test_windows_command_does_not_reference_legacy_ps1(config: dict) -> None:
    """The 'windows' command must NOT reference the old PowerShell script."""
    windows_cmd: str = config["hooks"]["PreToolUse"][0].get("windows", "")
    assert "require-approval.ps1" not in windows_cmd, (
        f"'windows' command still references legacy PowerShell script: {windows_cmd!r}"
    )


def test_windows_command_uses_python(config: dict) -> None:
    """The Windows command must invoke python (not powershell)."""
    windows_cmd: str = config["hooks"]["PreToolUse"][0].get("windows", "")
    assert windows_cmd.startswith("python"), (
        f"'windows' command should start with 'python', got: {windows_cmd!r}"
    )


# ---------------------------------------------------------------------------
# Script path resolution
# ---------------------------------------------------------------------------

def test_script_path_resolves() -> None:
    """The referenced security_gate.py must actually exist on disk."""
    script = _SCRIPTS_DIR / "security_gate.py"
    assert script.exists(), (
        f"security_gate.py does not exist at expected path: {script}"
    )


def test_security_gate_is_python_script(config: dict) -> None:
    """The script referenced in 'command' must end with .py."""
    command: str = config["hooks"]["PreToolUse"][0].get("command", "")
    assert command.endswith(".py"), (
        f"Script referenced in 'command' is not a .py file: {command!r}"
    )


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------

def test_timeout_is_present(config: dict) -> None:
    """Timeout field must be present in the PreToolUse entry."""
    entry = config["hooks"]["PreToolUse"][0]
    assert "timeout" in entry, "Missing 'timeout' field in PreToolUse entry"


def test_timeout_is_positive_integer(config: dict) -> None:
    """Timeout must be a positive integer."""
    timeout = config["hooks"]["PreToolUse"][0].get("timeout")
    assert isinstance(timeout, int), f"timeout must be an int, got {type(timeout)}"
    assert timeout > 0, f"timeout must be > 0, got {timeout}"


# ---------------------------------------------------------------------------
# Coverage — no tool-type filtering (covers ALL tools)
# ---------------------------------------------------------------------------

def test_no_tool_filter(config: dict) -> None:
    """PreToolUse entry must NOT have a 'matcher' or 'tools' restriction.

    If a filter is present, the hook would only fire for specific tool types,
    leaving other tools unguarded. The security gate must cover ALL tool calls.
    """
    entry = config["hooks"]["PreToolUse"][0]
    assert "matcher" not in entry, (
        "'matcher' field found — hook is restricted to specific tools; must cover ALL"
    )
    assert "tools" not in entry, (
        "'tools' field found — hook is restricted to specific tools; must cover ALL"
    )


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def test_no_bom_encoding() -> None:
    """require-approval.json must be UTF-8 without BOM.

    A UTF-8 BOM (0xEF 0xBB 0xBF) would cause json.loads to raise a
    JSONDecodeError in some Python versions and runtimes.
    """
    raw_bytes = _CONFIG_PATH.read_bytes()
    BOM = b"\xef\xbb\xbf"
    assert not raw_bytes.startswith(BOM), (
        "require-approval.json starts with a UTF-8 BOM — must be BOM-free UTF-8"
    )


# ---------------------------------------------------------------------------
# Round-trip fidelity
# ---------------------------------------------------------------------------

def test_json_round_trip(config: dict) -> None:
    """Load + dump + load must produce semantically equivalent JSON.

    Validates that the file has no information-altering content (e.g. duplicate
    keys) that would silently change behaviour after a serialize / deserialize
    cycle.
    """
    raw = _CONFIG_PATH.read_text(encoding="utf-8")
    original = json.loads(raw)
    dumped = json.dumps(original, sort_keys=True)
    reloaded = json.loads(dumped)
    assert original == reloaded, (
        "JSON round-trip produced a different structure — possible duplicate keys"
    )


# ---------------------------------------------------------------------------
# Top-level structure restriction
# ---------------------------------------------------------------------------

def test_top_level_only_hooks_key(config: dict) -> None:
    """Config must contain ONLY the 'hooks' key at the top level.

    Unexpected extra keys could indicate config drift, accidental merge
    artefacts, or an attacker trying to inject unsupported directives.
    """
    unexpected = set(config.keys()) - {"hooks"}
    assert not unexpected, (
        f"Unexpected top-level keys found: {unexpected!r}"
    )


def test_only_pretooluse_event_registered(config: dict) -> None:
    """Only PreToolUse should be registered under 'hooks'.

    An unintended PostToolUse or other event hook added here could
    silently swallow output or introduce side effects.
    """
    registered_events = set(config["hooks"].keys())
    assert registered_events == {"PreToolUse"}, (
        f"Unexpected hook events registered: {registered_events - {'PreToolUse'}!r}"
    )


# ---------------------------------------------------------------------------
# Relative path enforcement
# ---------------------------------------------------------------------------

def test_command_uses_relative_path(config: dict) -> None:
    """The Unix 'command' path must be relative, not absolute.

    An absolute path would break on any installation where the workspace is
    not at exactly the same location.  The path must be relative to the
    workspace root so VS Code can resolve it portably.
    """
    command: str = config["hooks"]["PreToolUse"][0].get("command", "")
    # Extract the script path (part after the interpreter)
    parts = command.split(" ", 1)
    if len(parts) == 2:
        script_path = parts[1]
        assert not script_path.startswith("/"), (
            f"Unix command uses an absolute path: {script_path!r}"
        )
        # Also reject Windows-style absolute paths (C:\ or C:/)
        assert not (len(script_path) > 1 and script_path[1] == ":"), (
            f"Unix command uses a Windows absolute path: {script_path!r}"
        )


def test_windows_command_uses_relative_path(config: dict) -> None:
    """The Windows 'command' path must be relative, not absolute."""
    windows_cmd: str = config["hooks"]["PreToolUse"][0].get("windows", "")
    parts = windows_cmd.split(" ", 1)
    if len(parts) == 2:
        script_path = parts[1]
        assert not script_path.startswith("/"), (
            f"Windows command uses a Unix absolute path: {script_path!r}"
        )
        assert not (len(script_path) > 1 and script_path[1] == ":"), (
            f"Windows command uses an absolute path: {script_path!r}"
        )


def test_windows_security_gate_is_python_script(config: dict) -> None:
    """The script referenced in 'windows' must also end with .py."""
    windows_cmd: str = config["hooks"]["PreToolUse"][0].get("windows", "")
    assert windows_cmd.endswith(".py"), (
        f"Script in 'windows' command is not a .py file: {windows_cmd!r}"
    )


# ---------------------------------------------------------------------------
# Timeout — reasonable range
# ---------------------------------------------------------------------------

def test_timeout_within_reasonable_range(config: dict) -> None:
    """Timeout must be within 1–60 seconds.

    A timeout of 0 would effectively disable the hook.
    A timeout > 60 would cause VS Code to hang noticeably on every tool call.
    """
    timeout = config["hooks"]["PreToolUse"][0].get("timeout", 0)
    assert 1 <= timeout <= 60, (
        f"timeout={timeout} is outside the acceptable range [1, 60]"
    )


# ---------------------------------------------------------------------------
# Security gate script integrity
# ---------------------------------------------------------------------------

def test_security_gate_has_main_function() -> None:
    """security_gate.py must define a callable main() function.

    The hook command calls the script directly via python security_gate.py.
    Without a main() function the script would do nothing when invoked.
    """
    script = _SCRIPTS_DIR / "security_gate.py"
    source = script.read_text(encoding="utf-8")
    assert "def main(" in source, (
        "security_gate.py does not define a main() function"
    )


def test_security_gate_has_name_guard() -> None:
    """security_gate.py must have a 'if __name__ == \"__main__\"' guard.

    Without this guard, importing the module in tests would execute the
    hook logic and block on stdin.
    """
    script = _SCRIPTS_DIR / "security_gate.py"
    source = script.read_text(encoding="utf-8")
    assert '__name__ == "__main__"' in source, (
        "security_gate.py is missing the if __name__ == '__main__' guard"
    )


# ---------------------------------------------------------------------------
# Settings guard — confirms autoApprove is still disabled
# ---------------------------------------------------------------------------

def test_settings_json_auto_approve_disabled() -> None:
    """settings.json must still have chat.tools.global.autoApprove set to false.

    This is a guard test — if someone enables global auto-approve the hook
    system is effectively bypassed.
    """
    raw = _SETTINGS_PATH.read_text(encoding="utf-8")
    # Strip JS-style // comments so json.loads can parse settings.json
    import re
    stripped = re.sub(r"//[^\n]*", "", raw)
    settings = json.loads(stripped)
    assert settings.get("chat.tools.global.autoApprove") is False, (
        "chat.tools.global.autoApprove must be false in settings.json"
    )
