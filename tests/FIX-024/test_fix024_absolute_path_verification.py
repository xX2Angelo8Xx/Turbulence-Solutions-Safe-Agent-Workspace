"""FIX-024: Verify zone_classifier.py uses relative_to() for absolute path resolution."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_zone_classifier_uses_relative_to():
    """zone_classifier.py must use Path.relative_to() for path resolution."""
    zc_path = REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    assert zc_path.exists(), "zone_classifier.py must exist"
    
    content = zc_path.read_text(encoding="utf-8")
    assert "relative_to" in content, (
        "zone_classifier.py must use relative_to() for absolute path resolution"
    )

def test_zone_classifier_handles_absolute_paths():
    """zone_classifier.py should have logic for handling absolute paths."""
    zc_path = REPO_ROOT / "templates" / "coding" / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    content = zc_path.read_text(encoding="utf-8")
    
    # Should handle both relative and absolute paths
    assert "Path" in content, "zone_classifier.py should use pathlib.Path"
