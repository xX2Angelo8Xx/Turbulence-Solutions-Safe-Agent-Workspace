r"""
INS-021 — Update Inno Setup for shim installation and PATH

Validates that setup.iss contains all INS-021 changes:
  - ts-python.cmd [Files] entry targeting {localappdata}\TurbulenceSolutions\bin
  - [Registry] section extending HKCU Path via NeedsAddPath
  - NeedsAddPath Pascal function in [Code]
  - CurStepChanged writing python-path.txt on ssPostInstall (overwrite mode)
  - CurUninstallStepChanged removing the PATH entry on usPostUninstall
  - [UninstallDelete] entry for {localappdata}\TurbulenceSolutions
  - INS-018 PythonEmbedExists function preserved
"""

import re
from pathlib import Path

import pytest

ISS_PATH = (
    Path(__file__).parent.parent.parent
    / "src" / "installer" / "windows" / "setup.iss"
)


@pytest.fixture(scope="module")
def iss_content() -> str:
    return ISS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Basic presence
# ---------------------------------------------------------------------------

def test_iss_file_exists():
    assert ISS_PATH.exists(), f"setup.iss not found at {ISS_PATH}"


# ---------------------------------------------------------------------------
# [Files] — shim entry
# ---------------------------------------------------------------------------

def test_shim_files_entry_source(iss_content: str):
    """ts-python.cmd is listed as a Source in the [Files] section."""
    assert "ts-python.cmd" in iss_content


def test_shim_files_entry_dest(iss_content: str):
    """DestDir for ts-python.cmd is {localappdata}\\TurbulenceSolutions\\bin."""
    assert r"{localappdata}\TurbulenceSolutions\bin" in iss_content


def test_shim_source_path_references_shims_dir(iss_content: str):
    """Source path for the shim points into installer\\shims\\."""
    assert r"installer\shims\ts-python.cmd" in iss_content


def test_shim_flags_ignoreversion(iss_content: str):
    """The shim [Files] entry uses ignoreversion so reinstall overwrites it."""
    # Find the line that references ts-python.cmd and verify the flag is present.
    for line in iss_content.splitlines():
        if "ts-python.cmd" in line and "DestDir" in line:
            assert "ignoreversion" in line, (
                "ts-python.cmd Files entry missing 'ignoreversion' flag"
            )
            break
    else:
        pytest.fail("No ts-python.cmd Files entry with DestDir found")


# ---------------------------------------------------------------------------
# [Registry] — PATH extension
# ---------------------------------------------------------------------------

def test_registry_section_exists(iss_content: str):
    """A [Registry] section is present."""
    assert "[Registry]" in iss_content


def test_registry_hkcu_environment_path(iss_content: str):
    """Registry entry targets HKCU\\Environment\\Path."""
    assert "HKCU" in iss_content
    assert "Environment" in iss_content
    # ValueName "Path"
    assert 'ValueName: "Path"' in iss_content


def test_registry_expandsz_value_type(iss_content: str):
    """PATH value uses expandsz type to support %LOCALAPPDATA% expansion."""
    assert "expandsz" in iss_content


def test_registry_olddata_preserved(iss_content: str):
    """{olddata} keeps existing PATH entries when appending the new directory."""
    assert "{olddata}" in iss_content


def test_registry_needs_add_path_check(iss_content: str):
    """Registry PATH entry is guarded by NeedsAddPath to prevent duplicates."""
    assert "NeedsAddPath" in iss_content


# ---------------------------------------------------------------------------
# [Code] — NeedsAddPath
# ---------------------------------------------------------------------------

def test_needs_add_path_function_defined(iss_content: str):
    """NeedsAddPath function is declared in the [Code] section."""
    assert "function NeedsAddPath" in iss_content


def test_needs_add_path_queries_registry(iss_content: str):
    """NeedsAddPath reads the existing PATH from the registry."""
    assert "RegQueryStringValue" in iss_content


def test_needs_add_path_case_insensitive(iss_content: str):
    """NeedsAddPath uses Lowercase() for case-insensitive comparison."""
    assert "Lowercase" in iss_content


# ---------------------------------------------------------------------------
# [Code] — CurStepChanged / python-path.txt
# ---------------------------------------------------------------------------

def test_cur_step_changed_defined(iss_content: str):
    """CurStepChanged procedure is declared in [Code]."""
    assert "procedure CurStepChanged" in iss_content


def test_cur_step_changed_ss_post_install(iss_content: str):
    """CurStepChanged acts on ssPostInstall."""
    assert "ssPostInstall" in iss_content


def test_python_path_txt_written(iss_content: str):
    """python-path.txt is written during CurStepChanged."""
    assert "python-path.txt" in iss_content


def test_save_string_to_file_used(iss_content: str):
    """SaveStringToFile is called to write python-path.txt."""
    assert "SaveStringToFile" in iss_content


def test_python_path_txt_overwrite_mode(iss_content: str):
    """SaveStringToFile is called with Append=False (overwrite on reinstall)."""
    assert re.search(
        r"SaveStringToFile\s*\([^,]+,[^,]+,\s*False\s*\)",
        iss_content,
    ), "SaveStringToFile must use Append=False for overwrite on reinstall"


def test_python_path_contains_app_python_embed(iss_content: str):
    """python-path.txt content references {app}\\python-embed\\python.exe."""
    assert r"python-embed\python.exe" in iss_content


# ---------------------------------------------------------------------------
# [Code] — CurUninstallStepChanged / PATH cleanup
# ---------------------------------------------------------------------------

def test_cur_uninstall_step_changed_defined(iss_content: str):
    """CurUninstallStepChanged procedure is declared in [Code]."""
    assert "procedure CurUninstallStepChanged" in iss_content


def test_cur_uninstall_step_us_post_uninstall(iss_content: str):
    """CurUninstallStepChanged acts on usPostUninstall."""
    assert "usPostUninstall" in iss_content


def test_reg_write_expand_string_value_called(iss_content: str):
    """PATH is written back via RegWriteExpandStringValue after removal."""
    assert "RegWriteExpandStringValue" in iss_content


# ---------------------------------------------------------------------------
# [UninstallDelete] — config directory removal
# ---------------------------------------------------------------------------

def test_uninstall_delete_turbulence_dir(iss_content: str):
    """{localappdata}\\TurbulenceSolutions is removed on uninstall."""
    assert r"{localappdata}\TurbulenceSolutions" in iss_content


def test_uninstall_delete_type_files_and_dirs(iss_content: str):
    """The TurbulenceSolutions UninstallDelete entry uses filesandordirs."""
    # Must match a line that has both Type: filesandordirs and the target dir,
    # but NOT a Registry ValueType line (which also contains "TurbulenceSolutions").
    for line in iss_content.splitlines():
        stripped = line.strip()
        if (
            r"{localappdata}\TurbulenceSolutions" in stripped
            and stripped.startswith("Type:")
        ):
            assert "filesandordirs" in stripped, (
                "UninstallDelete entry must use Type: filesandordirs"
            )
            break
    else:
        pytest.fail(
            "No UninstallDelete entry found for {localappdata}\\TurbulenceSolutions"
        )


# ---------------------------------------------------------------------------
# INS-018 regression — PythonEmbedExists must still be present
# ---------------------------------------------------------------------------

def test_python_embed_exists_function_preserved(iss_content: str):
    """INS-018 PythonEmbedExists function is still defined (no regression)."""
    assert "function PythonEmbedExists" in iss_content


def test_python_embed_files_entry_present(iss_content: str):
    """INS-018 python-embed [Files] entry is still present."""
    assert r"{app}\python-embed" in iss_content
