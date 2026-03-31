"""
FIX-089: Tests verifying that setup.iss contains the [InstallDelete] directive
that removes stale template files from previous installations.
"""

import re
from pathlib import Path

SETUP_ISS = (
    Path(__file__).parent.parent.parent
    / "src" / "installer" / "windows" / "setup.iss"
)


def _read_iss() -> str:
    return SETUP_ISS.read_text(encoding="utf-8")


def test_setup_iss_exists():
    """The Inno Setup script must exist at the expected path."""
    assert SETUP_ISS.is_file(), f"setup.iss not found at {SETUP_ISS}"


def test_install_delete_section_exists():
    """[InstallDelete] section must be present in setup.iss."""
    content = _read_iss()
    assert "[InstallDelete]" in content, "[InstallDelete] section is missing from setup.iss"


def test_install_delete_targets_templates_dir():
    r"""The InstallDelete directive must target {app}\_internal\templates."""
    content = _read_iss()
    # Normalise backslash variants for robustness
    assert r"{app}\_internal\templates" in content, (
        r"Expected '{app}\_internal\templates' in [InstallDelete], not found"
    )


def test_install_delete_type_is_filesandordirs():
    """The InstallDelete entry must use Type: filesandordirs."""
    content = _read_iss()
    # Find the [InstallDelete] block and check for the type
    install_delete_block = re.search(
        r"\[InstallDelete\](.*?)(?=\n\[|\Z)", content, re.DOTALL
    )
    assert install_delete_block is not None, "[InstallDelete] section not found"
    block_text = install_delete_block.group(1)
    assert "filesandordirs" in block_text, (
        "Expected 'Type: filesandordirs' inside [InstallDelete] block"
    )


def test_files_section_still_has_recursesubdirs():
    """The [Files] section must still carry the recursesubdirs flag (unchanged)."""
    content = _read_iss()
    files_block = re.search(r"\[Files\](.*?)(?=\n\[|\Z)", content, re.DOTALL)
    assert files_block is not None, "[Files] section not found"
    block_text = files_block.group(1)
    assert "recursesubdirs" in block_text, (
        "Expected 'recursesubdirs' flag in [Files] section — it must not have been removed"
    )


def test_install_delete_appears_before_files_section():
    """[InstallDelete] must appear before [Files] in the script for clarity."""
    content = _read_iss()
    idx_install_delete = content.find("[InstallDelete]")
    idx_files = content.find("[Files]")
    assert idx_install_delete != -1, "[InstallDelete] section not found"
    assert idx_files != -1, "[Files] section not found"
    assert idx_install_delete < idx_files, (
        "[InstallDelete] must appear before [Files] in setup.iss"
    )


def test_install_delete_name_is_exact():
    """The Name value in [InstallDelete] must be exactly {app}\\_internal\\templates."""
    content = _read_iss()
    # Match the specific directive line
    match = re.search(
        r'Type:\s*filesandordirs;\s*Name:\s*"(\{app\}[^"]+)"',
        content
    )
    assert match is not None, "Could not find a 'Type: filesandordirs; Name: ...' line in setup.iss"
    name_value = match.group(1)
    assert name_value == r"{app}\_internal\templates", (
        f"Expected Name to be '{{app}}\\_internal\\templates', got '{name_value}'"
    )
