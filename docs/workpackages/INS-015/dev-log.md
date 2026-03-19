# Dev Log — INS-015: CI macOS Build Jobs

## Status
In Progress → Review

## Branch
`ins/INS-015-ci-macos-build`

## Objective
Add `macos-intel-build` (macos-13) and `macos-arm-build` (macos-14) jobs to
`.github/workflows/release.yml`. Each job checks out code, sets up Python 3.11,
installs dependencies, runs PyInstaller, then calls `build_dmg.sh` with the
appropriate architecture argument, and uploads the resulting DMG as an artifact.

---

## Research

### `src/installer/macos/build_dmg.sh`
- Accepts `x86_64` or `arm64` as `$1`; falls back to `uname -m` if omitted.
- Runs PyInstaller via `python -m PyInstaller --target-arch <arch>` (skip if
  `dist/launcher/` already exists).
- Creates `.app` bundle at `dist/AgentEnvironmentLauncher.app`.
- Creates DMG at `dist/AgentEnvironmentLauncher-0.1.0-<arch>.dmg` using
  `hdiutil create` (UDZO format).
- No additional system dependencies — `hdiutil` is pre-installed on macOS.

### Artifact paths
| Arch   | DMG filename                                 |
|--------|----------------------------------------------|
| x86_64 | `dist/AgentEnvironmentLauncher-0.1.0-x86_64.dmg` |
| arm64  | `dist/AgentEnvironmentLauncher-0.1.0-arm64.dmg`  |

A glob (`dist/*.dmg`) is used in the upload step for resilience across version bumps.

---

## Implementation

Modified `.github/workflows/release.yml`:

### `macos-intel-build` (was stub — just checkout)
Replaced stub with 6 steps:
1. `actions/checkout@v4`
2. `actions/setup-python@v5` — python-version: '3.11'
3. Install dependencies — `pip install -e ".[dev]"`
4. Build with PyInstaller — `pyinstaller launcher.spec`
5. Build DMG — `chmod +x …/build_dmg.sh && build_dmg.sh x86_64`
6. Upload macOS Intel DMG — artifact name `macos-intel-dmg`, path `dist/*.dmg`

### `macos-arm-build` (was stub — just checkout)
Identical 6-step structure with `arm64` arch and artifact name `macos-arm-dmg`.

---

## Files Changed
- `.github/workflows/release.yml` — fleshed out both macOS job stubs
- `docs/workpackages/workpackages.csv` — status set to In Progress / Review
- `docs/workpackages/INS-015/dev-log.md` — this file
- `tests/INS-015/__init__.py` — test package
- `tests/INS-015/test_ins015_macos_build_jobs.py` — 27 tests

---

## Tests Written
File: `tests/INS-015/test_ins015_macos_build_jobs.py`

### Coverage
- Both jobs exist in workflow
- Correct `runs-on` values (`macos-13`, `macos-14`)
- Both jobs have exactly 6 steps
- `actions/checkout@v4` present in each
- `actions/setup-python@v5` present in each
- `python-version: '3.11'` in each
- `Install dependencies` step with correct `pip install -e ".[dev]"` command
- `Build with PyInstaller` step references `launcher.spec`
- `Build DMG` step — `chmod +x` and correct script path
- `Build DMG` step — correct architecture argument (`x86_64` / `arm64`)
- `actions/upload-artifact@v4` present in each
- Artifact names: `macos-intel-dmg` / `macos-arm-dmg`
- Artifact paths contain `.dmg`
- Other jobs (windows-build, linux-build, release) unaffected

---

## Test Results
All 27 INS-015 tests pass. Full suite run before handoff — see test-results.csv.
