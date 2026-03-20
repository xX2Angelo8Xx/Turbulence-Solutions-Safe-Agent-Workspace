"""FIX-001: Verify GUI-004 test uses call_args_list pattern (not bare call_args)."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_gui004_test_uses_call_args_list():
    """GUI-004 test must use call_args_list, not bare call_args."""
    test_dir = REPO_ROOT / "tests" / "GUI-004"
    assert test_dir.exists(), "tests/GUI-004/ directory must exist"
    test_files = list(test_dir.glob("test_*.py"))
    assert test_files, "tests/GUI-004/ must contain test_*.py files"
    
    found_call_args_list = False
    for tf in test_files:
        content = tf.read_text(encoding="utf-8")
        if "call_args_list" in content:
            found_call_args_list = True
            break
    
    assert found_call_args_list, (
        "GUI-004 tests should use call_args_list pattern for mock isolation"
    )
