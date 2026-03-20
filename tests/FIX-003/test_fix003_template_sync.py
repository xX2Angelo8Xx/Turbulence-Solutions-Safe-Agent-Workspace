"""FIX-003: Verify key files in templates/coding/ exist and are non-empty."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates" / "coding"

KEY_FILES = [
    ".github/hooks/scripts/security_gate.py",
    ".github/hooks/scripts/zone_classifier.py",
    ".github/hooks/require-approval.json",
    "README.md",
]

def test_template_dir_exists():
    """templates/coding/ must exist."""
    assert TEMPLATE_DIR.exists(), "templates/coding/ directory must exist"

def test_key_files_exist_and_nonempty():
    """Key template files must exist and be non-empty."""
    for rel_path in KEY_FILES:
        full_path = TEMPLATE_DIR / rel_path
        assert full_path.exists(), f"templates/coding/{rel_path} must exist"
        assert full_path.stat().st_size > 0, f"templates/coding/{rel_path} must be non-empty"
