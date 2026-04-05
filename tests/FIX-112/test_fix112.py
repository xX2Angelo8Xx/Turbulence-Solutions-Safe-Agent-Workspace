"""
FIX-112 — Verify that tests/SAF-074/test_saf074.py contains a module-level
pytestmark that skips all tests when PowerShell is not available.
"""
import ast
from pathlib import Path

_SAF074_FILE = Path(__file__).resolve().parents[2] / "tests" / "SAF-074" / "test_saf074.py"


def _load_source() -> str:
    return _SAF074_FILE.read_text(encoding="utf-8")


def test_pytestmark_present():
    """test_saf074.py must define a module-level pytestmark variable."""
    source = _load_source()
    tree = ast.parse(source)
    assigns = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "pytestmark"
            for t in node.targets
        )
    ]
    assert assigns, "pytestmark not found in tests/SAF-074/test_saf074.py"


def test_pytestmark_checks_powershell():
    """pytestmark must reference the string 'powershell'."""
    source = _load_source()
    assert "powershell" in source, (
        "tests/SAF-074/test_saf074.py does not check for 'powershell'"
    )


def test_pytestmark_checks_pwsh():
    """pytestmark must reference the string 'pwsh' (for pwsh on Linux/macOS)."""
    source = _load_source()
    assert "pwsh" in source, (
        "tests/SAF-074/test_saf074.py does not check for 'pwsh'"
    )


def test_shutil_which_used():
    """shutil.which must be used to detect PowerShell availability."""
    source = _load_source()
    assert "shutil.which" in source, (
        "tests/SAF-074/test_saf074.py does not use shutil.which"
    )
