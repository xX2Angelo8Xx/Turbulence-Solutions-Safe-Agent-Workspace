"""
INS-012 — .gitignore Configuration Tests

Verifies that .gitignore exists at the repository root and contains
all required exclusion patterns.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

REQUIRED_PATTERNS = [
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    ".eggs/",
    "*.egg-info/",
    "dist/",
    "build/",
    ".pytest_cache/",
    ".venv/",
    "env/",
    "venv/",
    "*.spec",
    ".DS_Store",
    "Thumbs.db",
]


def _gitignore_lines() -> list[str]:
    return GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()


def _active_patterns() -> list[str]:
    lines = _gitignore_lines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


# ── Existence ─────────────────────────────────────────────────────────────────

def test_gitignore_exists():
    assert GITIGNORE_PATH.is_file(), ".gitignore not found at repository root"


# ── Individual required patterns ──────────────────────────────────────────────

def test_pycache_excluded():
    assert "__pycache__/" in _active_patterns()


def test_pyc_excluded():
    assert "*.pyc" in _active_patterns()


def test_pyo_excluded():
    assert "*.pyo" in _active_patterns()


def test_eggs_dir_excluded():
    assert ".eggs/" in _active_patterns()


def test_egg_info_excluded():
    assert "*.egg-info/" in _active_patterns()


def test_dist_excluded():
    assert "dist/" in _active_patterns()


def test_build_excluded():
    assert "build/" in _active_patterns()


def test_pytest_cache_excluded():
    assert ".pytest_cache/" in _active_patterns()


def test_venv_excluded():
    assert ".venv/" in _active_patterns()


def test_env_excluded():
    assert "env/" in _active_patterns()


def test_venv_plain_excluded():
    assert "venv/" in _active_patterns()


def test_spec_excluded():
    assert "*.spec" in _active_patterns()


def test_ds_store_excluded():
    assert ".DS_Store" in _active_patterns()


def test_thumbs_db_excluded():
    assert "Thumbs.db" in _active_patterns()


# ── Quality checks ─────────────────────────────────────────────────────────────

def test_no_duplicate_patterns():
    patterns = _active_patterns()
    seen: set[str] = set()
    duplicates: list[str] = []
    for p in patterns:
        if p in seen:
            duplicates.append(p)
        seen.add(p)
    assert not duplicates, f"Duplicate patterns found in .gitignore: {duplicates}"


# ── Git integration ────────────────────────────────────────────────────────────

def test_gitignore_git_recognises_pyc():
    """git check-ignore must report a .pyc path as ignored."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "some/module.pyc"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode == 0, (
        "git check-ignore did not recognise 'some/module.pyc' as ignored — "
        "*.pyc rule may be missing or malformed"
    )


def test_gitignore_git_recognises_pycache():
    """git check-ignore must report a __pycache__ path as ignored."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "src/launcher/__pycache__/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode == 0, (
        "git check-ignore did not recognise 'src/launcher/__pycache__/' as ignored — "
        "__pycache__/ rule may be missing or malformed"
    )


def test_gitignore_git_recognises_spec():
    """git check-ignore must report a .spec file as ignored."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "launcher.spec"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode == 0, (
        "git check-ignore did not recognise 'launcher.spec' as ignored — "
        "*.spec rule may be missing or malformed"
    )


def test_gitignore_git_recognises_venv():
    """git check-ignore must report a .venv directory as ignored."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".venv/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    assert result.returncode == 0, (
        "git check-ignore did not recognise '.venv/' as ignored — "
        ".venv/ rule may be missing or malformed"
    )


def test_pycache_not_tracked_in_git_index():
    """No __pycache__ paths should currently be tracked in the git index."""
    result = subprocess.run(
        ["git", "ls-files", "--", "*__pycache__*"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    tracked = result.stdout.strip()
    assert not tracked, (
        f"The following __pycache__ paths are still tracked in the git index:\n{tracked}\n"
        "Run: git rm -r --cached <path>"
    )


def test_egg_info_not_tracked_in_git_index():
    """No .egg-info paths should currently be tracked in the git index."""
    result = subprocess.run(
        ["git", "ls-files", "--", "*.egg-info"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    tracked = result.stdout.strip()
    assert not tracked, (
        f"The following .egg-info paths are still tracked in the git index:\n{tracked}\n"
        "Run: git rm -r --cached <path>"
    )
