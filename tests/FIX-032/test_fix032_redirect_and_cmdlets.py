"""FIX-032 — Tests for shell redirection and PS write cmdlets in project folder.

Verifies that:
1. Shell redirection (> >>) to project folder paths is allowed.
2. Shell redirection to restricted zones is denied.
3. PS write cmdlets (Set-Content, Add-Content, Out-File) with project-folder
   paths are allowed.
4. PS copy/move cmdlets (Copy-Item, Move-Item) with project-folder paths are
   allowed.
5. Project-folder fallback applies: multi-segment relative paths without the
   project prefix resolve correctly when CWD is inside the project folder.
6. All deny cases still deny (restricted zones, variable paths, etc.).
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
    """Mock detect_project_folder to return 'project' without filesystem access."""
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


# Workspace root used in all tests
WS = "c:/workspace"

# Paths inside the project folder — must always be allowed
PROJECT_FILE = "project/file.txt"
PROJECT_NESTED = "project/src/output.txt"

# Paths in restricted zones — must always be denied
GITHUB_FILE = ".github/file.txt"
VSCODE_FILE = ".vscode/settings.json"
NOAGENT_FILE = "noagentzone/secret.txt"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# 1. Shell redirection > to project folder — allowed
# ---------------------------------------------------------------------------

def test_redirect_gt_project_file_allowed(sg):
    """echo ... > project/file.txt must be allowed."""
    assert allow(sg, f'echo "test" > {PROJECT_FILE}')


def test_redirect_gt_nested_project_file_allowed(sg):
    """echo ... > project/src/output.txt must be allowed."""
    assert allow(sg, f'echo "test" > {PROJECT_NESTED}')


def test_redirect_append_project_file_allowed(sg):
    """echo ... >> project/file.txt must be allowed (append form)."""
    assert allow(sg, f'echo "test" >> {PROJECT_FILE}')


def test_redirect_append_nested_project_file_allowed(sg):
    """echo ... >> project/src/output.txt must be allowed (append form)."""
    assert allow(sg, f'echo "append" >> {PROJECT_NESTED}')


def test_redirect_fd_prefixed_project_allowed(sg):
    """1> fd-prefixed redirect to project folder must be allowed."""
    assert allow(sg, f'echo "test" 1> {PROJECT_FILE}')


def test_redirect_fd_prefixed_append_project_allowed(sg):
    """1>> fd-prefixed append redirect to project folder must be allowed."""
    assert allow(sg, f'echo "test" 1>> {PROJECT_FILE}')


# ---------------------------------------------------------------------------
# 2. Shell redirection > to restricted zones — denied
# ---------------------------------------------------------------------------

def test_redirect_gt_github_denied(sg):
    """echo ... > .github/file.txt must be denied."""
    assert deny(sg, f'echo "evil" > {GITHUB_FILE}')


def test_redirect_gt_vscode_denied(sg):
    """echo ... > .vscode/settings.json must be denied."""
    assert deny(sg, f'echo "evil" > {VSCODE_FILE}')


def test_redirect_gt_noagentzone_denied(sg):
    """echo ... > noagentzone/secret.txt must be denied."""
    assert deny(sg, f'echo "evil" > {NOAGENT_FILE}')


def test_redirect_append_github_denied(sg):
    """echo ... >> .github/file.txt must be denied."""
    assert deny(sg, f'echo "evil" >> {GITHUB_FILE}')


def test_redirect_variable_target_denied(sg):
    """echo ... > $var must be denied (variable path)."""
    assert deny(sg, 'echo "test" > $output_file')


# ---------------------------------------------------------------------------
# 3. Set-Content — allowed for project folder, denied for restricted zones
# ---------------------------------------------------------------------------

def test_set_content_project_file_allowed(sg):
    """Set-Content project/file.txt -Value 'test' must be allowed."""
    assert allow(sg, f"set-content {PROJECT_FILE} -value 'test'")


def test_set_content_nested_project_allowed(sg):
    """Set-Content project/src/output.txt must be allowed."""
    assert allow(sg, f"set-content {PROJECT_NESTED} 'hello world'")


def test_set_content_with_path_flag_allowed(sg):
    """Set-Content -Path project/file.txt -Value 'test' must be allowed."""
    assert allow(sg, f"set-content -path {PROJECT_FILE} -value 'test'")


def test_set_content_github_denied(sg):
    """Set-Content targeting .github/ must be denied."""
    assert deny(sg, f"set-content {GITHUB_FILE} 'evil'")


def test_set_content_vscode_denied(sg):
    """Set-Content targeting .vscode/ must be denied."""
    assert deny(sg, f"set-content {VSCODE_FILE} 'evil'")


def test_set_content_variable_path_denied(sg):
    """Set-Content with variable path must be denied."""
    assert deny(sg, "set-content $path -value 'test'")


# ---------------------------------------------------------------------------
# 4. Set-Content alias sc — allowed for project folder, denied otherwise
# ---------------------------------------------------------------------------

def test_sc_alias_project_allowed(sg):
    """sc (Set-Content alias) targeting project folder must be allowed."""
    assert allow(sg, f"sc {PROJECT_FILE} 'hello'")


def test_sc_alias_github_denied(sg):
    """sc targeting .github/ must be denied."""
    assert deny(sg, f"sc {GITHUB_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 5. Add-Content — allowed for project folder, denied for restricted zones
# ---------------------------------------------------------------------------

def test_add_content_project_file_allowed(sg):
    """Add-Content project/file.txt must be allowed."""
    assert allow(sg, f"add-content {PROJECT_FILE} 'append line'")


def test_add_content_nested_project_allowed(sg):
    """Add-Content project/src/output.txt must be allowed."""
    assert allow(sg, f"add-content {PROJECT_NESTED} 'new line'")


def test_add_content_github_denied(sg):
    """Add-Content targeting .github/ must be denied."""
    assert deny(sg, f"add-content {GITHUB_FILE} 'evil'")


def test_add_content_vscode_denied(sg):
    """Add-Content targeting .vscode/ must be denied."""
    assert deny(sg, f"add-content {VSCODE_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 6. Add-Content alias ac
# ---------------------------------------------------------------------------

def test_ac_alias_project_allowed(sg):
    """ac (Add-Content alias) targeting project folder must be allowed."""
    assert allow(sg, f"ac {PROJECT_FILE} 'hello'")


def test_ac_alias_github_denied(sg):
    """ac targeting .github/ must be denied."""
    assert deny(sg, f"ac {GITHUB_FILE} 'evil'")


# ---------------------------------------------------------------------------
# 7. Out-File — allowed for project folder, denied for restricted zones
# ---------------------------------------------------------------------------

def test_out_file_project_allowed(sg):
    """Out-File targeting project folder must be allowed."""
    assert allow(sg, f"out-file -filepath {PROJECT_FILE} -inputobject 'test'")


def test_out_file_positional_project_allowed(sg):
    """Out-File with positional path targeting project folder must be allowed."""
    assert allow(sg, f"out-file {PROJECT_FILE}")


def test_out_file_nested_project_allowed(sg):
    """Out-File targeting nested project path must be allowed."""
    assert allow(sg, f"out-file -filepath {PROJECT_NESTED}")


def test_out_file_github_denied(sg):
    """Out-File targeting .github/ must be denied."""
    assert deny(sg, f"out-file -filepath {GITHUB_FILE}")


def test_out_file_vscode_denied(sg):
    """Out-File targeting .vscode/ must be denied."""
    assert deny(sg, f"out-file {VSCODE_FILE}")


# ---------------------------------------------------------------------------
# 8. Copy-Item — both source and dest in project folder allowed
# ---------------------------------------------------------------------------

def test_copy_item_project_to_project_allowed(sg):
    """Copy-Item with both paths in project folder must be allowed."""
    assert allow(sg, f"copy-item {PROJECT_FILE} project/file_copy.txt")


def test_copy_item_nested_project_allowed(sg):
    """Copy-Item project/src.txt project/dest.txt must be allowed."""
    assert allow(sg, "copy-item project/src.txt project/dest.txt")


def test_copy_item_github_source_denied(sg):
    """Copy-Item with .github/ source must be denied."""
    assert deny(sg, f"copy-item {GITHUB_FILE} {PROJECT_FILE}")


def test_copy_item_github_dest_denied(sg):
    """Copy-Item with .github/ destination must be denied."""
    assert deny(sg, f"copy-item {PROJECT_FILE} {GITHUB_FILE}")


def test_copy_item_vscode_denied(sg):
    """Copy-Item targeting .vscode/ must be denied."""
    assert deny(sg, f"copy-item {PROJECT_FILE} {VSCODE_FILE}")


# ---------------------------------------------------------------------------
# 9. Move-Item — both source and dest in project folder allowed
# ---------------------------------------------------------------------------

def test_move_item_project_to_project_allowed(sg):
    """Move-Item with both paths in project folder must be allowed."""
    assert allow(sg, f"move-item {PROJECT_FILE} project/file_new.txt")


def test_move_item_nested_project_allowed(sg):
    """Move-Item project/old.txt project/new.txt must be allowed."""
    assert allow(sg, "move-item project/old.txt project/new.txt")


def test_move_item_github_source_denied(sg):
    """Move-Item with .github/ source must be denied."""
    assert deny(sg, f"move-item {GITHUB_FILE} {PROJECT_FILE}")


def test_move_item_github_dest_denied(sg):
    """Move-Item with .github/ destination must be denied."""
    assert deny(sg, f"move-item {PROJECT_FILE} {GITHUB_FILE}")


# ---------------------------------------------------------------------------
# 10. Project-folder fallback for write cmdlets (multi-segment relative paths)
#     Simulates CWD inside project folder — src/output.txt should resolve to
#     project/src/output.txt via _try_project_fallback.
# ---------------------------------------------------------------------------

def test_set_content_relative_multi_segment_fallback_allowed(sg):
    """Set-Content src/output.txt with project fallback must be allowed."""
    assert allow(sg, "set-content src/output.txt 'test'")


def test_add_content_relative_multi_segment_fallback_allowed(sg):
    """Add-Content src/log.txt with project fallback must be allowed."""
    assert allow(sg, "add-content src/log.txt 'entry'")


def test_out_file_relative_multi_segment_fallback_allowed(sg):
    """Out-File src/report.txt with project fallback must be allowed."""
    assert allow(sg, "out-file src/report.txt")


def test_copy_item_relative_multi_segment_fallback_allowed(sg):
    """Copy-Item src/a.txt src/b.txt with project fallback must be allowed."""
    assert allow(sg, "copy-item src/a.txt src/b.txt")


def test_move_item_relative_multi_segment_fallback_allowed(sg):
    """Move-Item src/old.txt src/new.txt with project fallback must be allowed."""
    assert allow(sg, "move-item src/old.txt src/new.txt")


# ---------------------------------------------------------------------------
# 11. Project-folder fallback for redirect targets (multi-segment)
# ---------------------------------------------------------------------------

def test_redirect_relative_multi_segment_fallback_allowed(sg):
    """echo ... > src/output.txt (project fallback) must be allowed."""
    assert allow(sg, "echo 'test' > src/output.txt")


def test_redirect_append_relative_multi_segment_fallback_allowed(sg):
    """echo ... >> src/log.txt (project fallback) must be allowed."""
    assert allow(sg, "echo 'entry' >> src/log.txt")


# ---------------------------------------------------------------------------
# 12. Non-path-like bare filenames are not zone-checked (by design)
#     _is_path_like returns False for tokens with no slash, no leading dot,
#     and no '..' — so bare_file.txt is not classified and is allowed.
# ---------------------------------------------------------------------------

def test_set_content_bare_filename_not_path_like_allowed(sg):
    """Set-Content bare_file.txt is allowed: bare names are not path-like tokens."""
    # bare_file.txt has no slash or leading dot — _is_path_like returns False
    # so no zone check is applied; this is by design for non-structured names.
    assert allow(sg, "set-content bare_file.txt 'test'")


def test_redirect_bare_filename_not_path_like_allowed(sg):
    """Redirect to bare_file.txt is allowed: bare names are not path-like tokens."""
    # bare_file.txt has no slash or leading dot — _is_path_like returns False
    # so no zone check is applied for the redirect target.
    assert allow(sg, "echo 'test' > bare_file.txt")


# ---------------------------------------------------------------------------
# 13. Embedded redirect form (e.g. 1>file.txt combined token) security
# ---------------------------------------------------------------------------

def test_embedded_redirect_github_denied(sg):
    """Embedded redirect token targeting .github/ must be denied."""
    assert deny(sg, "echo evil 1>.github/config")


def test_embedded_redirect_project_path_allowed(sg):
    """Embedded redirect token targeting project/file.txt must be allowed."""
    assert allow(sg, "echo test 1>project/file.txt")


# ---------------------------------------------------------------------------
# 14. Edge cases — ensure existing security is not weakened
# ---------------------------------------------------------------------------

def test_set_content_traversal_github_denied(sg):
    """Set-Content with path traversal targeting .github/ must be denied."""
    assert deny(sg, "set-content project/../.github/evil.txt 'bad'")


def test_copy_item_traversal_github_denied(sg):
    """Copy-Item with .. traversal targeting .github/ must be denied."""
    assert deny(sg, "copy-item project/src.txt project/../.github/evil.txt")


def test_redirect_traversal_github_denied(sg):
    """Redirect with .. traversal targeting .github/ must be denied."""
    assert deny(sg, "echo bad > project/../.github/evil.txt")
