"""Tests for FIX-104: Verify version-hardcoded test assertions are fixed.

Validates that the affected test files no longer contain hardcoded stale
version strings and use CURRENT_VERSION from version_utils instead.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

STALE_VERSIONS = [
    "3.2.3",
    "3.2.4",
    "3.2.6",
    "3.3.1",
]

AFFECTED_FILES = {
    "tests/FIX-077/test_fix077_version_322.py": "3.2.3",
    "tests/FIX-078/test_fix078_version_323.py": "3.2.4",
    "tests/FIX-078/test_fix078_edge_cases.py": "3.2.4",
    "tests/FIX-088/test_fix088_version_bump.py": "3.2.6",
    "tests/FIX-088/test_fix088_edge_cases.py": "3.2.6",
    "tests/FIX-090/test_fix090_version_bump.py": "3.3.1",
    "tests/FIX-090/test_fix090_edge_cases.py": "3.3.1",
    "tests/INS-029/test_ins029_version_bump.py": "3.2.4",
}


def test_affected_files_no_hardcoded_expected_version() -> None:
    """None of the fixed test files may still use EXPECTED_VERSION = '<old_version>'."""
    violations = []
    for rel_path, stale_ver in AFFECTED_FILES.items():
        path = REPO_ROOT / rel_path
        assert path.exists(), f"Test file not found: {rel_path}"
        content = path.read_text(encoding="utf-8")
        bad_pattern = f'EXPECTED_VERSION = "{stale_ver}"'
        if bad_pattern in content:
            violations.append(f"{rel_path}: still contains {bad_pattern!r}")
    assert not violations, "Stale EXPECTED_VERSION found:\n" + "\n".join(violations)


def test_affected_files_use_current_version() -> None:
    """Affected test files must import CURRENT_VERSION from version_utils."""
    for rel_path in AFFECTED_FILES:
        path = REPO_ROOT / rel_path
        content = path.read_text(encoding="utf-8")
        assert "from tests.shared.version_utils import CURRENT_VERSION" in content, (
            f"{rel_path} does not import CURRENT_VERSION from version_utils"
        )


def test_fix047_uses_standard_import() -> None:
    """FIX-047 test must use standard 'from tests.shared.version_utils import' pattern."""
    path = REPO_ROOT / "tests/FIX-047/test_fix047_version.py"
    content = path.read_text(encoding="utf-8")
    assert "from tests.shared.version_utils import CURRENT_VERSION" in content, (
        "FIX-047 does not use standard version_utils import"
    )
    assert "sys.path.insert" not in content, (
        "FIX-047 still uses sys.path.insert workaround"
    )


def test_fix070_updated_version_assertion() -> None:
    """FIX-070 must assert CURRENT_VERSION == '3.4.0', not '3.2.3'."""
    path = REPO_ROOT / "tests/FIX-070/test_fix070_version_bump.py"
    content = path.read_text(encoding="utf-8")
    assert "== \"3.2.3\"" not in content, "FIX-070 still hardcodes '3.2.3'"
    assert "3.4.0" in content, "FIX-070 doesn't reference 3.4.0"


def test_fix019_no_minor_zero_assertion() -> None:
    """FIX-019 edge cases must not assert minor version == 0."""
    path = REPO_ROOT / "tests/FIX-019/test_fix019_edge_cases.py"
    content = path.read_text(encoding="utf-8")
    assert 'new_parts[1] == 0' not in content, (
        "FIX-019 still asserts minor version must be 0 (invalid for v3.3.11)"
    )


def test_fix036_no_hardcoded_version_in_arch_assertion() -> None:
    """FIX-036 architecture test must not assert '2.1.0' in architecture.md."""
    path = REPO_ROOT / "tests/FIX-036/test_fix036_version_consistency.py"
    content = path.read_text(encoding="utf-8")
    assert 'assert "2.1.0" in text' not in content, (
        "FIX-036 still asserts '2.1.0' in architecture.md text"
    )
