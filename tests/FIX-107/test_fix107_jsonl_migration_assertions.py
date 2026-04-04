"""FIX-107: Tests verifying the JSONL migration test assertions are correct.

Verifies that:
1. MNT-017 test uses the correct `Title` field for US JSONL records
2. MNT-022 is in ALLOWED_DIRS in MNT-021 tester edge cases
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mnt017_us_jsonl_uses_title_field():
    """The MNT-017 test should create US JSONL records with 'Title', not 'Name'."""
    test_file = REPO_ROOT / "tests" / "MNT-017" / "test_mnt017_script_migration.py"
    content = test_file.read_text(encoding="utf-8")
    assert '"Title"' in content, (
        "test_mnt017_script_migration.py must use 'Title' field for US JSONL records"
    )
    # Ensure the old incorrect field name is not used in a write_jsonl call for US
    for i, line in enumerate(content.splitlines(), 1):
        if "_write_jsonl(us_file" in line and '"Name"' in line:
            raise AssertionError(
                f"Line {i}: Found 'Name' field in US JSONL write — should be 'Title'"
            )


def test_mnt021_allowed_dirs_includes_mnt022():
    """MNT-021 tester edge cases must include MNT-022 in ALLOWED_DIRS."""
    test_file = REPO_ROOT / "tests" / "MNT-021" / "test_mnt021_tester_edge_cases.py"
    content = test_file.read_text(encoding="utf-8")
    assert '"MNT-022"' in content, (
        "test_mnt021_tester_edge_cases.py must include 'MNT-022' in ALLOWED_DIRS "
        "so the CSV retirement test is not flagged as a violation"
    )


def test_mnt_tests_all_pass():
    """Smoke test: import check that all key MNT test modules are importable."""
    import importlib.util

    mnt_dirs = [f"MNT-{n:03d}" for n in range(14, 24)]
    for d in mnt_dirs:
        test_dir = REPO_ROOT / "tests" / d
        for py_file in sorted(test_dir.glob("test_*.py")):
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                raise AssertionError(
                    f"{py_file.relative_to(REPO_ROOT)} failed to import: {e}"
                ) from e
