# Dev Log — FIX-100: Fix Staging Test Version Check

**Agent:** Developer Agent
**Branch:** FIX-100/fix-staging-version-check
**Date Started:** 2026-04-04

---

## ADR Acknowledgements

- **ADR-002 — Mandatory CI Test Gate Before Release Builds:** This WP improves the staging CI gate by ensuring version consistency is checked across all 5 version files, not just 2. This directly supports ADR-002's intent of preventing mismatched releases.

---

## Task Summary

`staging-test.yml` had a "Verify version consistency" step that only checked 2 files:
- `src/launcher/config.py`
- `pyproject.toml`

`release.yml`'s `validate-version` job checks 5 files:
- `src/launcher/config.py`
- `pyproject.toml`
- `src/installer/windows/setup.iss`
- `src/installer/macos/build_dmg.sh`
- `src/installer/linux/build_appimage.sh`

This mismatch meant a version bump could pass staging smoke tests but fail the real release pipeline because `setup.iss`, `build_dmg.sh`, or `build_appimage.sh` were not updated.

---

## Implementation

**File modified:** `.github/workflows/staging-test.yml`

Added 3 entries to the `checks` dict in the "Verify version consistency" step:

| File | Pattern |
|------|---------|
| `src/installer/windows/setup.iss` | `r'#define MyAppVersion "([^"]+)"'` |
| `src/installer/macos/build_dmg.sh` | `r'APP_VERSION="([^"]+)"'` |
| `src/installer/linux/build_appimage.sh` | `r'APP_VERSION="([^"]+)"'` |

These patterns match the exact regex patterns used in `release.yml`'s validate-version job (translated from shell `grep -oP` to Python `re.search`).

Updated the success print message to explicitly state "All 5 version files match" for clarity.

---

## Tests Written

Tests live in `tests/FIX-100/test_fix100_staging_version_check.py`.

Coverage:
1. All 5 version patterns present in the check dict
2. Pattern for `setup.iss` matches the actual file format
3. Pattern for `build_dmg.sh` matches the actual file format
4. Pattern for `build_appimage.sh` matches the actual file format
5. Pattern for `config.py` still present (regression)
6. Pattern for `pyproject.toml` still present (regression)
7. YAML parses without error
8. "All 5" message appears in the step (not "All version files")
9. All 5 file paths are present in the YAML
10. Version mismatch detection works for setup.iss
11. Version mismatch detection works for build_dmg.sh
12. Version mismatch detection works for build_appimage.sh

---

## Files Changed

- `.github/workflows/staging-test.yml` — added 3 missing version file checks
- `docs/workpackages/workpackages.csv` — status updated to In Progress / Review
- `docs/workpackages/FIX-100/dev-log.md` — this file
- `tests/FIX-100/test_fix100_staging_version_check.py` — unit tests

---

## Known Limitations

None. The fix is a straightforward dict extension mirroring release.yml's patterns.
