"""FIX-005: Verify .gitignore contains *.spec pattern."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_gitignore_contains_spec_pattern():
    """.gitignore must contain *.spec pattern."""
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore must exist"
    
    content = gitignore.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    
    assert "*.spec" in lines, ".gitignore must contain '*.spec' pattern"

def test_launcher_spec_exception_exists():
    """.gitignore should have !launcher.spec exception."""
    gitignore = REPO_ROOT / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    
    assert "!launcher.spec" in lines, ".gitignore should have '!launcher.spec' exception"
