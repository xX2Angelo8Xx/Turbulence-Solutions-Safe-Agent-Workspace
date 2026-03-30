"""
DOC-005 Tests: Known Tool Limitations section in copilot-instructions.md
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FILE = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "instructions" / "copilot-instructions.md"
TEMPLATE_FILE = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "instructions" / "copilot-instructions.md"

HEADING = "## Known Tool Limitations"

LIMITATION_ENTRIES = [
    "Out-File",
    "dir",
    "Get-ChildItem -Recurse",
    "pip install",
    "Venv activation",
    "Venv python",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_default_project_has_known_tool_limitations_heading():
    content = _read(DEFAULT_FILE)
    assert HEADING in content, f"Heading not found in {DEFAULT_FILE}"


def test_template_has_known_tool_limitations_heading():
    content = _read(TEMPLATE_FILE)
    assert HEADING in content, f"Heading not found in {TEMPLATE_FILE}"


def test_both_files_are_identical():
    default_content = _read(DEFAULT_FILE)
    template_content = _read(TEMPLATE_FILE)
    assert default_content == template_content, (
        "templates/coding and templates/coding copilot-instructions.md are not identical"
    )


def test_table_contains_out_file_entry():
    content = _read(DEFAULT_FILE)
    assert "Out-File" in content


def test_table_contains_dir_ls_gci_entry():
    content = _read(DEFAULT_FILE)
    assert "dir" in content and "ls" in content and "Get-ChildItem" in content


def test_table_contains_gci_recurse_entry():
    content = _read(DEFAULT_FILE)
    assert "Get-ChildItem -Recurse" in content


def test_table_contains_pip_install_entry():
    content = _read(DEFAULT_FILE)
    assert "pip install" in content


def test_table_contains_venv_activation_entry():
    content = _read(DEFAULT_FILE)
    assert "Venv activation" in content


def test_table_contains_venv_python_entry():
    content = _read(DEFAULT_FILE)
    assert "Venv python" in content

