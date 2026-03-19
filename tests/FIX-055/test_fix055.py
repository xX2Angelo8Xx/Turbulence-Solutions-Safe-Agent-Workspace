"""
FIX-055: Tests for Fix Inno Setup PythonEmbedExists runtime check.

Verifies that setup.iss correctly uses skipifsourcedoesntexist instead
of the runtime Check: PythonEmbedExists, and includes architecture directives.
"""
import re
import pathlib

SETUP_ISS = (
    pathlib.Path(__file__).parent.parent.parent
    / "src" / "installer" / "windows" / "setup.iss"
)


def _read_iss():
    return SETUP_ISS.read_text(encoding="utf-8")


def test_skipifsourcedoesntexist_in_python_embed_flags():
    """The python-embed [Files] entry must have skipifsourcedoesntexist in Flags."""
    content = _read_iss()
    # Find the python-embed source line
    match = re.search(
        r'Source:\s*"\.\.[\\\/]python-embed[\\\/]\*"[^\n]*',
        content
    )
    assert match, "python-embed source line not found in setup.iss"
    line = match.group(0)
    assert "skipifsourcedoesntexist" in line.lower(), (
        f"skipifsourcedoesntexist not found in python-embed Files entry: {line!r}"
    )


def test_no_check_parameter_on_python_embed():
    """The python-embed [Files] entry must NOT have a Check: parameter."""
    content = _read_iss()
    match = re.search(
        r'Source:\s*"\.\.[\\\/]python-embed[\\\/]\*"[^\n]*',
        content
    )
    assert match, "python-embed source line not found in setup.iss"
    line = match.group(0)
    assert "Check:" not in line, (
        f"Check: parameter still present on python-embed Files entry: {line!r}"
    )


def test_python_embed_exists_function_removed():
    """The PythonEmbedExists() Pascal function must NOT exist in [Code] section."""
    content = _read_iss()
    assert "PythonEmbedExists" not in content, (
        "PythonEmbedExists identifier still found in setup.iss — function was not removed"
    )


def test_architectures_install_in_64bit_mode():
    """[Setup] section must contain ArchitecturesInstallIn64BitMode=x64compatible."""
    content = _read_iss()
    # Must appear before [Languages] (i.e., still in [Setup])
    setup_section = content.split("[Languages]")[0]
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in setup_section, (
        "ArchitecturesInstallIn64BitMode=x64compatible not found in [Setup] section"
    )


def test_architectures_allowed():
    """[Setup] section must contain ArchitecturesAllowed=x64compatible."""
    content = _read_iss()
    setup_section = content.split("[Languages]")[0]
    assert "ArchitecturesAllowed=x64compatible" in setup_section, (
        "ArchitecturesAllowed=x64compatible not found in [Setup] section"
    )


def test_cur_step_changed_still_exists():
    """CurStepChanged procedure must still exist (writes python-path.txt)."""
    content = _read_iss()
    assert "procedure CurStepChanged" in content, (
        "CurStepChanged procedure is missing from setup.iss [Code] section"
    )
    assert "python-path.txt" in content, (
        "python-path.txt reference missing from CurStepChanged body"
    )


def test_python_embed_source_path_unchanged():
    r"""Source path for python-embed must still be ..\python-embed\*"""
    content = _read_iss()
    assert r'"..\python-embed\*"' in content, (
        r'Source path "..\python-embed\*" not found in setup.iss'
    )


def test_python_embed_dest_dir_unchanged():
    r"""DestDir for python-embed must still be {app}\python-embed."""
    content = _read_iss()
    match = re.search(
        r'Source:\s*"\.\.[\\\/]python-embed[\\\/]\*"[^\n]*',
        content
    )
    assert match, "python-embed source line not found in setup.iss"
    line = match.group(0)
    assert "{app}\\python-embed" in line or '"{app}\\python-embed"' in line, (
        f'DestDir "{{app}}\\python-embed" not found in python-embed Files entry: {line!r}'
    )


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------

def test_autopf_not_alongside_x86_in_default_dir_name():
    """DefaultDirName must use {autopf} and [Setup] must not hardcode x86 paths."""
    content = _read_iss()
    # Extract [Setup] section (up to the first other section)
    setup_section = re.split(r'^\[(?!Setup)', content, maxsplit=1, flags=re.MULTILINE)[0]
    assert "DefaultDirName={autopf}" in setup_section, (
        "DefaultDirName does not use {autopf} macro in [Setup] section"
    )
    assert "Program Files (x86)" not in setup_section, (
        "[Setup] section contains a hardcoded 'Program Files (x86)' path — "
        "ArchitecturesInstallIn64BitMode should resolve {autopf} to Program Files on x64"
    )


def test_uninstall_delete_still_references_python_embed():
    """[UninstallDelete] section must still contain an entry for python-embed."""
    content = _read_iss()
    # Find [UninstallDelete] section
    uninstall_match = re.search(
        r'\[UninstallDelete\](.*?)(?=\n\[|\Z)',
        content,
        re.DOTALL
    )
    assert uninstall_match, "[UninstallDelete] section not found in setup.iss"
    uninstall_body = uninstall_match.group(1)
    assert "python-embed" in uninstall_body, (
        "python-embed entry missing from [UninstallDelete] section — "
        "bundled Python would not be cleaned up on uninstall"
    )


def test_python_embed_dest_dir_not_bare_path():
    r"""DestDir for python-embed must be the {app}-relative path, not a bare/absolute path."""
    content = _read_iss()
    match = re.search(
        r'Source:\s*"\.\.[\\\/]python-embed[\\\/]\*"[^\n]*',
        content
    )
    assert match, "python-embed source line not found in setup.iss"
    line = match.group(0)
    # Must have {app} prefix — bare 'python-embed' without {app} would be relative
    # to an undefined working directory and fail at install time.
    destdir_match = re.search(r'DestDir:\s*"([^"]*)"', line)
    assert destdir_match, f"DestDir not found in python-embed Files line: {line!r}"
    dest = destdir_match.group(1)
    assert dest.startswith("{app}"), (
        f"DestDir '{dest}' does not start with {{app}} — bare path detected"
    )
    assert "python-embed" in dest, (
        f"DestDir '{dest}' does not include 'python-embed' subdirectory"
    )


def test_no_python_embed_exists_reference_anywhere():
    """PythonEmbedExists must not appear anywhere in setup.iss — not even in comments."""
    content = _read_iss()
    # Case-insensitive scan to catch any casing variant left in comments
    assert "pythonembed" not in content.lower().replace("python-embed", ""), (
        "A reference to PythonEmbedExists (or similar identifier) still exists in setup.iss. "
        "Check comments and dead code."
    )
    # Explicit check for exact identifier
    assert "PythonEmbedExists" not in content, (
        "PythonEmbedExists identifier still present in setup.iss"
    )


def test_shim_files_entry_unmodified():
    """The ts-python.cmd [Files] entry must be intact and unmodified by FIX-055."""
    content = _read_iss()
    # The shim entry must still be present verbatim
    expected_source = r'"..\..\installer\shims\ts-python.cmd"'
    assert expected_source in content, (
        f"ts-python.cmd source path {expected_source!r} not found — shim entry was modified"
    )
    # Verify the shim entry still has the correct DestDir
    match = re.search(
        r'Source:\s*"[^"]*ts-python\.cmd"[^\n]*',
        content
    )
    assert match, "ts-python.cmd Files entry not found in setup.iss"
    line = match.group(0)
    assert "{localappdata}" in line, (
        f"ts-python.cmd DestDir no longer uses {{localappdata}}: {line!r}"
    )
    assert "TurbulenceSolutions" in line, (
        f"ts-python.cmd DestDir no longer uses TurbulenceSolutions path: {line!r}"
    )
    assert "ignoreversion" in line.lower(), (
        f"ts-python.cmd Flags no longer contains ignoreversion: {line!r}"
    )
    # Must NOT have skipifsourcedoesntexist (shim is always present in the installer source)
    assert "skipifsourcedoesntexist" not in line.lower(), (
        f"ts-python.cmd Flags accidentally gained skipifsourcedoesntexist: {line!r}"
    )
