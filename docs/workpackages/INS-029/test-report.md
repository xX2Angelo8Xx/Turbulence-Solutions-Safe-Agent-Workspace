# Test Report — INS-029: Bump version to 3.2.4 and tag release

## Summary

**Verdict: PASS**

All version files correctly updated to `3.2.4`. All 33 tests pass (11 Developer + 6 Tester edge cases + 16 FIX-078 regression).

---

## Review Findings

### Files Changed (from `git diff HEAD~1 --name-only`)

| File | Expected Change | Verified |
|------|----------------|----------|
| `pyproject.toml` | `3.2.3` → `3.2.4` | ✅ |
| `src/launcher/config.py` | `3.2.3` → `3.2.4` | ✅ |
| `src/installer/windows/setup.iss` | `3.2.3` → `3.2.4` | ✅ |
| `src/installer/macos/build_dmg.sh` | `3.2.3` → `3.2.4` | ✅ |
| `src/installer/linux/build_appimage.sh` | `3.2.3` → `3.2.4` | ✅ |
| `tests/FIX-078/test_fix078_version_323.py` | `EXPECTED_VERSION` updated | ✅ |
| `tests/FIX-078/test_fix078_edge_cases.py` | All version assertions updated | ✅ |
| `tests/INS-029/test_ins029_version_bump.py` | New — 11 tests | ✅ |

### Version Consistency

All 5 canonical version files confirmed at `3.2.4`. Grep scan of `src/` found zero stale `3.2.3` references.

### No Unrelated Changes

The commit contains no scope creep. Only the 5 source files, the FIX-078 test updates (legitimate follow-on), and new INS-029 tests were changed.

---

## Test Execution

### Test Run 1 — Developer tests only
- **Command:** `.venv\Scripts\python.exe -m pytest tests/INS-029/ tests/FIX-078/ -v --tb=short`
- **Result:** 27 passed, 0 failed
- **Logged:** TST-2278 (covers full 33-test run after Tester additions)

### Test Run 2 — Full suite including Tester edge cases
- **Command:** `.venv\Scripts\python.exe -m pytest tests/INS-029/ tests/FIX-078/ -v --tb=short`
- **Result:** 33 passed, 0 failed

---

## Edge Cases Added (`tests/INS-029/test_ins029_edge_cases.py`)

| Test | Description |
|------|-------------|
| `test_no_stale_version_in_setup_iss` | setup.iss must not contain `3.2.3` as `MyAppVersion` |
| `test_no_stale_version_in_build_dmg` | build_dmg.sh must not contain `3.2.3` as `APP_VERSION` |
| `test_no_stale_version_in_build_appimage` | build_appimage.sh must not contain `3.2.3` as `APP_VERSION` |
| `test_version_tuple_greater_than_stale` | `parse_version("3.2.4") > parse_version("3.2.3")` |
| `test_version_tuple_components` | `parse_version("3.2.4")` returns exactly `(3, 2, 4)` |
| `test_egg_info_pkg_info_version_not_future` | egg-info must not claim a version newer than `3.2.4` |

**Note on `test_egg_info_pkg_info_version_not_future`:** During testing, `src/agent_environment_launcher.egg-info/PKG-INFO` was found to report `Version: 3.1.0` — a stale pre-existing condition unrelated to this WP. The test was designed to guard against future mis-merges (too-high version) rather than enforce equality with a generated artifact. Bug logged as BUG-155.

---

## Bugs Found

| ID | Severity | Title | Notes |
|----|----------|-------|-------|
| BUG-155 | Low | Stale egg-info: `importlib.metadata` returns `3.1.0` not `3.2.4` | Pre-existing, not introduced by INS-029. `get_display_version()` fallback to `VERSION` constant is unaffected for production builds. Fix: `pip install -e .` in the dev venv. |

---

## Security Review

No security concerns. This WP contains only string constant changes to version identifiers. No executable logic, no network calls, no file I/O changes aside from the version strings.

---

## Validation

```
scripts/validate_workspace.py --wp INS-029 → All checks passed (exit 0)
```

---

## Verdict

**PASS** — WP set to `Done`.
