"""
DOC-031 Tester Edge Cases
Verifies accuracy requirements not covered by the developer's tests.
"""
import pathlib
import re

AGENT_RULES_PATH = (
    pathlib.Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / "Project"
    / "AGENT-RULES.md"
)


def _content() -> str:
    return AGENT_RULES_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Stale language
# ---------------------------------------------------------------------------

def test_no_permanently_off_limits_phrase():
    """'permanently off-limits' is a stale phrase — .github/ now has partial access."""
    assert "permanently off-limits" not in _content().lower(), (
        "Stale phrase 'permanently off-limits' must not appear; .github/ has partial read access"
    )


def test_no_fully_off_limits_phrase():
    """'fully off-limits' is another stale variant that must not appear."""
    assert "fully off-limits" not in _content().lower(), (
        "Stale phrase 'fully off-limits' must not appear"
    )


# ---------------------------------------------------------------------------
# Section numbering §1-§7, no §8
# ---------------------------------------------------------------------------

def test_all_seven_sections_present():
    """Sections ## 1 through ## 7 must all exist."""
    content = _content()
    for n in range(1, 8):
        assert re.search(rf"^##\s+{n}\.", content, re.MULTILINE), (
            f"Section ## {n}. is missing from AGENT-RULES.md"
        )


def test_no_section_eight():
    """§8 must not exist in any form."""
    content = _content()
    assert not re.search(r"^##\s+8\.", content, re.MULTILINE), (
        "Section ## 8. must not appear (Agent Personas section was removed)"
    )


def test_no_agent_personas_heading():
    """'Agent Personas' heading must not appear."""
    assert "Agent Personas" not in _content(), (
        "The 'Agent Personas' heading must have been removed from the document"
    )


# ---------------------------------------------------------------------------
# .github/hooks/ fully denied
# ---------------------------------------------------------------------------

def test_github_hooks_fully_denied_documented():
    """hooks/ must be explicitly documented as fully denied."""
    content = _content()
    assert "hooks/" in content, "hooks/ must be mentioned somewhere in AGENT-RULES.md"
    # The phrase must indicate it is fully denied
    assert re.search(r"hooks/.*fully denied", content, re.IGNORECASE), (
        ".github/hooks/ must be described as 'fully denied' in the document"
    )


def test_github_hooks_no_reads_or_writes():
    """The hooks/ entry must state both reads AND writes are denied."""
    content = _content()
    hooks_line = next(
        (line for line in content.splitlines() if "hooks/" in line), None
    )
    assert hooks_line is not None, "No line mentioning hooks/ found"
    assert "reads" in hooks_line.lower() or "read" in hooks_line.lower(), (
        "hooks/ entry must mention that reads are denied"
    )
    assert "writes" in hooks_line.lower() or "write" in hooks_line.lower(), (
        "hooks/ entry must mention that writes are denied"
    )


# ---------------------------------------------------------------------------
# read_file and list_dir in .github/ context
# ---------------------------------------------------------------------------

def test_read_file_mentioned_for_github_access():
    """read_file must appear in the .github/ access description."""
    content = _content()
    # Find the .github/ row in the Denied Zones table
    github_lines = [l for l in content.splitlines() if ".github/" in l]
    assert any("read_file" in l for l in github_lines), (
        "read_file must be mentioned in the .github/ access description"
    )


def test_list_dir_denied_for_github():
    """list_dir must be explicitly stated as denied for .github/."""
    content = _content()
    github_lines = [l for l in content.splitlines() if ".github/" in l]
    assert any("list_dir" in l and "denied" in l.lower() for l in github_lines), (
        "list_dir must be listed as denied in the .github/ access description"
    )


def test_list_dir_matrix_entry_denies_github():
    """The tool permission matrix list_dir row must mention .github/ is denied."""
    content = _content()
    listdir_lines = [l for l in content.splitlines() if "list_dir" in l]
    assert any(".github/" in l for l in listdir_lines), (
        "The list_dir permission matrix row must reference .github/ as denied"
    )


# ---------------------------------------------------------------------------
# Template placeholder correctness
# ---------------------------------------------------------------------------

def test_project_name_placeholder_in_paths():
    """{{PROJECT_NAME}} must appear in the file path structure example."""
    content = _content()
    # The placeholder should appear in the allowed zone path example
    assert re.search(r"\{\{PROJECT_NAME\}\}", content), (
        "{{PROJECT_NAME}} placeholder must be present"
    )


def test_workspace_name_placeholder_in_paths():
    """{{WORKSPACE_NAME}} must appear in root path examples."""
    content = _content()
    assert re.search(r"\{\{WORKSPACE_NAME\}\}", content), (
        "{{WORKSPACE_NAME}} placeholder must be present"
    )


def test_no_hardcoded_workspace_name():
    """No hardcoded workspace name like 'MyWorkspace' or 'Workspace' should replace the placeholder."""
    content = _content()
    # The path structure must use placeholders, not literal names
    assert "MyWorkspace" not in content, "Hardcoded 'MyWorkspace' must not appear"
    assert "MyProject" not in content, "Hardcoded 'MyProject' must not appear"


# ---------------------------------------------------------------------------
# cmd.exe documented (not just cmd /c)
# ---------------------------------------------------------------------------

def test_cmd_exe_in_blocked_commands():
    """cmd.exe must also be listed in blocked commands, not just cmd /c."""
    content = _content()
    assert "cmd.exe" in content, (
        "cmd.exe must appear in the blocked commands section alongside cmd /c"
    )


# ---------------------------------------------------------------------------
# System Python fallback documented
# ---------------------------------------------------------------------------

def test_system_python_fallback_documented():
    """System Python (no .venv) is an acceptable fallback and must be documented."""
    content = _content()
    # The allowed terminal commands must mention bare 'python' without .venv
    assert re.search(r"python\s+script\.py", content), (
        "System Python fallback (python script.py) must be documented as acceptable"
    )


# ---------------------------------------------------------------------------
# Memory tool present in matrix
# ---------------------------------------------------------------------------

def test_memory_tool_in_permission_matrix():
    """The memory tool must appear as 'Allowed' in the tool permission matrix."""
    content = _content()
    assert re.search(r"\*\*Memory\*\*.*Allowed|Memory.*Allowed", content, re.IGNORECASE), (
        "Memory tool must be listed as Allowed in the tool permission matrix"
    )


# ---------------------------------------------------------------------------
# All 5 blocked git operations
# ---------------------------------------------------------------------------

def test_all_five_blocked_git_operations_present():
    """All 5 blocked git operations must appear in the document."""
    content = _content()
    blocked_ops = [
        "push --force",
        "reset --hard",
        "filter-branch",
        "gc --force",
        "clean -f",
    ]
    for op in blocked_ops:
        assert op in content, f"Blocked git operation 'git {op}' must be documented"


# ---------------------------------------------------------------------------
# .vscode/ and NoAgentZone/ fully denied
# ---------------------------------------------------------------------------

def test_vscode_fully_denied():
    """.vscode/ must be documented as fully denied."""
    content = _content()
    assert ".vscode/" in content, ".vscode/ must appear in the Denied Zones section"
    vscode_lines = [l for l in content.splitlines() if ".vscode/" in l]
    assert any("denied" in l.lower() for l in vscode_lines), (
        ".vscode/ must be described as denied"
    )


def test_noagentzone_fully_denied():
    """NoAgentZone/ must be documented as fully denied."""
    content = _content()
    assert "NoAgentZone/" in content, "NoAgentZone/ must appear in the Denied Zones section"
    naz_lines = [l for l in content.splitlines() if "NoAgentZone/" in l]
    assert any("denied" in l.lower() for l in naz_lines), (
        "NoAgentZone/ must be described as denied"
    )


# ---------------------------------------------------------------------------
# Document length
# ---------------------------------------------------------------------------

def test_significant_length_reduction():
    """Document must be shorter than 160 lines (substantial reduction from the ~200-line original)."""
    lines = _content().splitlines()
    assert len(lines) < 160, (
        f"Document should be significantly shorter than the original ~200 lines; "
        f"found {len(lines)} lines"
    )
