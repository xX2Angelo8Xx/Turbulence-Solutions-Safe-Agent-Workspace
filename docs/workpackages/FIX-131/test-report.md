# Test Report — FIX-131: CI clean-workspace .vscode tracking

**Tester:** Tester Agent  
**Date:** 2026-04-08  
**Branch:** FIX-131/ci-clean-workspace-vscode  
**Verdict:** ✅ PASS

---

## Summary

FIX-131 force-tracks `templates/clean-workspace/.vscode/settings.json` in git so CI checkout includes the file, resolving 5 previously-failing tests (3 × DOC-063, 1 × DOC-064, 1 × FIX-122). It also adds `pytest.internal` to the regression baseline to suppress a CI-only collection artifact.

---

## Requirements Verification

| Acceptance Criterion | Status |
|---------------------|--------|
| `templates/clean-workspace/.vscode/settings.json` force-tracked in git | ✅ Verified (`git ls-files` returns the file) |
| Previously-failing DOC-063/DOC-064/FIX-122 tests now pass | ✅ Verified (all 3 formerly-failing DOC-063 tests + DOC-064::test_clean_workspace_manifest_is_current + FIX-122::test_generate_manifest_check_clean_workspace now pass) |
| `pytest.internal` added to regression baseline | ✅ Verified (key present, _count=221 matches 221 entries) |
| MANIFEST.json regenerated with correct SHA256 | ✅ SHA256 c9cd0834… matches actual file on disk |
| `.gitignore` not modified (force-add approach preserved) | ✅ `.vscode` remains in `.gitignore` |
| No new regressions introduced | ✅ All pre-existing failures remain in baseline |

---

## Test Runs

### FIX-131 Unit Tests (Developer, TST-2780)

Logged by Developer Agent pre-handoff — 7 tests, all passed.

### FIX-131 Unit + Tester Edge Cases (Tester, TST-2781)

**Command:** `.venv\Scripts\python.exe -m pytest tests/FIX-131/ -v --tb=short`  
**Result:** 12 passed, 0 failed  
**Environment:** Windows 11 + Python 3.11.9

| Test | Status |
|------|--------|
| `test_clean_workspace_vscode_settings_is_git_tracked` | PASS |
| `test_clean_workspace_vscode_settings_file_exists` | PASS |
| `test_clean_workspace_vscode_settings_is_valid_json` | PASS |
| `test_clean_workspace_vscode_settings_excludes_vscode` | PASS |
| `test_clean_workspace_vscode_settings_excludes_github` | PASS |
| `test_pytest_internal_in_regression_baseline` | PASS |
| `test_regression_baseline_count_matches_entries` | PASS |
| `test_gitignore_still_excludes_vscode` *(tester)* | PASS |
| `test_clean_workspace_settings_security_critical_in_manifest` *(tester)* | PASS |
| `test_clean_workspace_settings_sha256_matches_disk` *(tester)* | PASS |
| `test_clean_workspace_settings_terminal_sandbox_enabled` *(tester)* | PASS |
| `test_clean_workspace_settings_no_plain_text_secrets` *(tester)* | PASS |

### Previously-Failing Tests (Regression Confirmation)

**Command:** `.venv\Scripts\python.exe -m pytest tests/DOC-063/ tests/DOC-064/ tests/FIX-122/ -v --tb=short`  
- `tests/DOC-063/` — 25 passed (including 3 previously-failing vscode_settings tests)  
- `tests/DOC-064/test_doc064_tester_edge_cases.py::test_clean_workspace_manifest_is_current` — PASS  
- `tests/FIX-122/test_fix122_manifest_relocation.py::test_generate_manifest_check_clean_workspace` — PASS  
- DOC-064 agent-workbench failures (6) — all pre-existing known failures in regression-baseline.json (superseded by DOC-065), not regressions

---

## Regression Baseline Check

- _count declared: 221 ✅
- Actual known_failures entries: 221 ✅
- `pytest.internal` entry added correctly ✅
- 170 pre-existing failures (excluding DOC-064) confirmed against baseline — zero new regressions ✅

---

## ADR Check

- **ADR-011** reviewed. It confirms exclusion of `settings.json` from security gate *integrity hash* only. No conflict — this WP force-tracks the file for CI availability but does not alter any hash check.

---

## Security Review

- No credentials or secrets introduced ✅
- No `.gitignore` modification (force-add only) ✅
- `security_critical: True` properly set in MANIFEST.json for settings.json ✅
- `chat.tools.terminal.sandbox.enabled: true` confirmed present in settings.json ✅
- `chat.tools.global.autoApprove: false` confirmed present ✅

---

## Issues Found

### Minor Code Quality (fixed by Tester)

**Issue:** `test_clean_workspace_vscode_settings_is_git_tracked` contained dead code — a first `subprocess.run([sys.executable, "-m", "git", ...])` call whose result was immediately overwritten. Running `python -m git` would fail (no `git` Python module); the dead result was silently discarded before the correct `subprocess.run(["git", ...])` call. This did not affect test correctness but was misleading.

**Resolution:** Dead `subprocess.run` call removed. The test is functionally identical and cleaner. No behavioural change.

---

## Validate Workspace

`scripts/validate_workspace.py --wp FIX-131` → **All checks passed** (exit code 0) ✅

---

## Verdict

**PASS** — All requirements met, no regressions, tests clean, security review clear.
