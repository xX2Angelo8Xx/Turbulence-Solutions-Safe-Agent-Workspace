# Test Report — SAF-059

**Tester:** Tester Agent
**Date:** 2026-03-30
**Iteration:** 1

## Summary

SAF-059 fixes four terminal command filtering inconsistencies in `security_gate.py`. All four bugs are correctly addressed and fully tested. The implementation is sound from both a correctness and security perspective. 76 new tests pass, 812 regression tests pass, and no existing tests regress.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2250: Developer suite (51 tests) | Unit | PASS | BUG-140/141/142/143 scenarios + critical Stage 3 bypass tests |
| TST-2251: Tester edge-case suite (25 tests) | Security | PASS | Paren+deny-zone, nested paren, paren+pipe, subshell variants, chained segment bypass attempts |
| TST-2252: Regression suite (812 tests) | Unit | PASS | SAF-005/006/014/015/016/020/026/028/035/036 — zero regressions |

**Total: 888 tests, 888 passed, 0 failed**

## Code Review

### BUG-140 (Remove-Item vs del — Stage 3 false-positive)
- **Fix verified:** `_CRITICAL_OBFUSCATION_INDICES` (indices 8,12,14,15,16,17,26) correctly identify only the truly dangerous patterns (pipe-to-interpreter, subshell, process substitution). Non-critical patterns are skipped for allowlisted-verb segments.
- **Security correctness:** Pipe-to-interpreter and subshell patterns still fire on ALL segments including allowlisted ones. `del project/exec-scripts/file.txt` and `remove-item project/source/main.py` now pass; `del project/f.txt | bash` still denies. ✓

### BUG-141 (dir -Name blocked)
- **Fix verified:** `-Name` is already handled correctly by `_validate_args` (tokens starting with `-` are flags, not path args). The WP adds explicit regression tests. No code change was needed.
- **Test coverage:** `dir -Name`, `dir -Name project/`, `dir -Name -Force`, `dir -Name -Filter *.py` all pass correctly. ✓

### BUG-142 (Parenthesized subexpressions)
- **Fix verified:** `_PAREN_SUBEXPR_RE = r'^\((.+)\)(?:\.[A-Za-z_][A-Za-z0-9_]*)*\s*$'` correctly unwraps `(cmd).Property` patterns in both Stage 3 pre-scan (for allowlist determination) and Stage 4 (for verb extraction and arg validation).
- **Security correctness:**
  - `(iex exploit).Length` → denied (iex not in allowlist) ✓
  - `(Get-Content .github/secret).Count` → denied (deny zone) ✓
  - `$(...)` subshell still caught by Stage 3 critical P-19 before reaching paren check ✓
  - `diff <(cat f) <(cat g)` process substitution still denied by P-28 ✓
- **Known limitation (not a bug):** Double-nested parens like `((Get-Content f.txt).Split(",")).Count` fail closed (denied) — single-level unwrap only. This is acceptable; failing closed is the correct security posture. ✓

### BUG-143 (Test-Path not in allowlist)
- **Fix verified:** `test-path` added to Category G with `path_args_restricted=True, allow_arbitrary_paths=False`. Allowlist entry confirmed in tests. ✓
- **Security correctness:** `Test-Path .github/hooks` → denied; `Test-Path project/` → allowed. ✓

### _PAREN_SUBEXPR_RE Regex Security Analysis
- **Zero-property matches** (`(Remove-Item project/file.txt)` with no `.Property`) are handled correctly — the regex allows zero property accesses (quantifier `*`). Deny-zone paths still denied; blocked verbs still denied. ✓
- **Greedy backtracking edge case:** For strings like `(cmd).Split(",")` where the property has parentheses (e.g., `Split(",")` is not a pure identifier), the regex fails to match and the segment is denied. Failing closed. ✓
- **Critical patterns apply to full command text** (`all_non_venv_lowered`) — a pipe-to-iex inside parens is still caught at Stage 3 before reaching the paren unwrap. ✓

## Tester Edge Cases Added (`tests/SAF-059/test_saf059_tester_edge_cases.py`)

25 tests across 6 test classes:

1. **`TestParenRemoveItemDenyZone`** (6 tests) — `(Remove-Item deny-zone).Count` correctly denied; `(Remove-Item project/...).Count` allowed; combined BUG-140+142 (exec-path + paren) passes.
2. **`TestParenNoPropertyAccess`** (4 tests) — Zero-quantifier paren expressions work; iex still denied regardless of path; no-property paren wrapping of allowed command works.
3. **`TestTestPathDenyZoneVariants`** (4 tests) — Trailing slash, paren-wrapped, `.ToString` form, and `security_gate.py` path all denied.
4. **`TestNestedParens`** (2 tests) — Double-wrapped parens correctly fail closed (single-level unwrap).
5. **`TestParenPipeCombos`** (3 tests) — Paren expression followed by `| Out-File`, `| iex`, and bare `| iex` all correctly denied.
6. **`TestSubshellSyntax`** (3 tests) — `$(iex cmd)`, `$(malicious)` in arg, `$(malicious)` in chained segment all denied.
7. **`TestChainedSegments`** (3 tests) — Safe segment followed by `(iex ...).Count` correctly denied; reverse order denied; bare `Remove-Item .github/` denied.

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All four bugs (BUG-140, BUG-141, BUG-142, BUG-143) are correctly fixed. Security posture is maintained: critical Stage 3 patterns always apply to all non-venv segments, deny-zone enforcement works through paren unwrapping, and blocked verbs (iex, Invoke-Expression) remain denied in all syntactic forms. 888 tests pass with zero failures or regressions.
