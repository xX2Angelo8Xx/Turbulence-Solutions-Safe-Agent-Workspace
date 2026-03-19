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
