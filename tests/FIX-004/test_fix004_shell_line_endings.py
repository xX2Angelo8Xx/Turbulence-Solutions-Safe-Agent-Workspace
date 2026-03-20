"""FIX-004: Verify shell scripts use LF line endings (no CRLF)."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SHELL_SCRIPTS = [
    "src/installer/macos/build_dmg.sh",
    "src/installer/linux/build_appimage.sh",
]

def test_shell_scripts_use_lf():
    """Shell scripts must use LF line endings, not CRLF."""
    for rel_path in SHELL_SCRIPTS:
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"{rel_path} must exist"
        
        raw = full_path.read_bytes()
        assert b"\r\n" not in raw, (
            f"{rel_path} contains CRLF line endings — must use LF only"
        )
