# Python Embeddable Distribution — Bundle Placeholder

This directory holds the Python embeddable distribution that is bundled with the
installer. The actual Python binaries are **not committed to git** (they are
~15 MB binary blobs). Instead, they must be downloaded at build time before
running PyInstaller or the platform installer scripts.

---

## Windows (python-3.11.x-embed-amd64.zip)

**Download URL pattern:**
```
https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
```

**Build-time setup (run from repository root):**
```powershell
# Download and extract into this directory
$version = "3.11.9"
$url = "https://www.python.org/ftp/python/$version/python-$version-embed-amd64.zip"
Invoke-WebRequest -Uri $url -OutFile "python-embed.zip"
Expand-Archive -Path "python-embed.zip" -DestinationPath "src/installer/python-embed/" -Force
Remove-Item "python-embed.zip"
```

**Expected layout after extraction:**
```
src/installer/python-embed/
    python.exe
    python3.dll
    python311.dll
    python311.zip
    pythonw.exe
    vcruntime140.dll
    ... (other DLLs and zip archives)
```

**CI integration note:**
The `windows-build` job in `.github/workflows/release.yml` must download and
extract this package before running `pyinstaller launcher.spec`. See the CI note
comment in [release.yml](.github/workflows/release.yml).

---

## macOS

macOS ships with Python 3 as part of Xcode Command Line Tools, and the
PyInstaller `.app` bundle already embeds a Python.framework. No separate
embeddable package is needed for the macOS build.

For scenarios where the system Python is not available, download the macOS
installer from:
```
https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg
```

The `build_dmg.sh` script copies the contents of this directory into the `.app`
bundle Resources if a non-empty `python-embed/` directory is present.

---

## Linux

Linux builds use the system Python (installed via `apt-get`) during the CI
pipeline. A portable Python distribution is not required for the AppImage build
because PyInstaller embeds its own Python.

For offline/portable scenarios, a self-contained Python build from
[python-build-standalone](https://github.com/indygreg/python-build-standalone)
can be placed here.

The `build_appimage.sh` script copies the contents of this directory into the
AppDir if a non-empty `python-embed/` directory is present.

---

## .gitignore

Binary Python distribution files are excluded from git via the repository
`.gitignore` (pattern: `src/installer/python-embed/*.zip`,
`src/installer/python-embed/python*.exe`,
`src/installer/python-embed/python*.dll`).
Only this `README.md` is tracked.

---

## Security note

Always verify the SHA256 checksum of the downloaded Python distribution against
the official hashes published at https://www.python.org/downloads/release/python-3119/
before bundling.
