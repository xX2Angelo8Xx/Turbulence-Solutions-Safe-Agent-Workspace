"""
Tests for FIX-057: Deploy ts-python shim in Linux AppImage build.

Verifies that build_appimage.sh correctly bundles the ts-python shim
into the AppImage at the path expected by _find_bundled_shim().
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
SHIM_CONFIG = REPO_ROOT / "src" / "launcher" / "core" / "shim_config.py"


def _script_text() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


def _shim_config_text() -> str:
    return SHIM_CONFIG.read_text(encoding="utf-8")


def test_build_script_contains_shim_path():
    """build_appimage.sh must reference usr/share/shims/ts-python."""
    assert "usr/share/shims/ts-python" in _script_text(), (
        "build_appimage.sh does not reference usr/share/shims/ts-python"
    )


def test_build_script_chmod_shim():
    """build_appimage.sh must chmod +x the bundled shim."""
    text = _script_text()
    # Must have a chmod +x line that targets the shim
    pattern = r'chmod\s+\+x.*usr/share/shims'
    assert re.search(pattern, text), (
        "build_appimage.sh does not chmod +x the shim at usr/share/shims"
    )


def test_build_script_mkdir_shims_dir():
    """build_appimage.sh must create the ${APPDIR}/usr/share/shims directory."""
    text = _script_text()
    pattern = r'mkdir\s+-p.*usr/share/shims'
    assert re.search(pattern, text), (
        "build_appimage.sh does not mkdir -p the usr/share/shims directory"
    )


def test_build_script_copies_from_shims_source():
    """build_appimage.sh must copy from src/installer/shims/ts-python."""
    assert "src/installer/shims/ts-python" in _script_text(), (
        "build_appimage.sh does not reference src/installer/shims/ts-python as the copy source"
    )


def test_shim_config_checks_linux_appimage_path():
    """_find_bundled_shim() in shim_config.py must check the Linux AppImage path."""
    text = _shim_config_text()
    # The function should reference the Linux AppImage path pattern
    assert "usr/share/shims" in text, (
        "shim_config.py _find_bundled_shim() does not check usr/share/shims (Linux AppImage path)"
    )


def test_shim_bundling_before_desktop_file():
    """The shim bundling block must appear before the Step 3 .desktop file section."""
    text = _script_text()
    shim_idx = text.find("usr/share/shims/ts-python")
    desktop_idx = text.find("Step 3: Write .desktop file")
    assert shim_idx != -1, "usr/share/shims/ts-python not found in build_appimage.sh"
    assert desktop_idx != -1, "Step 3: Write .desktop file section not found in build_appimage.sh"
    assert shim_idx < desktop_idx, (
        "Shim bundling must appear BEFORE the Step 3 .desktop file section"
    )


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------


def test_no_windows_shim_paths_in_build_script():
    """build_appimage.sh must not reference Windows-specific shim paths.

    Windows path patterns (.cmd/.bat extension, drive letters, backslash
    file-path separators) must never appear in the Linux build script.
    """
    text = _script_text()
    # .cmd or .bat shim extensions — exclusively Windows
    assert "ts-python.cmd" not in text, (
        "build_appimage.sh references ts-python.cmd — a Windows-only shim extension"
    )
    assert "ts-python.bat" not in text, (
        "build_appimage.sh references ts-python.bat — a Windows-only shim extension"
    )
    # Windows drive letter path pattern (e.g. C:\ or C:/) — use negative lookbehind
    # to avoid matching URL schemes like https:/ where a letter precedes the colon
    assert not re.search(r'(?<![a-zA-Z0-9])[A-Za-z]:[/\\]', text), (
        "build_appimage.sh contains a Windows drive letter path (e.g. C:\\)"
    )
    # %APPDATA% or %USERPROFILE% Windows environment variables
    assert "%APPDATA%" not in text and "%USERPROFILE%" not in text, (
        "build_appimage.sh references Windows environment variables"
    )
    # Backslash as path separator in installer paths (not shell escapes)
    # Pattern: src\installer or shims\ (backslash in a file path context)
    assert not re.search(r'src\\installer|shims\\', text), (
        "build_appimage.sh uses backslash path separators in installer paths (Windows-style)"
    )


def test_mkdir_uses_p_flag():
    """The mkdir for shims directory must use the -p flag (idempotent, no error if exists)."""
    text = _script_text()
    # Must match: mkdir -p ... usr/share/shims
    pattern = r'mkdir\s+-p[^\n]*usr/share/shims'
    assert re.search(pattern, text), (
        "build_appimage.sh mkdir for usr/share/shims does not use the -p flag"
    )


def test_cp_uses_relative_path_from_repo_root():
    """cp command must reference a relative path rooted at src/installer/shims/ts-python."""
    text = _script_text()
    # The cp source must be exactly: src/installer/shims/ts-python (not an absolute path)
    pattern = r'cp\s+"?src/installer/shims/ts-python"?'
    assert re.search(pattern, text), (
        "build_appimage.sh cp does not use src/installer/shims/ts-python as the relative source path"
    )
