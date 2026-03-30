"""
Tests for DOC-032: Fix copilot-instructions.md stale limitations.

Verifies that the stale memory tool limitation row has been removed from
templates/agent-workbench/.github/instructions/copilot-instructions.md
"""
import pathlib

INSTRUCTIONS_FILE = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


def _read_file():
    return INSTRUCTIONS_FILE.read_text(encoding="utf-8")


def _limitations_section(content: str) -> str:
    """Extract the Known Tool Limitations section text."""
    start = content.find("## Known Tool Limitations")
    if start == -1:
        return ""
    # Find the next h2 heading after the section start
    next_h2 = content.find("\n## ", start + 1)
    if next_h2 == -1:
        return content[start:]
    return content[start:next_h2]


def test_file_exists():
    assert INSTRUCTIONS_FILE.exists(), (
        f"copilot-instructions.md not found at {INSTRUCTIONS_FILE}"
    )


def test_blocked_by_design_not_present():
    content = _read_file()
    assert "blocked by design" not in content, (
        "Stale text 'blocked by design' still present in copilot-instructions.md"
    )


def test_memory_not_in_limitations_table():
    content = _read_file()
    section = _limitations_section(content)
    assert section, "Known Tool Limitations section not found"
    # The word 'memory' should not appear in the table rows of this section
    for line in section.splitlines():
        if line.startswith("|") and "memory" in line.lower():
            raise AssertionError(
                f"'memory' still appears in a limitations table row: {line!r}"
            )


def test_known_limitations_section_exists():
    content = _read_file()
    assert "## Known Tool Limitations" in content, (
        "Known Tool Limitations section is missing"
    )


def test_out_file_row_present():
    content = _read_file()
    section = _limitations_section(content)
    assert "Out-File" in section, (
        "Expected 'Out-File' row missing from Known Tool Limitations table"
    )


def test_dir_ls_row_present():
    content = _read_file()
    section = _limitations_section(content)
    assert "`dir`" in section or "dir" in section, (
        "Expected 'dir' row missing from Known Tool Limitations table"
    )


def test_pip_install_row_present():
    content = _read_file()
    section = _limitations_section(content)
    assert "pip install" in section, (
        "Expected 'pip install' row missing from Known Tool Limitations table"
    )


def test_venv_activation_row_present():
    content = _read_file()
    section = _limitations_section(content)
    assert "venv" in section.lower(), (
        "Expected venv activation row missing from Known Tool Limitations table"
    )
