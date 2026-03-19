# FIX-057 Test Report — Deploy ts-python shim in Linux AppImage build

## Verdict: PASS

## Tester
Tester Agent

## Date
2026-03-20

---

## Code Review

### build_appimage.sh

- **Shim bundling block exists:** `FIX-057` block present immediately after the python-embed copy and before Step 3 (`.desktop` file). Position verified via `test_shim_bundling_before_desktop_file`.
- **`mkdir -p` used:** `mkdir -p ${APPDIR}/usr/share/shims` — idempotent, correct.
- **`cp` uses full relative path:** `cp "src/installer/shims/ts-python" "${APPDIR}/usr/share/shims/ts-python"` — path is relative to repo root, correct.
- **`chmod +x` applied:** `chmod +x "${APPDIR}/usr/share/shims/ts-python"` — shim will be executable inside the AppImage.
- **No Windows-specific paths:** No `.cmd`/`.bat` extensions, no drive letters, no backslash path separators in installer paths.

### shim_config.py — `_find_bundled_shim()`

- Checks `usr/share/shims/ts-python` for the Linux AppImage layout (line 160–163).
- Uses `resolve()` to handle the `../..` traversal from `usr/bin/` to `usr/share/shims/`.
- Correctly guards all bundled paths under `hasattr(sys, "_MEIPASS")`.

### Security

No security issues. The shim is bundled from a known repo path (`src/installer/shims/ts-python`) and there is no dynamic path construction from user input.

---

## Test Runs

| ID | Suite | Tests | Result |
|----|-------|-------|--------|
| TST-1884 | Developer targeted (6 tests) | 6 passed / 0 failed | PASS |
| TST-1885 | Tester targeted (9 tests) | 9 passed / 0 failed | PASS |
| TST-1886 | Full regression suite | exit 0 (all tests pass) | PASS |

---

## Tests Added (Tester edge-cases)

Three new tests added to `tests/FIX-057/test_fix057.py`:

1. **`test_no_windows_shim_paths_in_build_script`** — Asserts no `.cmd`/`.bat` shim extension, no Windows drive letters (`C:\`), and no Windows env vars (`%APPDATA%`) appear in the Linux build script.
2. **`test_mkdir_uses_p_flag`** — Asserts the `mkdir` for `usr/share/shims` includes the `-p` flag (idempotent creation).
3. **`test_cp_uses_relative_path_from_repo_root`** — Asserts the `cp` command references `src/installer/shims/ts-python` as the relative source path from repo root.

---

## Edge-Case Analysis

| Concern | Finding |
|---------|---------|
| Windows paths in Linux script | None found — test confirms |
| `mkdir` without `-p` (fails if dir exists) | Uses `-p` — safe |
| Absolute path in `cp` source | Uses relative path — portable |
| Shim bundled after `.desktop` section | Not the case — bundled before Step 3 |
| `chmod +x` missing | Applied — shim is executable |
| `_find_bundled_shim()` wrong path | Correctly checks `usr/share/shims/ts-python` with `resolve()` |
| Race condition on `mkdir`/`cp` | `set -euo pipefail` + `-p` flag mitigate |
| No regression from change | Full suite exit 0, consistent with v3.0.2 baseline |
