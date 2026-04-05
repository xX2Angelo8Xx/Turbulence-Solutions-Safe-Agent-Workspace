# Dev Log — MNT-025: Cross-WP Test Impact Pre-Commit Hook

**Developer:** Developer Agent  
**Date:** 2026-04-05  
**Branch:** MNT-025/cross-wp-test-impact-hook  
**Status:** Review

---

## ADR Acknowledgement

**ADR-008** (`docs/decisions/ADR-008-tests-track-code.md`) is directly relevant. This WP implements the automated mechanism implied by ADR-008's "New Process Rule": surfacing which test files in other workpackages reference a changed module, before the commit is finalized. MNT-025 does not supersede ADR-008 — it operationalises it.

---

## Summary

Implemented a cross-WP test impact advisor that runs as part of the pre-commit hook. The tool scans all test files for references to staged source modules and prints advisory warnings — but never blocks a commit (always exits 0).

---

## Files Changed

| File | Action |
|------|--------|
| `scripts/check_test_impact.py` | Created — core scanner |
| `scripts/hooks/pre-commit` | Extended — calls check_test_impact.py |
| `docs/work-rules/testing-protocol.md` | Extended — added "Cross-WP Test Impact" section at end |
| `docs/workpackages/workpackages.jsonl` | Updated — MNT-025 status → In Progress / Review |
| `docs/workpackages/MNT-025/dev-log.md` | Created — this file |
| `tests/MNT-025/test_mnt025_check_test_impact.py` | Created — 24 unit tests |

---

## Implementation Details

### `scripts/check_test_impact.py`

The script derives three search forms from each staged `src/` path:

- **Dotted import path** — `launcher.core.shim_config`
- **Slash path fragment** — `launcher/core/shim_config`  
- **Bare module name** — `shim_config`

For each test `.py` under `tests/`, it checks:
1. Import statements: `\b(?:import|from)\s+<dotted>\b`
2. Patch-string references (dotted/slashed only — no word-boundary needed for fully-qualified names): `["\'].*?<dotted>.*?["\']`
3. Bare-name string references with word-boundary: `["\'].*?\b<bare>\b.*?["\']`

`__init__.py` is handled as the parent package (`src/launcher/__init__.py` → `launcher`).

Results are grouped by WP directory and printed to stderr. Exit code is always 0.

### `scripts/hooks/pre-commit`

After the `validate_workspace.py` run (which may block), the hook now:
1. Collects staged `src/` files via `git diff --cached --name-only -- src/`
2. Calls `check_test_impact.py` with those files if any exist
3. Output goes to stderr (advisory warnings only)

### `docs/work-rules/testing-protocol.md`

Added section **"Cross-WP Test Impact — Developer Responsibility"** at the end of the file, which:
- References ADR-008
- Documents the pre-commit mechanism
- States the developer obligation to act on flagged tests
- Shows manual invocation and output format

---

## Tests Written

24 unit tests in `tests/MNT-025/test_mnt025_check_test_impact.py`:

| Test Class | Tests | Coverage |
|-----------|-------|---------|
| `TestModuleVariants` | 4 | Module path derivation, `__init__.py` handling |
| `TestWpIdFromTestPath` | 3 | WP directory identification |
| `TestFileReferencesModule` | 6 | Import, patch, bare-name, false-positive rejection |
| `TestScan` | 5 | Full scan logic across temp file trees |
| `TestFormatWarnings` | 3 | Advisory output, grouping, empty case |
| `TestMainExitCode` | 3 | Exit = 0 always; no staged files; non-src args |

All 24 tests pass. Result logged as TST-2617.

---

## Test Results

- **Run:** `scripts/run_tests.py --wp MNT-025 --type Unit --env "Windows 11 + Python 3.13"`
- **Result:** 24 passed / 0 failed
- **TST ID:** TST-2617

---

## Known Limitations

- The tool scans all `tests/` files on every commit — for very large test suites this adds latency, but the current suite (~60 WP directories) completes in well under 1 second.
- The bare-name check has a word-boundary constraint to reduce false positives; very short or common bare names (`io`, `re`) could still produce noise. This is acceptable for the advisory nature of the tool.
