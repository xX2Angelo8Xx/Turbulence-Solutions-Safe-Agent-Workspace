# Test Report — SAF-073

**Tester:** Tester Agent (GitHub Copilot)
**Date:** 2026-04-02
**Iteration:** 2 (re-test after BUG-180 and BUG-181 fixes)

## Summary

**PASS.** All 24 SAF-073 tests pass, including the two regression tests added during
Iteration 1 (T12: curly-brace env-var, T13: `base64 -d` short flag). The SAF regression
suite (SAF-070 → SAF-073, 78 tests) is clean. Both High-severity bypasses reported in
Iteration 1 are confirmed fixed.

---

## Iteration 1 Summary (for traceability)

The initial implementation passed 11/11 developer tests but edge-case testing revealed
**two security bypasses**: `${HOME}` (BUG-180) and `base64 -d` (BUG-181), both returning
`ask` instead of `deny`. The WP was returned to the Developer as FAIL.

---

---

## Tests Executed — Iteration 2

| Test ID | Test Name | Type | Result | Notes |
|---------|-----------|------|--------|-------|
| TST-2451 | SAF-073 Developer Suite (11 tests) | Security | **Pass** | Iteration 1: all 11 pass |
| TST-2452 | SAF-073 Tester Edge-Cases (13 tests) | Security | **Fail** | Iteration 1: 2/13 fail (BUG-180, BUG-181) |
| TST-2453 | SAF Regression Suite | Regression | **Pass** | Iteration 1: 0 new failures |
| TST-2455 | SAF-073 Full Suite Re-run (24 tests) | Security | **Pass** | Iteration 2: all 24 pass after Developer fixes |
| TST-2456 | SAF Regression SAF-070→SAF-073 (78 tests) | Regression | **Pass** | Iteration 2: no regressions |

### Iteration 2 edge-case results (previously failing T12 and T13)

| TC | Command | Expected | Actual | Result |
|----|---------|----------|--------|--------|
| T12 | `echo ${HOME}` (curly-brace syntax) | deny | deny | **PASS** — BUG-180 fixed |
| T13 | `echo payload \| base64 -d` (short flag) | deny | deny | **PASS** — BUG-181 fixed |

### Iteration 1 edge-case detail (TST-2452, retained for traceability)

| TC | Command | Expected | Actual (iter 1) | Result |
|----|---------|----------|--------|--------|
| E01 | `echo $home` (already lowercase) | deny | deny | PASS |
| E02 | `echo ${HOME}` (curly-brace syntax) | deny | **ask** | **FAIL** — BUG-180 |
| E03 | `echo $RANDOM` (non-sensitive var) | ask | ask | PASS — no false positive |
| E04 | `printenv HOME` (no $ prefix) | ask | ask | PASS — accepted limitation |
| E05 | `echo hello; cat /etc/passwd` (semicolons) | deny | deny | PASS |
| E06 | `echo aGVsbG8= \| base64 --decode` | deny | deny | PASS |
| E07 | `echo aGVsbG8= \| base64 -d` (short flag) | deny | **ask** | **FAIL** — BUG-181 |
| E08 | `cat ./project/file.txt` (relative path) | ask | ask | PASS — no false positive |
| E09 | `echo $PATH` | deny | deny | PASS |
| E10 | `export $TOKEN` | deny | deny | PASS |
| E11 | `eval(rm -rf /)` | deny | deny | PASS |
| E12 | `dir c:/windows/system32` | deny | deny | PASS |
| E13 | `cp secret.txt /tmp/exfil` | deny | deny | PASS |

---

## Bugs Found

- **BUG-180** (High, **Fixed**): `require-approval.sh` — curly-brace env-var syntax `${HOME}` bypassed SAF-073 deny guard. Fixed by adding `\{?` to the regex pattern (iteration 2).
- **BUG-181** (High, **Fixed**): `require-approval.sh` — `base64 -d` short flag bypassed SAF-073 obfuscation deny guard. Fixed by changing pattern to `base64.*(-d\b|decode)` (iteration 2).

---

## Security Analysis (Iteration 2)

Both fixes are confirmed correct and tight:

### BUG-180 Fix verified — `\$\{?(home|path|user|...)`

The `\{?` makes the opening curly brace optional, matching both `$HOME` and `${HOME}`.
The fix is minimal and does not introduce false positives (`$RANDOM` → `ask` confirmed).
`echo ${PATH}`, `echo ${TOKEN}`, `echo ${HOME}` all now correctly return `deny`.

### BUG-181 Fix verified — `base64.*(-d\b|decode)`

The pattern now catches both `base64 -d` (POSIX short flag) and `base64 --decode` (long flag).
The `\b` word boundary on `-d\b` prevents false matches on hypothetical flags like `-do`.
Both test vectors confirmed: `base64 -d` → deny, `base64 --decode` → deny (regression).

### No new false positives introduced

Safe commands verified in the 24-test suite continue to return `ask`:
- `echo $RANDOM` — non-sensitive var, no false-positive
- `cat ./project/file.txt` — relative path, no false-positive
- `printenv HOME` — no `$` prefix variant, accepted limitation remains

### Accepted limitations (unchanged from iteration 1)

- `printenv HOME` (no `$` prefix) returns `ask` — `printenv` could theoretically leak env vars,
  but blocking it would over-block legitimate `printenv --help` style introspection. Acceptable.
- Backtick heuristic remains (`\`` + word char). Unusual backtick-in-JSON could false-positive,
  but no real-world test vector found. Acceptable trade-off.

---

## TODOs for Developer

None. Both bugs are fixed and verified.

---

## Verdict

**PASS**

All 24 SAF-073 tests pass. Both High-severity bypasses (BUG-180, BUG-181) are fixed and
confirmed by automated regression tests. SAF-070→SAF-073 regression suite (78 tests) is clean.
Workspace validator passes. WP set to **Done**.
