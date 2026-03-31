"""
FIX-089 — Tester edge-case tests for the [InstallDelete] directive in setup.iss.

Focus areas:
- The directive is scoped precisely (not too broad, not too narrow)
- Other bundled data directories are NOT accidentally deleted
- Path uses backslashes (Inno Setup requirement)
- No duplicate [InstallDelete] entries
- [UninstallDelete] section is untouched
- Section syntax is valid (no duplicate section headers)
"""

import re
from pathlib import Path

SETUP_ISS = (
    Path(__file__).parent.parent.parent
    / "src" / "installer" / "windows" / "setup.iss"
)


def _read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Scope precision: too broad deletions must not be present
# ---------------------------------------------------------------------------

def test_install_delete_does_not_target_internal_directory():
    """[InstallDelete] must NOT wipe {app}\\_internal — only the templates sub-dir."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    # A Name pointing at bare {app}\_internal (without further path) would be too broad
    dangerous = re.search(r'Name:\s*"\{app\}\\_internal"', block_text)
    assert dangerous is None, (
        "[InstallDelete] must not delete the entire {app}\\_internal directory"
    )


def test_install_delete_does_not_target_app_root():
    """[InstallDelete] must NOT target {app} itself — that would delete the entire install."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    # Name: "{app}" or Name: "{app}\" would be catastrophic
    dangerous = re.search(r'Name:\s*"\{app\}\\?"(?=\s*$|\s*;)', block_text, re.MULTILINE)
    assert dangerous is None, (
        "[InstallDelete] must not target {app} root — that would delete the full installation"
    )


def test_python_embed_directory_not_in_install_delete():
    """The python-embed directory must NOT appear in [InstallDelete] — it must be preserved."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    assert "python-embed" not in block_text, (
        "[InstallDelete] must not delete python-embed — bundled Python runtime must survive upgrades"
    )


# ---------------------------------------------------------------------------
# Path correctness: backslashes, exact target
# ---------------------------------------------------------------------------

def test_install_delete_path_uses_backslashes():
    """The InstallDelete Name path must use backslashes (Inno Setup convention)."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    # If forward slashes are used, Inno Setup may not resolve the path correctly
    forward_slash_path = re.search(
        r'Name:\s*"\{app\}/[^"]*"', block_text
    )
    assert forward_slash_path is None, (
        "InstallDelete Name must use backslashes, not forward slashes"
    )


def test_install_delete_targets_internal_not_top_level_templates():
    """Must delete {app}\\_internal\\templates, NOT {app}\\templates (wrong path)."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    # Wrong path: {app}\templates (without _internal)
    wrong_path = re.search(r'Name:\s*"\{app\}\\templates"', block_text)
    assert wrong_path is None, (
        "InstallDelete must target '{app}\\_internal\\templates', not '{app}\\templates'"
    )


# ---------------------------------------------------------------------------
# No duplicates
# ---------------------------------------------------------------------------

def test_no_duplicate_install_delete_sections():
    """There must be exactly one [InstallDelete] section header in setup.iss."""
    content = _read_iss()
    occurrences = content.count("[InstallDelete]")
    assert occurrences == 1, (
        f"Expected exactly 1 [InstallDelete] section, found {occurrences}"
    )


def test_install_delete_has_exactly_one_directive():
    """The [InstallDelete] section must have exactly one active directive line."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    # Count non-empty, non-comment lines
    directive_lines = [
        line.strip() for line in block_text.splitlines()
        if line.strip() and not line.strip().startswith(";")
    ]
    assert len(directive_lines) == 1, (
        f"Expected exactly 1 directive in [InstallDelete], found {len(directive_lines)}: {directive_lines}"
    )


# ---------------------------------------------------------------------------
# [UninstallDelete] section is untouched
# ---------------------------------------------------------------------------

def test_uninstall_delete_section_still_targets_app():
    """[UninstallDelete] must still have a directive targeting {app} (unchanged)."""
    content = _read_iss()
    uninstall_delete_block = re.search(
        r"\[UninstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert uninstall_delete_block is not None, "[UninstallDelete] section missing"
    block_text = uninstall_delete_block.group(1)
    assert r'"{app}"' in block_text, (
        "[UninstallDelete] must still contain a directive for {app}"
    )


def test_uninstall_delete_section_still_targets_python_embed():
    """[UninstallDelete] must still have a directive for python-embed (unchanged)."""
    content = _read_iss()
    uninstall_delete_block = re.search(
        r"\[UninstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert uninstall_delete_block is not None, "[UninstallDelete] section missing"
    block_text = uninstall_delete_block.group(1)
    assert "python-embed" in block_text, (
        "[UninstallDelete] must still reference python-embed (was not removed by FIX-089)"
    )


# ---------------------------------------------------------------------------
# Section ordering and structure validity
# ---------------------------------------------------------------------------

def test_sections_are_well_formed():
    """All expected Inno Setup sections must be present."""
    content = _read_iss()
    required_sections = [
        "[Setup]", "[Languages]", "[Tasks]", "[InstallDelete]",
        "[Files]", "[Registry]", "[Icons]", "[Run]", "[UninstallDelete]", "[Code]"
    ]
    for section in required_sections:
        assert section in content, f"Expected section '{section}' is missing from setup.iss"


def test_install_delete_comment_references_fix089():
    """The [InstallDelete] block should include a comment referencing FIX-089."""
    content = _read_iss()
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section missing"
    block_text = install_delete_block.group(1)
    assert "FIX-089" in block_text, (
        "[InstallDelete] block must contain a comment referencing FIX-089 for traceability"
    )
