# Dev Log — MNT-031: Local Windows Build Script (build_windows.py)

## Status
In Progress → Review

## Assigned To
Developer Agent

## Date
2026-04-07

## Prior Art / ADRs Reviewed
- **ADR-002** (Mandatory CI Test Gate Before Release Builds) — Local build script mirrors CI pipeline steps but is independent of the gate; no conflict.
- **ADR-010** (Windows-Only CI Until Stable Release) — This WP produces a Windows-only build script, consistent with ADR-010.
- No ADRs contradict or require supersession for this WP.

## Summary
Created `scripts/build_windows.py`, a local Windows build helper that mirrors the CI pipeline in `.github/workflows/release.yml` (lines 160–195). The script runs three sequential steps:
1. **PyInstaller** — builds `dist/launcher/launcher.exe` via `pyinstaller launcher.spec`
2. **Python embeddable download** — downloads Python 3.11.9 embed zip from python.org into `src/installer/python-embed/` if not already present
3. **Inno Setup** — locates `ISCC.exe` and runs it on `src/installer/windows/setup.iss`

CLI flags `--skip-pyinstaller`, `--skip-embed`, and `--dry-run` are supported.

## Files Changed
- `scripts/build_windows.py` — new file (main deliverable)
- `tests/MNT-031/test_mnt031_build_windows.py` — new test file
- `tests/MNT-031/__init__.py` — new empty init
- `scripts/README.md` — added `build_windows.py` entry
- `docs/workpackages/workpackages.jsonl` — status updated to In Progress / Review
- `docs/workpackages/MNT-031/dev-log.md` — this file

## Implementation Decisions
- Used `subprocess.run(..., check=True)` for all external commands to ensure non-zero exit codes propagate as errors.
- `shutil.which("ISCC")` is tried first (cross-user PATH), then two fallback hardcoded paths for standard Inno Setup 6 installs.
- Python embed download uses `urllib.request.urlretrieve` (stdlib only, no extra deps) with HTTPS; the URL is from the official Python FTP mirror.
- The embed step checks `len(list(embed_dir.iterdir())) > 0` to skip download if the directory already has files.
- `--dry-run` prints each step's command string without executing anything.

## Tests Written
- `test_find_iscc_via_which` — ISCC found via `shutil.which`
- `test_find_iscc_fallback_path` — ISCC found at default path when `which` returns None
- `test_find_iscc_not_found` — raises `SystemExit` with error message when no ISCC found
- `test_dry_run_no_subprocess` — `--dry-run` prints expected steps, never calls subprocess
- `test_skip_pyinstaller` — PyInstaller step skipped; only embed + ISCC run
- `test_skip_embed_when_present` — embed step skipped when directory already has files
- `test_skip_embed_flag` — embed step skipped via `--skip-embed` flag
- `test_embed_download_called` — `urlretrieve` called when embed dir is empty
- `test_iscc_not_found_error` — entire build fails with informative error when ISCC absent

## Known Limitations
- The embed download has no progress indicator; large downloads print nothing until complete. This mirrors the CI behavior and is acceptable for a local helper.

## Test Results
All tests pass — see `docs/test-results/test-results.jsonl` for TST record.
