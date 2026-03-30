"""DOC-034 Tester edge-case tests — Update orchestrator release instructions.

Additional tests beyond the Developer's suite covering:
- Correct Windows venv path in command examples
- All 5 version-file names present in the CI/CD section
- scripts/release.py actually exists at the referenced path
- Valid YAML frontmatter in both agent files
- No deprecated manual version-editing instructions remain
- Key structural headings are intact in both files
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ORCHESTRATOR = REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md"
CLOUD_ORCHESTRATOR = REPO_ROOT / ".github" / "agents" / "CLOUD-orchestrator.agent.md"
RELEASE_SCRIPT = REPO_ROOT / "scripts" / "release.py"

AGENT_FILES = [ORCHESTRATOR, CLOUD_ORCHESTRATOR]

VERSION_FILES_EXPECTED = [
    "config.py",
    "pyproject.toml",
    "setup.iss",
    "build_dmg.sh",
    "build_appimage.sh",
]

EXPECTED_HEADINGS = [
    "## Startup",
    "## Core Workflow",
    "## WP Finalization",
    "## CI/CD Pipeline Trigger",
    "## WP Splitting",
    "## Adding New Workpackages",
    "## Constraints",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _cicd_section(content: str) -> str:
    """Extract the CI/CD Pipeline Trigger section from file content."""
    match = re.search(
        r"(## CI/CD Pipeline Trigger.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "CI/CD Pipeline Trigger section not found"
    return match.group(1)


# ---------------------------------------------------------------------------
# Test: actual scripts/release.py file exists at the referenced path
# ---------------------------------------------------------------------------

def test_release_script_file_exists():
    """scripts/release.py must exist at the path referenced in the documentation."""
    assert RELEASE_SCRIPT.exists(), (
        f"scripts/release.py not found at expected location: {RELEASE_SCRIPT}"
    )


# ---------------------------------------------------------------------------
# Test: Windows venv command syntax used in the CI/CD section
# ---------------------------------------------------------------------------

def test_cicd_section_uses_venv_scripts_python_path():
    """.venv\\Scripts\\python must be used in the CI/CD release command examples."""
    for path in AGENT_FILES:
        section = _cicd_section(_read(path))
        assert r".venv\Scripts\python" in section, (
            f"{path.name} CI/CD section does not use .venv\\Scripts\\python "
            "in release script command example"
        )


# ---------------------------------------------------------------------------
# Test: all 5 version file names mentioned in the CI/CD section
# ---------------------------------------------------------------------------

def test_cicd_section_names_all_five_version_files():
    """The CI/CD section must explicitly name all 5 version files."""
    for path in AGENT_FILES:
        section = _cicd_section(_read(path))
        for vfile in VERSION_FILES_EXPECTED:
            assert vfile in section, (
                f"{path.name} CI/CD section does not mention version file '{vfile}'"
            )


# ---------------------------------------------------------------------------
# Test: no deprecated manual version-editing workflow
# ---------------------------------------------------------------------------

def test_no_deprecated_manual_version_edit_instructions():
    """Neither file must reference the old manual version-editing workflow."""
    deprecated_patterns = [
        "manually edit",
        "edit config.py",
        "edit pyproject.toml",
        "open config.py",
        "open pyproject.toml",
    ]
    for path in AGENT_FILES:
        content = _read(path).lower()
        for pattern in deprecated_patterns:
            assert pattern not in content, (
                f"{path.name} contains deprecated instruction: '{pattern}'"
            )


# ---------------------------------------------------------------------------
# Test: valid YAML frontmatter (starts and ends with ---)
# ---------------------------------------------------------------------------

def test_agent_files_have_valid_yaml_frontmatter():
    """Both agent files must have valid YAML frontmatter delimited by ---."""
    for path in AGENT_FILES:
        content = _read(path)
        assert content.startswith("---"), (
            f"{path.name} does not begin with YAML frontmatter delimiter '---'"
        )
        # Find second --- after the opening one
        second_delim = content.find("---", 3)
        assert second_delim != -1, (
            f"{path.name} is missing the closing YAML frontmatter delimiter '---'"
        )


# ---------------------------------------------------------------------------
# Test: all key structural headings still present (no accidental deletion)
# ---------------------------------------------------------------------------

def test_all_structural_headings_present_in_both_files():
    """All expected top-level sections must still exist in both agent files."""
    for path in AGENT_FILES:
        content = _read(path)
        for heading in EXPECTED_HEADINGS:
            assert heading in content, (
                f"{path.name} is missing structural heading: '{heading}'"
            )


# ---------------------------------------------------------------------------
# Test: primary CI/CD subsection is the Release Script (not Fallback)
# ---------------------------------------------------------------------------

def test_primary_method_heading_is_release_script():
    """The first named subsection in CI/CD section must be Primary Method (Release Script)."""
    for path in AGENT_FILES:
        section = _cicd_section(_read(path))
        # Find positions of both subsections
        primary_pos = section.find("### Primary Method")
        fallback_pos = section.find("### Fallback")
        assert primary_pos != -1, (
            f"{path.name} CI/CD section missing '### Primary Method' subsection"
        )
        assert fallback_pos != -1, (
            f"{path.name} CI/CD section missing '### Fallback' subsection"
        )
        assert primary_pos < fallback_pos, (
            f"{path.name} Fallback subsection appears before Primary Method — ordering is wrong"
        )


# ---------------------------------------------------------------------------
# Test: git tag -a must not appear in primary section of either file
# ---------------------------------------------------------------------------

def test_git_tag_a_only_in_fallback_not_primary():
    """git tag -a must not appear in the Primary Method subsection."""
    for path in AGENT_FILES:
        content = _read(path)
        section = _cicd_section(content)
        # Split at the Fallback heading to isolate the primary part
        parts = re.split(r"### Fallback", section, maxsplit=1)
        primary_part = parts[0]
        assert "git tag -a" not in primary_part, (
            f"{path.name}: 'git tag -a' found in primary CI/CD instructions "
            "(should only appear in Fallback subsection)"
        )
