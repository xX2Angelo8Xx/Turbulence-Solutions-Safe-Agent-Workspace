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

def test_python_embed_exists_function_removed(iss_content: str):
    """FIX-055: PythonEmbedExists runtime function must be absent from setup.iss.

    INS-021 originally required this function to be present (INS-018 regression
    guard).  FIX-055 deliberately removes it and replaces the runtime check with
    the compile-time skipifsourcedoesntexist flag on the python-embed [Files] entry.
    This test verifies the transition is complete and no stale reference remains.
    """
    assert "function PythonEmbedExists" not in iss_content, (
        "PythonEmbedExists function must not be in setup.iss — "
        "FIX-055 replaced it with skipifsourcedoesntexist on the [Files] entry"
    )
    assert "skipifsourcedoesntexist" in iss_content, (
        "skipifsourcedoesntexist flag must be present — "
        "it is the FIX-055 replacement for the removed PythonEmbedExists function"
    )


def test_python_embed_files_entry_present(iss_content: str):
    """INS-018 python-embed [Files] entry is still present."""
    assert r"{app}\python-embed" in iss_content


# ---------------------------------------------------------------------------
# Tester edge-case tests — INS-021
# ---------------------------------------------------------------------------

def test_needs_add_path_semicolon_wrapping(iss_content: str):
    """NeedsAddPath wraps both the target and the existing PATH with semicolons.

    Without this wrapping, 'C:\\Foo\\bin' would falsely match 'C:\\Foo\\bin2'.
    The implementation must produce ';'+Lowercase(PathToAdd)+';' and
    ';'+Lowercase(OldPath)+';' to guarantee an exact-segment match.
    """
    # Both the Pos argument (needle) and the haystack must include the wrapping.
    assert "';' + Lowercase(PathToAdd) + ';'" in iss_content or (
        # Accept alternative style: ';' + Lowercase(...) + ';'
        re.search(
            r"';'\s*\+\s*Lowercase\s*\(\s*PathToAdd\s*\)\s*\+\s*';'",
            iss_content,
        )
    ), "NeedsAddPath must wrap PathToAdd with semicolons for exact-segment match"
    assert "';' + Lowercase(OldPath) + ';'" in iss_content or (
        re.search(
            r"';'\s*\+\s*Lowercase\s*\(\s*OldPath\s*\)\s*\+\s*';'",
            iss_content,
        )
    ), "NeedsAddPath must wrap OldPath with semicolons to prevent partial matches"


def test_needs_add_path_early_exit_when_registry_missing(iss_content: str):
    """NeedsAddPath returns True (add path) when registry key does not exist.

    If RegQueryStringValue fails (no PATH key yet), NeedsAddPath must not
    crash and must return True so the entry gets added.
    """
    # The function must contain a branch that sets Result := True and calls Exit
    # immediately after a failed RegQueryStringValue call.
    assert re.search(
        r"Result\s*:=\s*True\s*;[\s\S]*?Exit\s*;",
        iss_content,
    ), "NeedsAddPath must set Result := True and call Exit when registry is absent"


def test_needs_add_path_uses_pos_function(iss_content: str):
    """NeedsAddPath uses Pos() to locate the path in the existing PATH string."""
    # Pos() is the Pascal substring-search function used for the membership test.
    assert re.search(r"\bPos\s*\(", iss_content), (
        "NeedsAddPath must use Pos() for case-insensitive substring search"
    )


def test_registry_root_is_hkcu_not_hklm(iss_content: str):
    """PATH is modified in HKCU (per-user), never HKLM (system-wide).

    Writing to HKLM would require elevation and affect all users, which is
    both a security concern and a privilege violation for a user-level shim.
    """
    # Verify HKCU is used and HKLM is absent from the Registry section.
    lines = iss_content.splitlines()
    in_registry = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[Registry]":
            in_registry = True
            continue
        if in_registry and stripped.startswith("[") and stripped != "[Registry]":
            break
        if in_registry and "Root:" in line:
            assert "HKCU" in line, f"Registry entry must use HKCU, got: {line}"
            assert "HKLM" not in line, (
                f"Registry entry must NOT use HKLM (machine-wide): {line}"
            )


def test_python_path_txt_written_to_localappdata(iss_content: str):
    """python-path.txt is written to {localappdata}\\TurbulenceSolutions, not {app}.

    The config file must be user-local so the shim can read it without
    elevation and from any working directory.
    """
    # CurStepChanged must expand {localappdata} for ConfigDir, not {app}.
    assert re.search(
        r"ExpandConstant\s*\(\s*['\"]?\{localappdata\}",
        iss_content,
    ), "ConfigDir must use {localappdata} via ExpandConstant, not {app}"


def test_config_dir_exists_check_before_create_dir(iss_content: str):
    """DirExists is checked before CreateDir to avoid a duplicate-directory error.

    Calling CreateDir on an existing directory is a no-op in Pascal, but the
    explicit guard makes the intent clear and avoids relying on implementation
    details of the Inno Setup runtime.
    """
    assert "DirExists" in iss_content, (
        "CurStepChanged must check DirExists before calling CreateDir"
    )
    assert "CreateDir" in iss_content, (
        "CurStepChanged must call CreateDir to ensure the config directory exists"
    )
    # DirExists must appear before CreateDir in the source.
    dir_exists_pos = iss_content.index("DirExists")
    create_dir_pos = iss_content.index("CreateDir")
    assert dir_exists_pos < create_dir_pos, (
        "DirExists check must appear before CreateDir call"
    )


def test_uninstall_strips_leading_and_trailing_semicolons(iss_content: str):
    """CurUninstallStepChanged trims leading and trailing semicolons from NewPath.

    After removing ';BinDir' from the wrapped path, the resulting string may
    still start or end with ';'. Both while-loops must be present to produce a
    clean PATH value.
    """
    # The implementation uses while loops checking NewPath[1] and
    # NewPath[Length(NewPath)] to strip residual semicolons.
    assert re.search(
        r"while\s*\(.*NewPath\s*\[\s*1\s*\]\s*=\s*';'",
        iss_content,
    ), "Uninstall cleanup must strip leading semicolons via while loop"
    assert re.search(
        r"while\s*\(.*NewPath\s*\[\s*Length\s*\(\s*NewPath\s*\)\s*\]\s*=\s*';'",
        iss_content,
    ), "Uninstall cleanup must strip trailing semicolons via while loop"


def test_uninstall_exits_early_if_path_not_found(iss_content: str):
    """CurUninstallStepChanged exits early when the bin dir is not in PATH.

    If StartPos = 0 the entry was never added (or already removed), so the
    procedure must return without modifying the registry.
    """
    assert re.search(
        r"StartPos\s*=\s*0\s*\)",
        iss_content,
    ) or "StartPos = 0" in iss_content, (
        "Uninstall PATH cleanup must exit early when StartPos = 0"
    )
    assert re.search(
        r"if\s+StartPos\s*=\s*0\s+then",
        iss_content,
    ), "Must guard with 'if StartPos = 0 then Exit'"


def test_registry_check_uses_expand_constant(iss_content: str):
    """The Registry [Check] guard calls ExpandConstant to resolve {localappdata}.

    Without ExpandConstant the literal string '{localappdata}\\...' would be
    passed to NeedsAddPath instead of the resolved path, causing NeedsAddPath
    to never match the actual PATH value.
    """
    # The Registry section's Check line must contain ExpandConstant.
    for line in iss_content.splitlines():
        if "NeedsAddPath" in line and "Check:" in line:
            assert "ExpandConstant" in line, (
                "Registry Check must wrap path in ExpandConstant: " + line
            )
            break
    else:
        pytest.fail("No [Registry] line with 'Check: NeedsAddPath' found")
