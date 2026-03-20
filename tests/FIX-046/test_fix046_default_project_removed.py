"""FIX-046: Verify Default-Project/ is removed and templates/coding/ exists."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_default_project_removed():
    """Default-Project/ directory must not exist at repo root."""
    default_project = REPO_ROOT / "Default-Project"
    assert not default_project.exists(), (
        "Default-Project/ should have been removed by FIX-046"
    )

def test_templates_coding_exists():
    """templates/coding/ must exist as the replacement."""
    templates = REPO_ROOT / "templates" / "coding"
    assert templates.exists(), "templates/coding/ must exist"
    
    # Should have content
    files = list(templates.rglob("*"))
    assert len(files) > 0, "templates/coding/ must not be empty"
