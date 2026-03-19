"""
INS-003 — PyInstaller Config Edge-Case Tests (Tester Agent)

Supplements the 7 developer tests with additional coverage of:
- hiddenimports correctness
- console=False for GUI mode
- pathex includes src/
- upx=True in both EXE and COLLECT
- noarchive=False
- SPECPATH usage (portability)
- os.path.join usage (cross-platform)
- No hardcoded absolute paths (security / portability)
- PYZ defined (valid onedir structure)
- binaries=[] (no unexpected injected binaries)
- name='launcher' in both EXE and COLLECT
- datas source uses SPECPATH (not a bare relative path)
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "launcher.spec"


def _spec_text() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


# ── Hidden imports ─────────────────────────────────────────────────────────────

def test_spec_hiddenimports_customtkinter():
    """customtkinter must be declared in hiddenimports to prevent runtime import errors."""
    content = _spec_text()
    assert "hiddenimports" in content, "hiddenimports kwarg not found in spec"
    assert "'customtkinter'" in content or '"customtkinter"' in content, (
        "customtkinter not listed in hiddenimports — dynamic plugin imports will break at runtime"
    )


# ── Console / GUI mode ─────────────────────────────────────────────────────────

def test_spec_console_false():
    """console=False must be set in EXE — GUI app must not spawn a console window."""
    assert "console=False" in _spec_text(), (
        "launcher.spec does not set console=False in EXE(); "
        "the Launcher would show a console window on Windows"
    )


# ── pathex ─────────────────────────────────────────────────────────────────────

def test_spec_pathex_includes_src():
    """pathex must include src/ so PyInstaller resolves launcher.* package imports."""
    content = _spec_text()
    # Matches both os.path.join(SPECPATH, 'src') and literal 'src' in pathex list
    assert "'src'" in content or '"src"' in content, (
        "launcher.spec pathex does not reference src/ — "
        "launcher.* package imports will fail during PyInstaller analysis"
    )


# ── UPX compression ───────────────────────────────────────────────────────────

def test_spec_upx_true_in_exe_and_collect():
    """upx=True must appear at least twice: once in EXE, once in COLLECT."""
    occurrences = _spec_text().count("upx=True")
    assert occurrences >= 2, (
        f"Expected upx=True at least twice (in EXE and COLLECT), found {occurrences} time(s)"
    )


# ── noarchive ─────────────────────────────────────────────────────────────────

def test_spec_noarchive_false():
    """noarchive=False keeps the standard PYZ archive — noarchive=True would unpack
    every .pyc to disk and is reserved for debugging only."""
    assert "noarchive=False" in _spec_text(), (
        "launcher.spec does not set noarchive=False; "
        "omitting it relies on PyInstaller's default and may be unintentional"
    )


# ── SPECPATH portability ───────────────────────────────────────────────────────

def test_spec_uses_specpath():
    """SPECPATH must be used to anchor paths — makes the spec location-independent."""
    assert "SPECPATH" in _spec_text(), (
        "launcher.spec does not reference SPECPATH; "
        "hard-coded or plain relative paths break when pyinstaller is invoked from a different directory"
    )


# ── os.path.join cross-platform ───────────────────────────────────────────────

def test_spec_uses_os_path_join():
    """os.path.join must be used for path construction — ensures correct separators
    on Windows (\\), macOS (/), and Linux (/)."""
    assert "os.path.join" in _spec_text(), (
        "launcher.spec does not use os.path.join; "
        "hand-crafted forward-slash paths break on Windows builds"
    )


# ── No hardcoded absolute paths ───────────────────────────────────────────────

def test_spec_no_hardcoded_absolute_paths():
    """No absolute paths should appear in the spec — they make the build
    machine-specific and are prohibited by security-rules.md."""
    content = _spec_text()
    # Check for Windows drive letters (C:\, D:\, etc.) and Unix home dirs
    windows_abs = re.search(r'[A-Za-z]:\\\\', content)
    unix_home = re.search(r'/home/[^\'"\s]+', content)
    unix_users = re.search(r'/Users/[^\'"\s]+', content)
    assert not windows_abs, (
        f"Hardcoded Windows absolute path found: {windows_abs.group()}"
    )
    assert not unix_home, (
        f"Hardcoded Unix /home/ path found: {unix_home.group()}"
    )
    assert not unix_users, (
        f"Hardcoded macOS /Users/ path found: {unix_users.group()}"
    )


# ── PYZ defined ───────────────────────────────────────────────────────────────

def test_spec_pyz_defined():
    """PYZ() call must be present — it packages the Python bytecode archive."""
    assert "PYZ(" in _spec_text(), (
        "launcher.spec missing PYZ() call — bytecode archive will not be created"
    )


# ── binaries ──────────────────────────────────────────────────────────────────

def test_spec_binaries_empty():
    """binaries=[] should be set — no extra binary files injected by the spec.
    Unexpected entries here could be a supply-chain concern."""
    assert "binaries=[]" in _spec_text(), (
        "launcher.spec does not declare binaries=[]; "
        "unexpected binaries may be bundled without review"
    )


# ── name consistency ──────────────────────────────────────────────────────────

def test_spec_exe_and_collect_both_named_launcher():
    """Both EXE and COLLECT must use name='launcher' — mismatched names produce
    a broken output directory structure."""
    occurrences = _spec_text().count("name='launcher'")
    assert occurrences >= 2, (
        f"Expected name='launcher' in both EXE() and COLLECT(), found {occurrences} occurrence(s)"
    )


# ── datas source uses SPECPATH ────────────────────────────────────────────────

def test_spec_datas_templates_source_uses_specpath():
    """The source side of the templates datas tuple must use SPECPATH so the
    bundler can locate templates/ relative to the spec file on any machine."""
    content = _spec_text()
    # Expect: (os.path.join(SPECPATH, 'templates'), 'templates')
    assert "SPECPATH" in content and "'templates'" in content, (
        "templates datas entry does not reference SPECPATH — "
        "build will fail on machines where the working directory differs from the spec location"
    )
    # Narrow check: SPECPATH must appear in the datas assignment block
    datas_block_match = re.search(
        r'datas\s*=\s*\[.*?\]', content, re.DOTALL
    )
    if datas_block_match:
        assert "SPECPATH" in datas_block_match.group(), (
            "SPECPATH not present inside the datas=[...] block"
        )
