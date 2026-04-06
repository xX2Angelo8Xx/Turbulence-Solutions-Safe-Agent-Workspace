"""
FIX-114: CI regression tests.

These tests verify the three CI fixes:
  1. MANIFEST.json hashes match current template files (CRLF->LF normalisation)
  2. _init_git_repository() sets git user config before committing
  3. require-approval.sh uses POSIX grep (no -qP) for backtick detection
"""

import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]


def test_manifest_check_passes():
    """Fix 1: MANIFEST.json hashes should match LF-normalised template files."""
    result = subprocess.run(
        [sys.executable, "scripts/generate_manifest.py", "--check"],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Manifest check failed:\n{result.stdout}\n{result.stderr}"


def test_git_init_sets_user_config():
    """Fix 2: _init_git_repository() must configure user.name and user.email."""
    src = (WORKSPACE / "src" / "launcher" / "core" / "project_creator.py").read_text(encoding="utf-8")
    assert 'git", "config", "user.name' in src, "user.name config not found in _init_git_repository"
    assert 'git", "config", "user.email' in src, "user.email config not found in _init_git_repository"


def test_require_approval_no_pcre_grep():
    """Fix 3: require-approval.sh must not use grep -qP (PCRE) for backtick detection."""
    script = (
        WORKSPACE / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "require-approval.sh"
    ).read_text(encoding="utf-8")
    assert "grep -qP" not in script, "grep -qP (PCRE) still present in require-approval.sh"
    # Confirm the POSIX replacement is in place
    assert "grep -qE '`[a-zA-Z_0-9]'" in script, "POSIX grep replacement for backtick not found"
