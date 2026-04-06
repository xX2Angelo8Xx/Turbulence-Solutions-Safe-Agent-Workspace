# Test Report — FIX-116

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1

## Summary

FIX-116 correctly fixes BUG-195: `validate_file_search()` in `security_gate.py` was blanket-denying any query containing `.github`, even for paths whitelisted under SAF-055 (`agents/`, `skills/`, `prompts/`, `instructions/`). The fix applies `_GITHUB_READ_ALLOWED_RE` — the same compiled regex used by `read_file`/`list_dir` — to grant consistent access for `file_search`. All other deny zones (`.vscode`, `NoAgentZone`, `.github/hooks/`, `.github/workflows/`, etc.) remain unconditionally denied. The implementation is correct, secure, and well-tested.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2668: FIX-116 full regression suite | Regression | **Fail** (expected) | 8972 passed, 80 failed, 66 errors — all failures are pre-existing known baselines (FIX-029, INS-015, INS-016, DOC-xxx) — zero new regressions |
| TST-2669: FIX-116 targeted suite | Regression | **Pass** | 33 passed, 0 failed |
| SAF-001 integrity hash | Security | Pass | Gate hash valid after code change |
| SAF-055 + SAF-043 | Unit/Security | Pass | 173 passed, 0 failed |
| Snapshot tests (security_gate/) | Snapshot | Pass | 10 passed, 0 failed |

### Developer-authored tests (24)
| Class | Tests | Result |
|-------|-------|--------|
| `TestRegressionBug195` | 6 | Pass |
| `TestGithubNonWhitelistedRemainsDenied` | 7 | Pass |
| `TestOtherDenyZonesUnchanged` | 4 | Pass |
| `TestEdgeCases` | 7 | Pass |

### Tester-added edge cases (9)
| Test | Result | Notes |
|------|--------|-------|
| `.github/agents` bare name (no trailing slash) | Pass | `$` anchor in regex correctly allows |
| `.github/instructions` bare name | Pass | Same regex boundary |
| `.github//agents/foo.md` double-slash bypass | Pass | `posixpath.normpath` collapses to single slash → allowed |
| Deep nested `.github/agents/a/b/c/d/file.md` | Pass | Recursive allowance correct |
| `.github/` trailing slash only (no subdir) | Pass | Correctly denied |
| `\.github\agents\foo.md` Windows backslash | Pass | `normalize_path` converts → allowed |
| `\.github\hooks\security_gate.py` Windows backslash | Pass | Denied after normalization |
| `None` query value | Pass | No query → allow (correct pre-existing behavior) |
| Empty string query | Pass | No deny-zone name → allow |

## Security Analysis

**Fix correctness:**
- `_GITHUB_READ_ALLOWED_RE` uses `(?:/|$)` trailing anchor — prevents prefix attacks (`.github/agents-extra/` → denied ✓).
- `.github/hooks/` (where the gate itself lives) remains denied — agents cannot see gate source via file_search ✓.
- The FIX-116 exemption in the absolute-path zone check (line ~2746) also uses the same regex — no inconsistency between relative and absolute path handling ✓.
- `.vscode` and `noagentzone` remain unconditional denies — not touched by this fix ✓.
- Path traversal inside an allowed subdir (`.github/agents/../hooks/`) is caught by the `..` check that runs after the regex check ✓.
- `normalize_path` resolves double slashes via `posixpath.normpath` — double-slash bypass not possible ✓.
- Windows backslash normalization handled correctly ✓.
- Mixed-case bypasses blocked by `query.lower()` before zone name check ✓.

**Residual risk:** None identified. The fix is minimal, surgical, and reuses an existing tested regex.

## Bugs Found

None. No new bugs discovered during testing.

## ADR Conflicts

None. Checked `docs/decisions/index.jsonl`. ADR-011 (Gate hash drop settings.json) is unrelated and not conflicting.

## Regression Baseline

No new failures introduced. All 80 failing tests in the full suite are recorded in `tests/regression-baseline.json`. FIX-116 did not remove any entry from the baseline (no existing baseline failures were fixed by this WP). This is correct — BUG-195 was not in the baseline.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

All 33 FIX-116 tests pass (24 Developer + 9 Tester-added). No security regressions. No new failures. Gate integrity hash valid. Snapshot tests clean. BUG-195 closed.
