# Test Report — SAF-069: Block env-var exfiltration in unrestricted commands

**WP ID:** SAF-069  
**Tester:** Tester Agent  
**Date:** 2026-04-02  
**Branch:** SAF-069/block-env-exfiltration  
**Verdict:** ❌ FAIL — return to Developer

---

## Summary

The SAF-069 fix correctly blocks `$env:VARNAME` tokens in all commands regardless of
`allow_arbitrary_paths`. However, Tester edge-case **T08 exposes a bypass**: the
**PowerShell brace notation `${env:VARNAME}`** (where a curly brace appears between `$`
and `env:`) passes the guard because the string `$env:` is not a substring of
`${env:USERNAME}`. This is a valid PowerShell exfiltration vector and constitutes an
incomplete security fix.

---

## Code Review

| Area | Finding |
|------|---------|
| Guard placement | ✅ Correctly inserted BEFORE the `path_args_restricted` gate. |
| Case-insensitivity | ✅ `tok.lower()` catches `$ENV:`, `$Env:` etc. |
| False positives | ✅ `$5`, `$environment` (no colon) not caught. ✅ |
| Brace syntax | ❌ `${env:USERNAME}` NOT caught — guard only checks `$env:`. |
| Scope | ✅ Runs for ALL commands, not just path-restricted ones. |
| Dev log | ✅ Present and accurate. |

---

## Test Results

| Test ID | Test Name | Type | Status |
|---------|-----------|------|--------|
| TST-2428 | SAF-069 Developer Tests T01-T07 | Security | ✅ Pass |
| TST-2429 | SAF-069 Tester Edge Cases T08-T13 | Security | ❌ Fail |
| TST-2430 | SAF-069 SAF Regression Suite (excl SAF-008) | Regression | ✅ Pass |

### Developer Tests (T01–T07) — 7/7 PASS

All 7 developer-written tests pass on the first run.

| # | Command | Expected | Actual |
|---|---------|----------|--------|
| T01 | `Write-Output $env:USERNAME` | deny | ✅ deny |
| T02 | `echo $env:GITHUB_TOKEN` | deny | ✅ deny |
| T03 | `Write-Host $env:PATH` | deny | ✅ deny |
| T04 | `echo "hello world"` | allow | ✅ allow |
| T05 | `echo price is $5` | allow | ✅ allow |
| T06 | `write-output $ENV:SECRET` | deny | ✅ deny |
| T07 | `Get-Content $env:USERPROFILE\file.txt` | deny | ✅ deny |

### Tester Edge Cases (T08–T13) — 5/6 PASS, 1 FAIL

| # | Command | Expected | Actual | Status |
|---|---------|----------|--------|--------|
| T08 | `echo ${env:USERNAME}` (PS brace syntax) | deny | allow | ❌ **FAIL** |
| T09 | `echo "$env:HOME/path"` (embedded string) | deny | ✅ deny | ✅ Pass |
| T10 | `echo hello` | allow | ✅ allow | ✅ Pass |
| T11 | `Write-Output normal_text` | allow | ✅ allow | ✅ Pass |
| T12 | `echo $environment` (no colon) | allow | ✅ allow | ✅ Pass |
| T13 | `echo safe_word $env:SECRET another_word` | deny | ✅ deny | ✅ Pass |

### T08 — Root Cause Analysis

The guard in `_validate_args()` (line ~1748, `security_gate.py`):

```python
for tok in args:
    if "$env:" in tok.lower():
        return False
```

The token for `${env:USERNAME}` is the literal string `${env:USERNAME}`.
`"$env:"` is NOT a substring of `"${env:username}"` because the `{` character appears
between `$` and `env:`, so the match fails.

PowerShell's brace notation `${env:VARNAME}` is semantically identical to `$env:VARNAME`
and **will exfiltrate the environment variable at runtime**. The guard must also check
for this pattern.

### Regression Results

- **3133 passed**, 37 failed on the SAF-only suite.
- **31 failures are pre-existing** (confirmed identical on `main` branch before this WP).
- **6 additional failures** are in SAF-025/SAF-052 hash integrity tests — expected because
  `security_gate.py` was modified. These will be resolved by SAF-071 (`update_hashes.py`).
- **No new regressions** introduced by the SAF-069 change.

---

## Bugs Found

| Bug ID | Severity | Title |
|--------|----------|-------|
| BUG-178 | High | `security_gate`: PS brace syntax `${env:VAR}` bypasses SAF-069 env-var guard |

---

## Security Analysis

1. **Confirmed bypass vector:** `echo ${env:USERNAME}` → allowed. An agent can use
   PowerShell brace notation to exfiltrate any environment variable.
2. **Other PS expansion forms not tested** (not present in tokenizer output):
   - `$($env:USERNAME)` — subexpression; shlex may split the inner tokens. Lower risk.
   - `-ArgumentList $env:VAR` — caught by existing check since `$env:` is present.
3. **Case-insensitive handling of brace syntax:** `${ENV:USERNAME}`, `${Env:PASSWORD}` —
   all would bypass the guard for the same reason.
4. **Scope:** Affects all commands with `allow_arbitrary_paths=True` (echo, Write-Output,
   Write-Host, etc.) — the exact commands this WP was meant to protect.

---

## Required Fix (for Developer)

Extend the guard in `_validate_args()` to also catch the brace notation:

```python
# SAF-069 / BUG-174 + BUG-178: Universal $env: exfiltration guard.
# Checks both $env:VARNAME and ${env:VARNAME} (PS brace syntax).
for tok in args:
    tok_lower = tok.lower()
    if "$env:" in tok_lower or "${env:" in tok_lower:
        return False
```

This is a minimal, targeted fix that:
- Still avoids false positives on `$5`, `$environment`, etc.
- Catches `${env:USERNAME}`, `${ENV:SECRET}`, `${Env:PATH}` (case-insensitive via `.lower()`).
- Requires updating `update_hashes.py` (SAF-071 already planned for this).

---

## Pre-Done Checklist (FAIL — items blocking completion)

- [x] `docs/workpackages/SAF-069/dev-log.md` — exists and non-empty
- [x] `docs/workpackages/SAF-069/test-report.md` — written by Tester
- [x] Test files exist in `tests/SAF-069/` with 13 tests
- [x] All test results logged via `scripts/add_test_result.py` (TST-2428, TST-2429, TST-2430)
- [x] BUG-178 filed in `docs/bugs/bugs.csv`
- [ ] ❌ T08 `test_echo_brace_env_syntax_denied` fails — bypass confirmed
- [ ] ❌ WP cannot be marked Done until fix applied and T08 passes

---

## Verdict: FAIL

**Return to Developer with the following TODOs:**

1. **[Must Fix — Security]** Extend the `$env:` guard to also match `${env:` pattern.
   See the "Required Fix" section above for the exact code change.
2. **[Re-test T08]** After fixing, verify that `sanitize_terminal_command("echo ${env:USERNAME}", ws)`
   returns `("deny", ...)`.
3. **[Re-run T13 for brace variant]** Also test `echo safe_word ${env:SECRET} another_word` → deny.
4. **Run full test suite** and confirm 13/13 tests pass in `tests/SAF-069/`.
5. **Do NOT run `update_hashes.py`** — that remains SAF-071's responsibility.
6. **Update `dev-log.md`** with the fix details and iteration notes.
