"""SAF-015 Edge-Case Tests — Tester additions.

Covers scenarios NOT in the Developer's test suite:
  - Category J commands tested directly (move-item, cp, copy, mkdir, new-item)
  - Piped write commands (path args in pipeline still zone-checked)
  - PowerShell named parameters (-Path, -FilePath, -Destination)
  - Common flags (-Force, -Append, -Encoding, -a)
  - Quoted paths with spaces
  - Redirect operators (> / >>) with write commands
  - Mixed-case/all-uppercase verb variants
  - copy-item: src-in-project + dest-outside and vice versa
  - ni as directory creator (-ItemType Directory)
  - tee with -a (append) flag
  - Tee-Object with -Variable (no path) vs -FilePath
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
P1 = "project/src/file.txt"
P2 = "project/src/renamed.txt"
GITHUB = ".github/hooks/evil.txt"
VSCODE = ".vscode/settings.json"
ROOT = "./root.txt"


def allow(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "allow"


def deny(sg, cmd: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(cmd, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Category J — move-item (direct tests, not covered by Developer)
# ---------------------------------------------------------------------------

def test_move_item_both_project_allowed(sg):
    """move-item with source and destination both inside project must be allowed."""
    assert allow(sg, f"move-item {P1} {P2}")


def test_move_item_source_github_denied(sg):
    """move-item with source in .github/ must be denied."""
    assert deny(sg, f"move-item {GITHUB} {P2}")


def test_move_item_dest_github_denied(sg):
    """move-item with destination in .github/ must be denied."""
    assert deny(sg, f"move-item {P1} {GITHUB}")


def test_move_item_dest_vscode_denied(sg):
    """move-item with destination in .vscode/ must be denied."""
    assert deny(sg, f"move-item {P1} {VSCODE}")


# ---------------------------------------------------------------------------
# Category J — cp (direct tests, not covered by Developer)
# ---------------------------------------------------------------------------

def test_cp_both_project_allowed(sg):
    """cp with source and dest both in project must be allowed."""
    assert allow(sg, f"cp {P1} {P2}")


def test_cp_src_denied(sg):
    """cp with source outside project must be denied."""
    assert deny(sg, f"cp {GITHUB} {P2}")


def test_cp_dest_denied(sg):
    """cp with destination outside project must be denied."""
    assert deny(sg, f"cp {P1} {GITHUB}")


# ---------------------------------------------------------------------------
# Category J — copy (direct tests)
# ---------------------------------------------------------------------------

def test_copy_both_project_allowed(sg):
    """copy with both paths inside project must be allowed."""
    assert allow(sg, f"copy {P1} {P2}")


def test_copy_dest_vscode_denied(sg):
    """copy with destination in .vscode/ must be denied."""
    assert deny(sg, f"copy {P1} {VSCODE}")


# ---------------------------------------------------------------------------
# Category J — mkdir (direct tests)
# ---------------------------------------------------------------------------

def test_mkdir_project_allowed(sg):
    """mkdir targeting a directory inside project must be allowed."""
    assert allow(sg, f"mkdir project/new_dir")


def test_mkdir_github_denied(sg):
    """mkdir targeting .github/ must be denied."""
    assert deny(sg, f"mkdir .github/evil_dir")


def test_mkdir_vscode_denied(sg):
    """mkdir targeting .vscode/ must be denied."""
    assert deny(sg, f"mkdir .vscode/evil_dir")


# ---------------------------------------------------------------------------
# Category J — new-item (distinct from ni alias; direct tests)
# ---------------------------------------------------------------------------

def test_new_item_project_allowed(sg):
    """new-item targeting project folder must be allowed."""
    assert allow(sg, f"new-item {P1}")


def test_new_item_github_denied(sg):
    """new-item targeting .github/ must be denied."""
    assert deny(sg, f"new-item {GITHUB}")


# ---------------------------------------------------------------------------
# Piped write commands — path args across the pipeline are still zone-checked
# ---------------------------------------------------------------------------

def test_pipe_set_content_project_project_allowed(sg):
    """get-content piped to set-content within project must be allowed."""
    assert allow(sg, f"get-content {P1} | set-content {P2}")


def test_pipe_set_content_project_github_denied(sg):
    """get-content piped to set-content targeting .github/ must be denied."""
    assert deny(sg, f"get-content {P1} | set-content {GITHUB}")


def test_pipe_add_content_project_github_denied(sg):
    """get-content piped to add-content targeting .github/ must be denied."""
    assert deny(sg, f"get-content {P1} | add-content {GITHUB}")


def test_pipe_out_file_github_denied(sg):
    """Command piped to out-file targeting .github/ must be denied."""
    assert deny(sg, f"get-content {P1} | out-file {GITHUB}")


def test_pipe_tee_github_denied(sg):
    """Command piped to tee targeting .github/ must be denied."""
    assert deny(sg, f"get-content {P1} | tee {GITHUB}")


def test_pipe_tee_object_github_denied(sg):
    """Command piped to tee-object targeting .github/ must be denied."""
    assert deny(sg, f"get-content {P1} | tee-object {GITHUB}")


# ---------------------------------------------------------------------------
# PowerShell named parameters (-Path, -FilePath, -Destination)
# The parameter name starts with '-' so is skipped; its value is zone-checked.
# ---------------------------------------------------------------------------

def test_set_content_named_path_project_allowed(sg):
    """-Path value in project zone must still be allowed for set-content."""
    assert allow(sg, f"set-content -Path {P1} -Value hello")


def test_set_content_named_path_github_denied(sg):
    """-Path value targeting .github/ must be denied for set-content."""
    assert deny(sg, f"set-content -Path {GITHUB} -Value evil")


def test_add_content_named_path_vscode_denied(sg):
    """-Path value targeting .vscode/ must be denied for add-content."""
    assert deny(sg, f"add-content -Path {VSCODE} -Value evil")


def test_out_file_named_filepath_github_denied(sg):
    """-FilePath value targeting .github/ must be denied for out-file."""
    assert deny(sg, f"out-file -FilePath {GITHUB}")


def test_out_file_named_filepath_project_allowed(sg):
    """-FilePath value in project zone must be allowed for out-file."""
    assert allow(sg, f"out-file -FilePath {P1}")


def test_copy_item_named_destination_github_denied(sg):
    """-Destination value targeting .github/ must be denied for copy-item."""
    assert deny(sg, f"copy-item -Path {P1} -Destination {GITHUB}")


def test_tee_object_named_filepath_github_denied(sg):
    """-FilePath value targeting .github/ must be denied for tee-object."""
    assert deny(sg, f"tee-object -FilePath {GITHUB}")


def test_tee_object_named_filepath_project_allowed(sg):
    """-FilePath value in project zone must be allowed for tee-object."""
    assert allow(sg, f"tee-object -FilePath {P1}")


# ---------------------------------------------------------------------------
# Common flags (-Force, -Append, -Encoding, -a) with project paths (allowed)
# ---------------------------------------------------------------------------

def test_set_content_force_flag_project_allowed(sg):
    """-Force flag with project path must be allowed for set-content."""
    assert allow(sg, f"set-content -Force {P1} hello")


def test_add_content_append_flag_project_allowed(sg):
    """-Append flag with project path must be allowed for add-content."""
    assert allow(sg, f"add-content -Append {P1} more")


def test_out_file_encoding_flag_project_allowed(sg):
    """-Encoding UTF8 flag with project path must be allowed for out-file."""
    assert allow(sg, f"out-file -Encoding UTF8 {P1}")


def test_tee_append_flag_project_allowed(sg):
    """-a (append) flag with project path must be allowed for tee."""
    assert allow(sg, f"tee -a {P1}")


def test_set_content_force_github_denied(sg):
    """-Force flag does NOT bypass zone check — .github/ still denied."""
    assert deny(sg, f"set-content -Force {GITHUB} evil")


def test_add_content_append_vscode_denied(sg):
    """-Append flag does NOT bypass zone check — .vscode/ still denied."""
    assert deny(sg, f"add-content -Append {VSCODE} evil")


# ---------------------------------------------------------------------------
# Quoted paths containing spaces
# ---------------------------------------------------------------------------

def test_set_content_quoted_space_path_allowed(sg):
    """set-content with a quoted project path containing a space must be allowed."""
    assert allow(sg, "set-content 'project/my file.txt' hello")


def test_set_content_quoted_github_denied(sg):
    """set-content with a quoted .github path must still be denied."""
    assert deny(sg, "set-content '.github/hooks/evil.txt' bad")


def test_out_file_quoted_space_project_allowed(sg):
    """out-file with a quoted path containing spaces in project must be allowed."""
    assert allow(sg, "out-file 'project/sub dir/output.txt'")


def test_rename_item_quoted_space_project_allowed(sg):
    """rename-item with quoted paths containing spaces in project must be allowed."""
    assert allow(sg, "rename-item 'project/old file.txt' 'project/new file.txt'")


# ---------------------------------------------------------------------------
# Redirect operators (> / >>) with write commands
# ---------------------------------------------------------------------------

def test_set_content_with_redirect_github_denied(sg):
    """set-content combined with redirect >> targeting .github/ must be denied."""
    assert deny(sg, f"set-content {P1} hello >> {GITHUB}")


def test_out_file_with_redirect_project_allowed(sg):
    """out-file combined with redirect >> targeting project folder must be allowed."""
    assert allow(sg, f"out-file {P1} >> {P2}")


def test_set_content_embedded_redirect_github_denied(sg):
    """Embedded redirect token set-content-path>.github/evil must be denied."""
    assert deny(sg, f"set-content {P1}>{GITHUB}")


# ---------------------------------------------------------------------------
# Mixed-case and all-uppercase verb variants
# ---------------------------------------------------------------------------

def test_move_item_pascalcase_allowed(sg):
    """Move-Item (PascalCase) with both project paths must be allowed."""
    assert allow(sg, f"Move-Item {P1} {P2}")


def test_cp_uppercase_allowed(sg):
    """CP (uppercase) with project paths must be allowed (case-insensitive)."""
    assert allow(sg, f"CP {P1} {P2}")


def test_mkdir_uppercase_allowed(sg):
    """MKDIR (uppercase) targeting project must be allowed."""
    assert allow(sg, "MKDIR project/new_dir")


def test_new_item_pascalcase_allowed(sg):
    """New-Item (PascalCase) targeting project must be allowed."""
    assert allow(sg, f"New-Item {P1}")


def test_ren_uppercase_project_allowed(sg):
    """REN (uppercase) with both paths in project must be allowed."""
    assert allow(sg, f"REN {P1} {P2}")


def test_set_content_allcaps_github_denied(sg):
    """SET-CONTENT (all caps) targeting .github/ must still be denied."""
    assert deny(sg, f"SET-CONTENT {GITHUB} evil")


# ---------------------------------------------------------------------------
# copy-item: src-in-project + dest-outside and vice versa
# ---------------------------------------------------------------------------

def test_copy_item_src_project_dest_root_denied(sg):
    """copy-item with src in project but dest at root level must be denied."""
    assert deny(sg, f"copy-item {P1} {ROOT}")


def test_copy_item_src_root_dest_project_denied(sg):
    """copy-item with src at root level but dest in project must be denied."""
    assert deny(sg, f"copy-item {ROOT} {P1}")


def test_copy_item_src_vscode_dest_project_denied(sg):
    """copy-item with src in .vscode/ and dest in project must be denied."""
    assert deny(sg, f"copy-item {VSCODE} {P1}")


# ---------------------------------------------------------------------------
# ni alias: directory creation with -ItemType Directory
# ---------------------------------------------------------------------------

def test_ni_itemtype_directory_project_allowed(sg):
    """ni -ItemType Directory with a project path must be allowed."""
    assert allow(sg, "ni -ItemType Directory project/new_subdir")


def test_ni_itemtype_directory_github_denied(sg):
    """ni -ItemType Directory targeting .github/ must be denied."""
    assert deny(sg, "ni -ItemType Directory .github/newdir")


# ---------------------------------------------------------------------------
# tee-object: -Variable (no path) vs -FilePath
# ---------------------------------------------------------------------------

def test_tee_object_variable_no_path(sg):
    """tee-object -Variable myvar has no path arg and must be allowed."""
    assert allow(sg, "tee-object -Variable myvar")


def test_tee_object_variable_and_file_github_denied(sg):
    """tee-object -Variable myvar -FilePath .github/x must be denied."""
    assert deny(sg, f"tee-object -Variable myvar -FilePath {GITHUB}")


# ---------------------------------------------------------------------------
# Path traversal on Category J commands (complementing Developer section 18)
# ---------------------------------------------------------------------------

def test_mkdir_traversal_denied(sg):
    """mkdir with path traversal to .github/ must be denied."""
    assert deny(sg, "mkdir project/../.github/evil_dir")


def test_cp_traversal_denied(sg):
    """cp with path traversal destination must be denied."""
    assert deny(sg, "cp project/f.txt project/../.github/evil.txt")


def test_move_item_traversal_dest_denied(sg):
    """move-item with traversal destination to root must be denied."""
    assert deny(sg, f"move-item {P1} project/../../secret.txt")
