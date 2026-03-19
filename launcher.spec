# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for the Turbulence Solutions Launcher.

Build mode: --onedir  (produces a launcher/ output directory)
Usage:      pyinstaller launcher.spec

The templates/ directory is bundled as data so the app can locate project
templates at runtime regardless of installation path.  templates/ is created
by INS-004; a pyinstaller build requires that directory to exist.

SPECPATH is a PyInstaller built-in that resolves to the directory containing
this spec file (i.e. the repository root).  Using os.path.join(SPECPATH, ...)
keeps all paths relative to the spec location, making the build reproducible
on any machine and on all three supported platforms (Windows, macOS, Linux).
"""

import os

# INS-018: Include the Python embeddable distribution if it has been populated.
# At build time the CI job downloads python-3.11.x-embed-amd64.zip and extracts
# it into src/installer/python-embed/ before running PyInstaller.  When the
# directory contains only the README placeholder (no .exe/.dll), this entry is
# omitted so that a plain developer build still works without the ~15 MB bundle.
_PYTHON_EMBED_DIR = os.path.join(SPECPATH, 'src', 'installer', 'python-embed')
_python_embed_bundle = []
if os.path.isfile(os.path.join(_PYTHON_EMBED_DIR, 'python.exe')):
    _python_embed_bundle = [(_PYTHON_EMBED_DIR, 'python-embed')]

a = Analysis(
    [os.path.join(SPECPATH, 'src', 'launcher', 'main.py')],
    pathex=[os.path.join(SPECPATH, 'src')],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, 'templates'), 'templates'),
        (os.path.join(SPECPATH, 'TS-Logo.png'), '.'),
        (os.path.join(SPECPATH, 'TS-Logo.ico'), '.'),
    ] + _python_embed_bundle,
    # customtkinter uses dynamic plugin imports that static analysis misses.
    hiddenimports=['customtkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    # exclude_binaries=True is the onedir switch; companion files go to COLLECT.
    exclude_binaries=True,
    name='launcher',
    debug=False,
    icon=os.path.join(SPECPATH, 'TS-Logo.ico'),
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # GUI app ΓÇö suppress console window on Windows.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='launcher',
)
