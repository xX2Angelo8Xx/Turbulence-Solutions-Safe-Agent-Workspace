"""
Tests for SAF-010 — Hook Integration Config

Verifies that Default-Project/.github/hooks/require-approval.json:
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
_CONFIG_PATH = _REPO_ROOT / "Default-Project" / ".github" / "hooks" / "require-approval.json"
_SCRIPTS_DIR = _REPO_ROOT / "Default-Project" / ".github" / "hooks" / "scripts"
_SETTINGS_PATH = _REPO_ROOT / "Default-Project" / ".vscode" / "settings.json"


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
