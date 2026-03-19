# ts-python Shim System

This directory contains the `ts-python` shim files for Windows, macOS, and Linux.

## Architecture

```
%LOCALAPPDATA%\TurbulenceSolutions\        (Windows)
~/.local/share/TurbulenceSolutions/        (macOS/Linux)
├── bin/
│   └── ts-python (.cmd on Windows)        ← shim executable
└── python-path.txt                         ← path to bundled python
```

## How It Works

1. The installer copies `ts-python.cmd` (Windows) or `ts-python` (macOS/Linux) to the `bin/` directory above.
2. The installer writes the absolute path to the bundled Python executable into `python-path.txt`.
3. The installer adds the `bin/` directory to the user's `PATH`.
4. From any terminal, `ts-python <args>` reads `python-path.txt` and delegates to the bundled Python.

## Why a Config File?

Using an indirection layer (`python-path.txt`) rather than hardcoding the Python path inside the shim means:

- The installer can be moved or updated without leaving broken shims.
- The "Relocate Python Runtime" GUI option only needs to rewrite `python-path.txt`.
- All created workspaces that reference `ts-python` continue working after relocation.

## Files

| File | Platform | Line Endings | Description |
|------|----------|--------------|-------------|
| `ts-python.cmd` | Windows | CRLF | Batch file shim for CMD and PowerShell |
| `ts-python` | macOS / Linux | LF | POSIX shell script shim |

## Error Handling

Both shims exit with code 1 and write a descriptive message to stderr if:
- `python-path.txt` does not exist (config not written yet — reinstall required)
- The Python executable path read from config does not exist (runtime was moved — use Relocate Python Runtime)

## PATH Integration

**Windows (Inno Setup):** A `[Registry]` entry sets `HKCU\Environment\PATH` to include the `bin/` directory.

**macOS/Linux:** Future WP — the installer appends an `export PATH` line to the user's shell profile (`~/.bashrc`, `~/.zshrc`).

## Related Workpackages

| WP | Description |
|----|-------------|
| INS-018 | Bundle Python Embeddable Distribution |
| INS-019 | This WP — shim files and `shim_config.py` |
| INS-020 | Update `require-approval.json` to use `ts-python` |
| INS-021 | Inno Setup integration: copy shim, write config, set PATH |
| GUI-018 | Relocate Python Runtime GUI option |
| SAF-034 | Verify `ts-python` before workspace creation |
