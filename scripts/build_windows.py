#!/usr/bin/env python3
"""Local Windows build script: mirrors the CI pipeline in release.yml.

Steps performed (in order):
  1. PyInstaller build    — produces dist/launcher/launcher.exe
  2. Python embed fetch  — downloads python-3.11.9-embed-amd64.zip into
                           src/installer/python-embed/ (skipped if files are
                           already present)
  3. Inno Setup compile  — runs ISCC.exe on src/installer/windows/setup.iss
                           producing AgentEnvironmentLauncher-Setup.exe

Usage:
    .venv\\Scripts\\python scripts/build_windows.py
    .venv\\Scripts\\python scripts/build_windows.py --skip-pyinstaller
    .venv\\Scripts\\python scripts/build_windows.py --skip-embed
    .venv\\Scripts\\python scripts/build_windows.py --dry-run
    .venv\\Scripts\\python scripts/build_windows.py --skip-pyinstaller --skip-embed
"""

# MNT-031

import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PYTHON_EMBED_VERSION = "3.11.9"
PYTHON_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_EMBED_VERSION}"
    f"/python-{PYTHON_EMBED_VERSION}-embed-amd64.zip"
)
PYTHON_EMBED_DIR = REPO_ROOT / "src" / "installer" / "python-embed"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
OUTPUT_EXE = (
    REPO_ROOT
    / "src"
    / "installer"
    / "windows"
    / "Output"
    / "AgentEnvironmentLauncher-Setup.exe"
)

_ISCC_FALLBACK_PATHS = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
]


def find_iscc() -> Path:
    """Return the path to ISCC.exe or abort with an informative error."""
    found = shutil.which("ISCC")
    if found:
        return Path(found)

    for candidate in _ISCC_FALLBACK_PATHS:
        if candidate.exists():
            return candidate

    print(
        "ERROR: ISCC.exe not found.\n"
        "Install Inno Setup 6 from https://jrsoftware.org/isdl.php\n"
        "or add its directory to PATH, then re-run this script.",
        file=sys.stderr,
    )
    sys.exit(1)


def step_pyinstaller(dry_run: bool) -> None:
    """Run PyInstaller using launcher.spec."""
    cmd = ["pyinstaller", "launcher.spec"]
    print(f"[build] PyInstaller: {' '.join(cmd)}")
    if dry_run:
        return
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def step_python_embed(dry_run: bool) -> None:
    """Download the Python embeddable distribution if not already present."""
    # Skip if the directory already contains files.
    if PYTHON_EMBED_DIR.exists() and any(PYTHON_EMBED_DIR.iterdir()):
        print(f"[build] Python embed: already present in {PYTHON_EMBED_DIR} — skipping")
        return

    zip_path = REPO_ROOT / "python-embed.zip"
    print(f"[build] Python embed: downloading {PYTHON_EMBED_URL}")
    if dry_run:
        print(f"[build] Python embed: would extract to {PYTHON_EMBED_DIR}")
        return

    PYTHON_EMBED_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(PYTHON_EMBED_DIR)
    finally:
        zip_path.unlink(missing_ok=True)

    print(f"[build] Python embed: extracted to {PYTHON_EMBED_DIR}")


def step_inno_setup(dry_run: bool) -> None:
    """Locate ISCC.exe and compile setup.iss."""
    iscc = find_iscc()
    cmd = [str(iscc), str(SETUP_ISS)]
    print(f"[build] Inno Setup: {' '.join(cmd)}")
    if dry_run:
        return
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Windows installer locally (mirrors CI pipeline)."
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip the PyInstaller step (use when only installer files changed).",
    )
    parser.add_argument(
        "--skip-embed",
        action="store_true",
        help="Skip the Python embeddable download step.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without executing anything.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[build] DRY RUN — no commands will be executed")

    # Step 1: PyInstaller
    if args.skip_pyinstaller:
        print("[build] PyInstaller: skipped (--skip-pyinstaller)")
    else:
        step_pyinstaller(dry_run=args.dry_run)

    # Step 2: Python embeddable distribution
    if args.skip_embed:
        print("[build] Python embed: skipped (--skip-embed)")
    else:
        step_python_embed(dry_run=args.dry_run)

    # Step 3: Inno Setup
    step_inno_setup(dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n[build] SUCCESS: {OUTPUT_EXE}")


if __name__ == "__main__":
    main()
