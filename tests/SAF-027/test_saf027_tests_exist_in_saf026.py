"""SAF-027: Verify python -c scanning tests exist in tests/SAF-026/ (co-located by design)."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_saf026_test_dir_exists():
    """tests/SAF-026/ must exist (SAF-027 tests co-located there)."""
    test_dir = REPO_ROOT / "tests" / "SAF-026"
    assert test_dir.exists(), "tests/SAF-026/ must exist"

def test_saf026_has_python_c_scanning_tests():
    """tests/SAF-026/ must contain python -c scanning test functions."""
    test_dir = REPO_ROOT / "tests" / "SAF-026"
    test_files = list(test_dir.glob("test_*.py"))
    assert test_files, "tests/SAF-026/ must contain test_*.py files"
    
    found_scan_test = False
    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        if "python" in content.lower() and ("scan" in content.lower() or "-c" in content):
            found_scan_test = True
            break
    
    assert found_scan_test, (
        "tests/SAF-026/ must contain tests related to python -c scanning"
    )
