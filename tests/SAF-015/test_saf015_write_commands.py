"""SAF-015 — Tests for expanded terminal allowlist: write file commands.

Verifies that the following commands are allowed when targeting the project
folder and denied when targeting restricted zones or root-level files:
  set-content, sc, add-content, ac, out-file,
  rename-item, ren, tee-object, tee, ni
Also verifies that commands already in Category J (copy-item, cp, copy,
mv, move-item, new-item, mkdir) continue to work correctly.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "coding"
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


# Workspace root used in all tests
WS = "c:/workspace"

# Path inside the project folder — always allowed
PROJECT_PATH = "project/src/output.txt"
PROJECT_PATH2 = "project/src/renamed.txt"

# Paths that target restricted zones — always denied
GITHUB_PATH = ".github/hooks/scripts/security_gate.py"
VSCODE_PATH = ".vscode/settings.json"
# Root-level file — ./ prefix triggers zone check
ROOT_FILE = "./root_config.json"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. set-content
# ---------------------------------------------------------------------------

def test_set_content_project_folder_allowed(sg):
    """set-content targeting project folder must be allowed."""
    assert allow(sg, f"set-content {PROJECT_PATH} 'hello'")


def test_set_content_github_denied(sg):
    """set-content targeting .github/ must be denied."""
    assert deny(sg, f"set-content {GITHUB_PATH} 'evil'")


def test_set_content_vscode_denied(sg):
    """set-content targeting .vscode/ must be denied."""
    assert deny(sg, f"set-content {VSCODE_PATH} 'evil'")


def test_set_content_root_file_denied(sg):
    """set-content targeting a root-level file must be denied."""
    assert deny(sg, f"set-content {ROOT_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 2. sc (alias for Set-Content)
# ---------------------------------------------------------------------------

def test_sc_project_folder_allowed(sg):
    """sc (Set-Content alias) targeting project folder must be allowed."""
    assert allow(sg, f"sc {PROJECT_PATH} 'hello'")


def test_sc_github_denied(sg):
    """sc targeting .github/ must be denied."""
    assert deny(sg, f"sc {GITHUB_PATH} 'evil'")


def test_sc_vscode_denied(sg):
    """sc targeting .vscode/ must be denied."""
    assert deny(sg, f"sc {VSCODE_PATH} 'evil'")


def test_sc_root_file_denied(sg):
    """sc targeting a root-level file must be denied."""
    assert deny(sg, f"sc {ROOT_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 3. Alias parity — sc and set-content behave identically
# ---------------------------------------------------------------------------

def test_sc_and_set_content_same_allow(sg):
    """sc and set-content must both allow the same project-folder path."""
    r1 = sg.sanitize_terminal_command(f"set-content {PROJECT_PATH} x", WS)
    r2 = sg.sanitize_terminal_command(f"sc {PROJECT_PATH} x", WS)
    assert r1[0] == r2[0] == "allow"


def test_sc_and_set_content_same_deny(sg):
    """sc and set-content must both deny the same .github path."""
    r1 = sg.sanitize_terminal_command(f"set-content {GITHUB_PATH} x", WS)
    r2 = sg.sanitize_terminal_command(f"sc {GITHUB_PATH} x", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 4. add-content
# ---------------------------------------------------------------------------

def test_add_content_project_folder_allowed(sg):
    """add-content targeting project folder must be allowed."""
    assert allow(sg, f"add-content {PROJECT_PATH} 'more text'")


def test_add_content_github_denied(sg):
    """add-content targeting .github/ must be denied."""
    assert deny(sg, f"add-content {GITHUB_PATH} 'evil'")


def test_add_content_vscode_denied(sg):
    """add-content targeting .vscode/ must be denied."""
    assert deny(sg, f"add-content {VSCODE_PATH} 'evil'")


def test_add_content_root_file_denied(sg):
    """add-content targeting a root-level file must be denied."""
    assert deny(sg, f"add-content {ROOT_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 5. ac (alias for Add-Content)
# ---------------------------------------------------------------------------

def test_ac_project_folder_allowed(sg):
    """ac (Add-Content alias) targeting project folder must be allowed."""
    assert allow(sg, f"ac {PROJECT_PATH} 'more text'")


def test_ac_github_denied(sg):
    """ac targeting .github/ must be denied."""
    assert deny(sg, f"ac {GITHUB_PATH} 'evil'")


def test_ac_vscode_denied(sg):
    """ac targeting .vscode/ must be denied."""
    assert deny(sg, f"ac {VSCODE_PATH} 'evil'")


def test_ac_root_file_denied(sg):
    """ac targeting a root-level file must be denied."""
    assert deny(sg, f"ac {ROOT_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 6. Alias parity — ac and add-content behave identically
# ---------------------------------------------------------------------------

def test_ac_and_add_content_same_allow(sg):
    """ac and add-content must both allow the same project-folder path."""
    r1 = sg.sanitize_terminal_command(f"add-content {PROJECT_PATH} x", WS)
    r2 = sg.sanitize_terminal_command(f"ac {PROJECT_PATH} x", WS)
    assert r1[0] == r2[0] == "allow"


def test_ac_and_add_content_same_deny(sg):
    """ac and add-content must both deny the same .github path."""
    r1 = sg.sanitize_terminal_command(f"add-content {GITHUB_PATH} x", WS)
    r2 = sg.sanitize_terminal_command(f"ac {GITHUB_PATH} x", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 7. out-file
# ---------------------------------------------------------------------------

def test_out_file_project_folder_allowed(sg):
    """out-file targeting project folder must be allowed."""
    assert allow(sg, f"out-file {PROJECT_PATH}")


def test_out_file_github_denied(sg):
    """out-file targeting .github/ must be denied."""
    assert deny(sg, f"out-file {GITHUB_PATH}")


def test_out_file_vscode_denied(sg):
    """out-file targeting .vscode/ must be denied."""
    assert deny(sg, f"out-file {VSCODE_PATH}")


def test_out_file_root_file_denied(sg):
    """out-file targeting a root-level file must be denied."""
    assert deny(sg, f"out-file {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 8. rename-item
# ---------------------------------------------------------------------------

def test_rename_item_project_folder_allowed(sg):
    """rename-item with both paths inside project folder must be allowed."""
    assert allow(sg, f"rename-item {PROJECT_PATH} {PROJECT_PATH2}")


def test_rename_item_source_github_denied(sg):
    """rename-item with source in .github/ must be denied."""
    assert deny(sg, f"rename-item {GITHUB_PATH} {PROJECT_PATH2}")


def test_rename_item_dest_github_denied(sg):
    """rename-item with destination in .github/ must be denied."""
    assert deny(sg, f"rename-item {PROJECT_PATH} {GITHUB_PATH}")


def test_rename_item_vscode_denied(sg):
    """rename-item targeting .vscode/ source must be denied."""
    assert deny(sg, f"rename-item {VSCODE_PATH} {PROJECT_PATH2}")


def test_rename_item_root_file_denied(sg):
    """rename-item targeting root-level file must be denied."""
    assert deny(sg, f"rename-item {ROOT_FILE} {PROJECT_PATH2}")


# ---------------------------------------------------------------------------
# 9. ren (alias for Rename-Item)
# ---------------------------------------------------------------------------

def test_ren_project_folder_allowed(sg):
    """ren (Rename-Item alias) with both paths inside project folder must be allowed."""
    assert allow(sg, f"ren {PROJECT_PATH} {PROJECT_PATH2}")


def test_ren_source_github_denied(sg):
    """ren with source in .github/ must be denied."""
    assert deny(sg, f"ren {GITHUB_PATH} {PROJECT_PATH2}")


def test_ren_dest_github_denied(sg):
    """ren with destination in .github/ must be denied."""
    assert deny(sg, f"ren {PROJECT_PATH} {GITHUB_PATH}")


def test_ren_root_file_denied(sg):
    """ren targeting root-level file must be denied."""
    assert deny(sg, f"ren {ROOT_FILE} {PROJECT_PATH2}")


# ---------------------------------------------------------------------------
# 10. Alias parity — ren and rename-item behave identically
# ---------------------------------------------------------------------------

def test_ren_and_rename_item_same_allow(sg):
    """ren and rename-item must both allow project-folder paths."""
    r1 = sg.sanitize_terminal_command(f"rename-item {PROJECT_PATH} {PROJECT_PATH2}", WS)
    r2 = sg.sanitize_terminal_command(f"ren {PROJECT_PATH} {PROJECT_PATH2}", WS)
    assert r1[0] == r2[0] == "allow"


def test_ren_and_rename_item_same_deny(sg):
    """ren and rename-item must both deny .github paths."""
    r1 = sg.sanitize_terminal_command(f"rename-item {GITHUB_PATH} {PROJECT_PATH2}", WS)
    r2 = sg.sanitize_terminal_command(f"ren {GITHUB_PATH} {PROJECT_PATH2}", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 11. tee-object
# ---------------------------------------------------------------------------

def test_tee_object_project_folder_allowed(sg):
    """tee-object with project folder output path must be allowed."""
    assert allow(sg, f"tee-object {PROJECT_PATH}")


def test_tee_object_github_denied(sg):
    """tee-object targeting .github/ must be denied."""
    assert deny(sg, f"tee-object {GITHUB_PATH}")


def test_tee_object_vscode_denied(sg):
    """tee-object targeting .vscode/ must be denied."""
    assert deny(sg, f"tee-object {VSCODE_PATH}")


def test_tee_object_root_file_denied(sg):
    """tee-object targeting root-level file must be denied."""
    assert deny(sg, f"tee-object {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 12. tee
# ---------------------------------------------------------------------------

def test_tee_project_folder_allowed(sg):
    """tee with project folder output path must be allowed."""
    assert allow(sg, f"tee {PROJECT_PATH}")


def test_tee_github_denied(sg):
    """tee targeting .github/ must be denied."""
    assert deny(sg, f"tee {GITHUB_PATH}")


def test_tee_vscode_denied(sg):
    """tee targeting .vscode/ must be denied."""
    assert deny(sg, f"tee {VSCODE_PATH}")


def test_tee_root_file_denied(sg):
    """tee targeting root-level file must be denied."""
    assert deny(sg, f"tee {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 13. Alias parity — tee and tee-object behave identically
# ---------------------------------------------------------------------------

def test_tee_and_tee_object_same_allow(sg):
    """tee and tee-object must both allow project-folder paths."""
    r1 = sg.sanitize_terminal_command(f"tee-object {PROJECT_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"tee {PROJECT_PATH}", WS)
    assert r1[0] == r2[0] == "allow"


def test_tee_and_tee_object_same_deny(sg):
    """tee and tee-object must both deny .github paths."""
    r1 = sg.sanitize_terminal_command(f"tee-object {GITHUB_PATH}", WS)
    r2 = sg.sanitize_terminal_command(f"tee {GITHUB_PATH}", WS)
    assert r1[0] == r2[0] == "deny"


# ---------------------------------------------------------------------------
# 14. ni (alias for New-Item)
# ---------------------------------------------------------------------------

def test_ni_project_folder_allowed(sg):
    """ni (New-Item alias) targeting project folder must be allowed."""
    assert allow(sg, f"ni {PROJECT_PATH}")


def test_ni_github_denied(sg):
    """ni targeting .github/ must be denied."""
    assert deny(sg, f"ni {GITHUB_PATH}")


def test_ni_vscode_denied(sg):
    """ni targeting .vscode/ must be denied."""
    assert deny(sg, f"ni {VSCODE_PATH}")


def test_ni_root_file_denied(sg):
    """ni targeting root-level file must be denied."""
    assert deny(sg, f"ni {ROOT_FILE}")


# ---------------------------------------------------------------------------
# 15. Multi-path: both paths inside project → allow; any outside → deny
# ---------------------------------------------------------------------------

def test_copy_item_both_project_allowed(sg):
    """copy-item with source and dest both in project folder must be allowed."""
    assert allow(sg, f"copy-item {PROJECT_PATH} {PROJECT_PATH2}")


def test_copy_item_source_github_denied(sg):
    """copy-item with source in .github/ must be denied."""
    assert deny(sg, f"copy-item {GITHUB_PATH} {PROJECT_PATH2}")


def test_copy_item_dest_github_denied(sg):
    """copy-item with destination in .github/ must be denied."""
    assert deny(sg, f"copy-item {PROJECT_PATH} {GITHUB_PATH}")


def test_mv_both_project_allowed(sg):
    """mv with source and dest both in project folder must be allowed."""
    assert allow(sg, f"mv {PROJECT_PATH} {PROJECT_PATH2}")


def test_mv_source_outside_denied(sg):
    """mv with source outside project must be denied."""
    assert deny(sg, f"mv {VSCODE_PATH} {PROJECT_PATH2}")


def test_mv_dest_outside_denied(sg):
    """mv with destination outside project must be denied."""
    assert deny(sg, f"mv {PROJECT_PATH} {ROOT_FILE}")


def test_rename_item_both_project_allowed(sg):
    """rename-item with both paths inside project folder must be allowed."""
    assert allow(sg, f"rename-item {PROJECT_PATH} {PROJECT_PATH2}")


def test_rename_item_one_outside_denied(sg):
    """rename-item with one path outside project must be denied."""
    assert deny(sg, f"rename-item {PROJECT_PATH} {VSCODE_PATH}")


# ---------------------------------------------------------------------------
# 16. Case-insensitive verb matching (PowerShell verbs are case-insensitive)
# ---------------------------------------------------------------------------

def test_set_content_uppercase_verb_allowed(sg):
    """Set-Content (PascalCase) targeting project folder must be allowed."""
    assert allow(sg, f"Set-Content {PROJECT_PATH} hello")


def test_add_content_uppercase_verb_allowed(sg):
    """Add-Content (PascalCase) targeting project folder must be allowed."""
    assert allow(sg, f"Add-Content {PROJECT_PATH} hello")


def test_out_file_uppercase_verb_allowed(sg):
    """Out-File (PascalCase) targeting project folder must be allowed."""
    assert allow(sg, f"Out-File {PROJECT_PATH}")


def test_rename_item_uppercase_verb_allowed(sg):
    """Rename-Item (PascalCase) must be allowed for project paths."""
    assert allow(sg, f"Rename-Item {PROJECT_PATH} {PROJECT_PATH2}")


def test_tee_object_uppercase_verb_allowed(sg):
    """Tee-Object (PascalCase) targeting project folder must be allowed."""
    assert allow(sg, f"Tee-Object {PROJECT_PATH}")


def test_new_item_alias_ni_allowed(sg):
    """NI (uppercase alias) targeting project folder must be allowed."""
    assert allow(sg, f"NI {PROJECT_PATH}")


# ---------------------------------------------------------------------------
# 17. Security: write commands targeting restricted zones are denied
#     (protection test)
# ---------------------------------------------------------------------------

def test_write_commands_cannot_reach_github(sg):
    """All new write commands must deny targeting .github/."""
    commands = [
        f"set-content {GITHUB_PATH} x",
        f"sc {GITHUB_PATH} x",
        f"add-content {GITHUB_PATH} x",
        f"ac {GITHUB_PATH} x",
        f"out-file {GITHUB_PATH}",
        f"rename-item {GITHUB_PATH} {PROJECT_PATH}",
        f"ren {GITHUB_PATH} {PROJECT_PATH}",
        f"tee-object {GITHUB_PATH}",
        f"tee {GITHUB_PATH}",
        f"ni {GITHUB_PATH}",
    ]
    for cmd in commands:
        decision, _ = sg.sanitize_terminal_command(cmd, WS)
        assert decision == "deny", f"Expected deny for: {cmd}"


def test_write_commands_cannot_reach_vscode(sg):
    """All new write commands must deny targeting .vscode/."""
    commands = [
        f"set-content {VSCODE_PATH} x",
        f"sc {VSCODE_PATH} x",
        f"add-content {VSCODE_PATH} x",
        f"ac {VSCODE_PATH} x",
        f"out-file {VSCODE_PATH}",
        f"rename-item {VSCODE_PATH} {PROJECT_PATH}",
        f"ren {VSCODE_PATH} {PROJECT_PATH}",
        f"tee-object {VSCODE_PATH}",
        f"tee {VSCODE_PATH}",
        f"ni {VSCODE_PATH}",
    ]
    for cmd in commands:
        decision, _ = sg.sanitize_terminal_command(cmd, WS)
        assert decision == "deny", f"Expected deny for: {cmd}"


# ---------------------------------------------------------------------------
# 18. Security: bypass-attempt test — path traversal via ../
# ---------------------------------------------------------------------------

def test_set_content_path_traversal_to_github_denied(sg):
    """set-content with path traversal to .github/ must be denied."""
    assert deny(sg, "set-content project/../.github/hooks/evil x")


def test_out_file_path_traversal_to_vscode_denied(sg):
    """out-file with path traversal to .vscode/ must be denied."""
    assert deny(sg, "out-file project/../.vscode/settings.json")


def test_tee_path_traversal_denied(sg):
    """tee with path traversal must be denied."""
    assert deny(sg, "tee project/../.github/pwned")


def test_rename_item_traversal_dest_denied(sg):
    """rename-item with dest traversal to .github/ must be denied."""
    assert deny(sg, f"rename-item {PROJECT_PATH} project/../.github/evil")


# ---------------------------------------------------------------------------
# 19. Security: bypass-attempt test — dollar-sign variable injection
# ---------------------------------------------------------------------------

def test_set_content_dollar_var_denied(sg):
    """set-content with $HOME variable must be denied."""
    assert deny(sg, "set-content $HOME/.bashrc evil")


def test_out_file_dollar_var_denied(sg):
    """out-file with $env:APPDATA variable must be denied."""
    assert deny(sg, "out-file $env:APPDATA/evil.txt")


def test_tee_dollar_var_denied(sg):
    """tee with $HOME variable must be denied."""
    assert deny(sg, "tee $HOME/secret.txt")
