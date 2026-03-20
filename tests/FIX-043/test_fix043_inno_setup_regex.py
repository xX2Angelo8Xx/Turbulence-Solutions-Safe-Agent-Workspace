"""FIX-043: Verify INS-005 tests use correct 'filesandordirs' spelling."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_ins005_tests_contain_filesandordirs():
    """tests/INS-005/ test files must contain 'filesandordirs'."""
    test_dir = REPO_ROOT / "tests" / "INS-005"
    assert test_dir.exists(), "tests/INS-005/ must exist"
    
    test_files = list(test_dir.glob("test_*.py"))
    assert test_files, "tests/INS-005/ must contain test_*.py files"
    
    found = False
    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        if "filesandordirs" in content:
            found = True
            break
    
    assert found, (
        "At least one INS-005 test must reference 'filesandordirs' (correct spelling)"
    )
