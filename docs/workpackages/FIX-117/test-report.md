# Test Report — FIX-117

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1  

---

## Summary

**VERDICT: FAIL**

FIX-117 correctly adds `get_changed_files` to `_ALWAYS_ALLOW_TOOLS`, removes the defunct `validate_get_changed_files()` function, updates both AGENT-RULES mirrors, and regenerates the MANIFEST. All 9 FIX-117-specific tests pass. The security audit is clean — only `get_changed_files` was added to `_ALWAYS_ALLOW_TOOLS` and no other tools were accidentally allowlisted.

However, the Developer added 14 contradicting SAF-058 tests to `tests/regression-baseline.json` but missed **one contradicting SAF-052 test**. This untracked new failure makes the full test suite appear to have a new regression, which must be resolved before the WP can be marked Done.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-117: 9 tests in `tests/FIX-117/` | Unit/Regression | PASS | All 9 pass: membership, decide() variants, doc check |
| Full test suite via `scripts/run_tests.py` | Regression | FAIL | 1 untracked SAF-052 failure; 7 pre-existing CRLF failures |
| Security audit: `_ALWAYS_ALLOW_TOOLS` diff | Manual | PASS | Only `get_changed_files` added; no accidental additions |
| AGENT-RULES.md mirror check | Manual | PASS | Both `Project/AGENT-RULES.md` and `Project/AgentDocs/AGENT-RULES.md` contain `get_changed_files \| Allowed` |
| `validate_get_changed_files` removal | Unit | PASS | `test_validate_get_changed_files_removed` passes |
| Workspace validation | Tool | PASS | `validate_workspace.py --wp FIX-117` → clean |
| BUG-197 status check | Manual | PASS | `Status: Fixed`, `Fixed In WP: FIX-117` |
| Hash integrity | Manual | PASS | `_KNOWN_GOOD_GATE_HASH` updated in security_gate.py |
| SAF-052 full test class | Regression | FAIL | 1/25 fails: `test_get_changed_files_in_always_allow_tools` |

---

## Failures Found

### FAIL-1 (Blocker): SAF-052 test not added to regression baseline

**Test:** `tests.SAF-052.test_saf052_get_changed_files.TestGetChangedFilesInAlwaysAllow.test_get_changed_files_in_always_allow_tools`

**Error:**
```
AssertionError: 'get_changed_files' unexpectedly found in frozenset({...}) : 
SAF-058: get_changed_files must NOT be in _ALWAYS_ALLOW_TOOLS
```

**Root cause:** This SAF-052 test was written after SAF-058 moved `get_changed_files` out of `_ALWAYS_ALLOW_TOOLS`. It asserts the SAF-058 behavior (NOT in always-allow). FIX-117 reverses this decision, making the test assert something that is now intentionally false. The Developer correctly identified and tracked 14 SAF-058 contradicting tests but missed this one SAF-052 test.

**Logged as:** BUG-201

**Fix required:**
Add the following entry to `tests/regression-baseline.json` under `"known_failures"`:
```json
"tests.SAF-052.test_saf052_get_changed_files.TestGetChangedFilesInAlwaysAllow.test_get_changed_files_in_always_allow_tools": {
  "reason": "SAF-052 test was written after SAF-058 moved get_changed_files out of _ALWAYS_ALLOW_TOOLS. FIX-117 unconditionally allowlists the tool, reversing the SAF-058 decision. This test assertion is intentionally superseded by FIX-117."
}
```
Update `_count` from `155` to `156` and `_updated` to `"2026-04-06"`.

---

### Pre-existing (non-blocking): Untracked CRLF regressions in build_dmg.sh

**Tests failing:**
- `tests.FIX-004.test_fix004_shell_line_endings.test_shell_scripts_use_lf`
- `tests.FIX-028.test_fix028_codesign.test_no_crlf_line_endings`
- `tests.FIX-062.test_fix062_resource_relocation.test_no_crlf_line_endings`
- `tests.FIX-063.test_fix063_internal_relocation.test_no_crlf_line_endings`
- `tests.INS-006.test_ins006_edge_cases.TestLineEndings.test_no_bare_cr`
- `tests.INS-006.test_ins006_edge_cases.TestLineEndings.test_no_crlf_line_endings`
- `tests.INS-007.test_ins007_tester.TestLineEndings.test_no_crlf_line_endings`

**Analysis:** `src/installer/macos/build_dmg.sh` has CRLF line endings. This file was **not modified** by FIX-117 (`git diff main HEAD -- src/installer/macos/build_dmg.sh` is empty). These failures existed before FIX-117 and are unrelated to this WP. BUG-031 (closed, "Fixed In WP: FIX-004") tracked the original issue — the CRLF appears to have been re-introduced since FIX-004. A separate maintenance WP should address this.

**Impact on FIX-117:** None. These are pre-existing failures that must be separately resolved. They are NOT caused by FIX-117 and are NOT blocking this WP.

---

## Security Review

| Check | Result |
|-------|--------|
| Only `get_changed_files` added to `_ALWAYS_ALLOW_TOOLS` | PASS |
| No other tools accidentally added | PASS |
| `validate_get_changed_files()` fully removed (no dead code left) | PASS |
| `decide()` dispatch block for `get_changed_files` fully removed | PASS |
| Hash updated after security_gate.py change | PASS |
| `get_changed_files` is read-only (no filesystem write capability) | PASS — confirmed in dev-log and code review |
| Tool returns only file-path metadata, not file content | PASS — confirmed by VS Code tool description |

---

## Edge Cases Assessed

- `decide()` with `.git/` at workspace root → PASS (now returns `allow`, matches FIX-117 intent)
- `decide()` with `.git/` only inside project folder → PASS
- `decide()` with no `.git/` anywhere → PASS
- `decide()` with both `.git/` locations → PASS
- Mixed-case `Get_Changed_Files` → PASS (correctly denied by non-membership; case-sensitive set)
- AGENT-RULES mirror sync (both copies updated) → PASS

---

## TODOs for Developer (Return to In Progress)

1. **[REQUIRED]** Add this entry to `tests/regression-baseline.json` `known_failures`:
   ```json
   "tests.SAF-052.test_saf052_get_changed_files.TestGetChangedFilesInAlwaysAllow.test_get_changed_files_in_always_allow_tools": {
     "reason": "SAF-052 test was written after SAF-058 moved get_changed_files out of _ALWAYS_ALLOW_TOOLS. FIX-117 unconditionally allowlists the tool, reversing the SAF-058 decision. This test assertion is intentionally superseded by FIX-117."
   }
   ```
   Update `_count` from `155` to `156` and `_updated` to `"2026-04-06"`.

2. **[REQUIRED]** Set `Fixed In WP: FIX-117` on BUG-201 in `docs/bugs/bugs.jsonl`.

3. **[REQUIRED]** Re-run `scripts/run_tests.py --wp FIX-117 --type Regression --env "Windows 11 + Python 3.11" --full-suite` and confirm the only remaining failures are those already in the regression baseline.

4. **[INFORMATIONAL]** The 7 pre-existing CRLF failures in `build_dmg.sh` are not your responsibility for this WP, but they should be reported to the Orchestrator for a separate maintenance/fix WP.

---

## Pre-Done Checklist

- [x] `dev-log.md` exists and is non-empty
- [ ] `test-report.md` written — this file (written by Tester)
- [x] Test files exist in `tests/FIX-117/` (9 tests)
- [ ] All test results logged via `scripts/add_test_result.py` — pending re-run after Developer fix
- [x] All bugs found during testing logged (BUG-201 via `scripts/add_bug.py`)
- [x] WP branch follows `FIX-117/allowlist-get-changed-files` convention
- [ ] `scripts/validate_workspace.py --wp FIX-117` → clean (passes currently, but must be re-verified after fix)
- [ ] Re-run full test suite confirms no untracked regressions

**Blocked items:** Items 4, 8 are blocked pending Developer fix of the regression baseline.
