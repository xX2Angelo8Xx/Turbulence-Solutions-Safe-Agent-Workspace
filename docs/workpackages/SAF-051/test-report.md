# Test Report — SAF-051

**Tester:** Tester Agent
**Date:** 2026-03-25
**Iteration:** 1

---

## Summary

SAF-051 adds TTL-based session expiry (30 min) to the `_get_session_id()` fallback
path in `security_gate.py`. The fix resolves BUG-118 (denial counter persisting
workspace-wide across conversations).

The implementation is correct, well-scoped, and all acceptance criteria are met.
No regressions were introduced. One minor robustness gap (BUG-129) was found and
logged — it is low severity, out of scope for this WP, and does not affect the
functional correctness of the fix.

**Verdict: PASS**

---

## Implementation Review

### Code Changes (`security_gate.py`)

- `_FALLBACK_SESSION_TTL_SECONDS = 1800` constant added in the SAF-035 constants block. ✅
- `_get_session_id()` correctly tracks `_fallback_last_seen` as a heartbeat. ✅
- Expiry condition uses `>=` (boundary at exactly TTL triggers new session). ✅
- Corrupt/missing timestamps caught by `except (ValueError, TypeError)` → treated as expired. ✅
- OTel primary path (`_read_otel_session_id`) is returned immediately without touching fallback state — no side effects. ✅
- Heartbeat updated on every call (including non-expired sessions). ✅
- `_fallback_created` is only reset when a new UUID is issued. ✅

### Edge Cases Checked

| Scenario | Expected | Result |
|----------|----------|--------|
| Fresh empty state | New UUID4 | ✅ |
| Session active (< TTL) | Same UUID reused | ✅ |
| Session expired (> TTL) | New UUID | ✅ |
| Exactly TTL seconds ago | New UUID (`>=` comparison) | ✅ |
| 1 second before TTL | Same UUID | ✅ |
| Corrupt `_fallback_last_seen` | New UUID | ✅ |
| Missing `_fallback_last_seen` (legacy) | New UUID (migration) | ✅ |
| Empty string `_fallback_last_seen` | New UUID | ✅ |
| OTel ID available | OTel ID returned, state unmutated | ✅ |
| Counter bleed across expired session | 0 count in new session | ✅ |

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2211: SAF-051 full regression suite | Regression | Fail* | 6759 passed; 72 pre-existing failures (FIX-039, INS-019, SAF-025, etc.) |
| TST-2212: SAF-051 session scoping unit tests | Unit | Pass | 30 passed (17 developer + 13 tester edge cases) |

\* The 72 failures are pre-existing and confirmed on `main`. SAF-051 introduced no new failures.

### Tester-Added Edge Cases (`tests/SAF-051/test_saf051_tester_edge_cases.py`)

| Test Class | Tests | Finding |
|-----------|-------|---------|
| `TestFutureTimestamp` | 2 | Future `_fallback_last_seen` (negative age) → NOT expired. Correct behaviour. |
| `TestTimezoneAwareTimestamp` | 1 | Timezone-aware ISO string causes `TypeError` on naive−aware subtraction → caught → treated as expired. New UUID generated. Correct defensive behaviour. |
| `TestNonStringSessionId` | 5 | None, int, bool, list, dict all correctly trigger new UUID. |
| `TestWhitespaceSessionId` | 2 | Empty string → new UUID ✅. Whitespace-only string → **reused as-is** (see BUG-129). |
| `TestStateMutation` | 2 | State is mutated in-place; returned dict is same object. ✅ |
| `TestLongSessionId` | 1 | Valid UUID4 preserved exactly. ✅ |

---

## Bugs Found

- **BUG-129**: Whitespace-only `_fallback_session_id` accepted without validation in `_get_session_id()` (logged in `docs/bugs/bugs.csv`). **Low severity** — only reachable via manually tampered `.hook_state.json`; attacker would already have full local write access. No impact on normal operation.

---

## Security Analysis

- **No injection risk**: Session ID is stored as a dict key in the in-process state, never executed or passed to a shell.
- **No privilege escalation**: TTL logic uses only `datetime.datetime.utcnow()` (no external calls).
- **No timing attacks**: UUID4 is used for session identity, not authentication.
- **OTel path unchanged**: When the primary OTel JSONL path is active, `_get_session_id()` returns immediately without touching the fallback state — no regression.
- **Timezone-aware timestamp attack surface**: Minimal. A tampered state file with a timezone-aware timestamp is treated as expired → new session. Safe default.
- **Clock manipulation**: A forward clock jump shrinks the effective TTL; a backward jump extends it. Neither allows bypassing the denial counter — the worst outcome is a delayed reset (backward jump) which is conservative.

---

## TODOs for Developer

None required for PASS. The following is a non-blocking recommendation for a future WP:

- [ ] (Optional / future WP) `BUG-129`: Add `fallback_id.strip()` check alongside `not fallback_id` to reject whitespace-only session IDs.

---

## Verdict

**PASS — mark WP as Done.**

All SAF-051 acceptance criteria are satisfied:
- ✅ Denial counter reliably resets when new conversation starts (TTL expiry → new UUID).
- ✅ Blocks from session 1 do not carry into session 2.
- ✅ OTel primary path is unchanged and takes priority.
- ✅ No regressions in existing tests.
- ✅ 30 tests pass (17 developer + 13 tester).
- ✅ `validate_workspace.py --wp SAF-051` returns clean.
