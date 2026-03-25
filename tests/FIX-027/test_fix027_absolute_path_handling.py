"""FIX-027: Verify zone_classifier.py handles absolute paths via pathlib."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_zone_classifier_method1_uses_pathlib():
    """zone_classifier.py must use pathlib for path handling."""
    zc_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    assert zc_path.exists(), "zone_classifier.py must exist"
    
    content = zc_path.read_text(encoding="utf-8")
    assert "from pathlib" in content or "import pathlib" in content, (
        "zone_classifier.py must import pathlib"
    )

def test_zone_classifier_has_relative_to_for_windows():
    """zone_classifier.py should use relative_to for Windows absolute paths."""
    zc_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    content = zc_path.read_text(encoding="utf-8")
    
    # relative_to is the key method for resolving absolute paths cross-platform
    assert content.count("relative_to") >= 1, (
        "zone_classifier.py must use relative_to() at least once"
    )
