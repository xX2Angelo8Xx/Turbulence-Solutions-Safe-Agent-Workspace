# Test Report — INS-015: CI macOS Build Jobs

## Verdict: PASS

**Date:** 2026-03-14  
**Tester:** Tester Agent  
**Branch:** `ins/INS-015-ci-macos-build`

---

## Scope Reviewed

- `.github/workflows/release.yml` — `macos-intel-build` and `macos-arm-build` jobs
- `src/installer/macos/build_dmg.sh` — architecture args and DMG output path
- `tests/INS-015/test_ins015_macos_build_jobs.py` — 31 developer tests
- `docs/workpackages/INS-015/dev-log.md` — implementation log

---

## Code Review Findings

### Correctness

| Check | Result |
|-------|--------|
| `macos-intel-build` uses `macos-13` runner | PASS |
| `macos-arm-build` uses `macos-14` runner | PASS |
| Intel passes `x86_64` to `build_dmg.sh` | PASS |
| ARM passes `arm64` to `build_dmg.sh` | PASS |
| Architecture args match `build_dmg.sh` accepted values (`x86_64` / `arm64`) | PASS |
| DMG output path `dist/*.dmg` matches `build_dmg.sh` output pattern | PASS |
| `chmod +x` present before script invocation | PASS |
| Artifact names distinct (`macos-intel-dmg` vs `macos-arm-dmg`) | PASS |
| Both jobs have exactly 6 steps | PASS |

### Security

| Check | Result |
|-------|--------|
| No `${{ secrets.* }}` in run commands | PASS |
| No `github.token` in env blocks | PASS |
| No `shell:` overrides (runner default used) | PASS |
| No Windows-specific references (choco, iscc, .exe) in macOS jobs | PASS |
| Runners are distinct (no shared runner label) | PASS |

### Regression

All other jobs (`windows-build`, `linux-build`, `release`) unaffected — confirmed via YAML parse and full suite regression run.

---

## Test Execution

### Developer tests (31 tests)

File: `tests/INS-015/test_ins015_macos_build_jobs.py`

```
31 passed in 0.20s
```

All 31 developer tests pass on first Tester run. No iteration required.

### Tester edge-case tests (18 tests)

File: `tests/INS-015/test_ins015_edge_cases.py`

Edge cases added:
1. `test_artifact_names_are_distinct` — Intel and ARM artifact names must not collide
2. `test_intel_job_does_not_pass_arm64` — arch arg cannot be swapped
3. `test_arm_job_does_not_pass_x86_64` — arch arg cannot be swapped
4. `test_macos_intel_exact_script_path` — exact path `src/installer/macos/build_dmg.sh`
5. `test_macos_arm_exact_script_path` — exact path `src/installer/macos/build_dmg.sh`
6. `test_macos_intel_chmod_before_script_invocation` — ordering guard
7. `test_macos_arm_chmod_before_script_invocation` — ordering guard
8. `test_macos_intel_no_shell_override` — no `shell:` key in any step
9. `test_macos_arm_no_shell_override` — no `shell:` key in any step
10. `test_macos_intel_no_secrets_in_run` — no `${{ secrets.*` in run commands
11. `test_macos_arm_no_secrets_in_run` — no `${{ secrets.*` in run commands
12. `test_macos_intel_no_tokens_in_env` — no `github.token` in env blocks
13. `test_macos_arm_no_tokens_in_env` — no `github.token` in env blocks
14. `test_macos_runners_are_distinct` — runners cannot be identical
15. `test_macos_intel_artifact_path_exact_glob` — path is exactly `dist/*.dmg`
16. `test_macos_arm_artifact_path_exact_glob` — path is exactly `dist/*.dmg`
17. `test_macos_intel_no_windows_references` — cross-contamination guard
18. `test_macos_arm_no_windows_references` — cross-contamination guard

```
18 passed in 0.21s
```

### Full regression suite

```
1759 passed, 2 skipped, 0 failed in 10.78s
```

---

## Issues Found

None. The implementation is correct and complete on first review.

**Dev-log minor note:** Dev-log states 27 tests but the actual file contains 31 tests. Non-blocking — the test file content is what matters.

---

## Pre-Done Checklist

- [x] `docs/workpackages/INS-015/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/INS-015/test-report.md` written by Tester
- [x] Test files exist in `tests/INS-015/` (developer: 31 + tester: 18 = 49 total)
- [x] All test runs logged in `docs/test-results/test-results.csv`
- [x] `git add -A` staged all changes
- [x] Commit: `INS-015: Tester PASS`
- [x] `git push origin ins/INS-015-ci-macos-build`
