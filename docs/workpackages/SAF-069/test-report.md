# Test Report — SAF-069: Block env-var exfiltration in unrestricted commands

**WP ID:** SAF-069  
**Tester:** Tester Agent  
**Date:** 2026-04-02 (Iteration 2 re-test)  
**Branch:** SAF-069/block-env-exfiltration  
**Verdict:** ✅ PASS

---

## Summary

Iteration 1 found a bypass: PowerShell brace syntax `${env:USERNAME}` was not caught by
the original `$env:` substring check. Developer fixed this in iteration 2 by extending
the guard to also check for `${env:` (case-insensitive). All 14 tests now pass, including
T08 (the bypass reproducer) and new T14 (uppercase-brace form `${ENV:USERNAME}`).

The fix is correct and complete. No new regressions were introduced.

---

## Code Review

| Area | Finding |
|------|---------|
| Guard placement | ✅ Inserted BEFORE the `path_args_restricted` gate — runs for ALL commands. |
| Case-insensitivity | ✅ `tok_lower = tok.lower()` catches `$ENV:`, `$Env:`, `${ENV:`, `${Env:`. |
| Brace syntax fix | ✅ `"${env:" in tok_lower` now catches `${env:USERNAME}`, `${ENV:SECRET}`, etc. |
| False positives | ✅ `$5`, `$environment` (no colon), plain text — all still allowed. |
| Scope | ✅ Applies to every command regardless of `allow_arbitrary_paths`. |
| Dev log (iter 2) | ✅ Accurately describes the fix and references this test finding. |

Guard code (line 1747–1750, `security_gate.py`):

```python
for tok in args:
    tok_lower = tok.lower()
    if "$env:" in tok_lower or "${env:" in tok_lower:
        return False
```

---

## Test Results

| Test ID | Test Name | Type | Status |
|---------|-----------|------|--------|
| TST-2428 | SAF-069 Developer Tests T01-T07 (Iteration 1) | Security | ✅ Pass |
| TST-2429 | SAF-069 Tester Edge Cases T08-T13 (Iteration 1) | Security | ❌ Fail (T08) |
| TST-2430 | SAF-069 SAF Regression Suite — Iteration 1 | Regression | ✅ Pass |
| TST-2432 | SAF-069 Iteration 2 Re-test T01-T14 (all 14) | Security | ✅ Pass |
| TST-2433 | SAF-069 SAF Regression Suite — Iteration 2 | Regression | ✅ Pass |

### All Tests T01–T14 — 14/14 PASS

| # | Command | Expected | Actual | Notes |
|---|---------|----------|--------|-------|
| T01 | `Write-Output $env:USERNAME` | deny | ✅ deny | Original guard |
| T02 | `echo $env:GITHUB_TOKEN` | deny | ✅ deny | |
| T03 | `Write-Host $env:PATH` | deny | ✅ deny | |
| T04 | `echo "hello world"` | allow | ✅ allow | No `$env:` |
| T05 | `echo price is $5` | allow | ✅ allow | `$` without `env:` |
| T06 | `write-output $ENV:SECRET` | deny | ✅ deny | Case-insensitive |
| T07 | `Get-Content $env:USERPROFILE\file.txt` | deny | ✅ deny | |
| T08 | `echo ${env:USERNAME}` | deny | ✅ deny | **Brace fix** |
| T09 | `echo "$env:HOME/path"` | deny | ✅ deny | Embedded in string |
| T10 | `echo hello` | allow | ✅ allow | Safe baseline |
| T11 | `Write-Output normal_text` | allow | ✅ allow | allow_arbitrary_paths, no `$env:` |
| T12 | `echo $environment` | allow | ✅ allow | No colon — no false positive |
| T13 | `echo safe_word $env:SECRET another_word` | deny | ✅ deny | Multi-arg |
| T14 | `echo ${ENV:USERNAME}` | deny | ✅ deny | **Uppercase brace** (Tester-added) |

### Regression — No New Failures

Pre-existing failures in other SAF suites confirmed unchanged vs. main branch:
- **SAF-008 / SAF-025 / SAF-052**: Hash integrity failures — expected, SAF-071 will fix.
- **SAF-010**: Hook command "ts-python" check — pre-existing, not caused by SAF-069.
- **SAF-047 / SAF-049 / SAF-056**: Doc/config pre-existing failures — not caused by SAF-069.

SAF-069 changes only `security_gate.py` and `tests/SAF-069/` — no regressions in other
security controls.

---

## Bugs Found / Resolved

| Bug ID | Severity | Title | Resolution |
|--------|----------|-------|-----------|
| BUG-177 | High | PS brace syntax bypasses SAF-069 guard | Fixed in SAF-069 iteration 2 |
| BUG-178 | High | `${env:VAR}` bypasses SAF-069 guard (detailed) | Fixed in SAF-069 iteration 2 |

---

## Security Analysis

1. **`$env:VARNAME`** — caught by `"$env:" in tok_lower`. ✅
2. **`${env:VARNAME}`** — caught by `"${env:" in tok_lower`. ✅ (iteration 2 fix)
3. **Case variants** (`$ENV:`, `$Env:`, `${ENV:`, `${Env:`) — all caught via `.lower()`. ✅
4. **False positives** (`$5`, `$environment`, `$PATH` bash-style without colon) — not blocked. ✅
5. **`%USERNAME%` (cmd.exe style)**: Not caught — but this is a separate vector, not in scope
   for SAF-069 (which targets PowerShell `$env:`). If cmd.exe support is needed, a future WP.
6. **`$($env:USERNAME)` (PS subexpression)**: Tokenizer splits this into `$(` and `$env:USERNAME)`.
   The second token contains `$env:` — caught. ✅

---

## Pre-Done Checklist

- [x] `docs/workpackages/SAF-069/dev-log.md` — exists, non-empty, covers both iterations
- [x] `docs/workpackages/SAF-069/test-report.md` — written by Tester (this document)
- [x] Test files exist in `tests/SAF-069/` with 14 tests (T01–T14)
- [x] All test results logged via `scripts/add_test_result.py` (TST-2428 through TST-2433)
- [x] BUG-177 and BUG-178 marked Fixed in `docs/bugs/bugs.csv` with `Fixed In WP = SAF-069`
- [x] `scripts/validate_workspace.py --wp SAF-069` returns exit code 0
- [x] No `tmp_` files in WP folder or test folder

---

## Verdict: ✅ PASS

WP SAF-069 is complete. Marking status to `Done`.

