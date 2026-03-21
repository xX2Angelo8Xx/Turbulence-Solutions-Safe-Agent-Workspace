# Test Report — SAF-035: Implement Session-Scoped Denial Counter

**Tester:** Tester Agent
**Date:** 2026-03-21
**Iteration:** 2 (re-test after BUG-094 / BUG-095 fixes)
**Verdict:** PASS

---

## Summary

SAF-035 adds a session-scoped denial counter to `security_gate.py`. On each deny
decision the counter increments, displays "Block N of M" in the deny reason, and
locks the session (denying ALL tool calls) once the threshold M=20 is reached.
Session identity is derived from OTel JSONL or a fallback UUID.

All acceptance criteria verified. BUG-094 and BUG-095 confirmed fixed. No regressions
introduced. Template directory remains clean.

---

## Iteration 2 Focus

The Developer addressed two bugs from Iteration 1:

- **BUG-094** — SAF-024 regressions: 7 SAF-024 tests asserted `reason == _GENERIC_MESSAGE`
  and broke because SAF-035 prepends "Block N of M." to deny messages. Fix: changed
  assertions to `_GENERIC_MESSAGE in reason`.
- **BUG-095** — Template directory pollution: tests calling `main()` wrote `.hook_state.json`
  to `templates/coding/.github/hooks/scripts/`. Fix: added a global autouse conftest
  fixture `_prevent_hook_state_writes` that mocks `_load_state`, `_save_state`, and
  `_get_session_id`, with cleanup in teardown. SAF-035-local conftest overrides the
  fixture for its own unit tests.

---

## Test Results

| Suite | Tests | Result |
|-------|-------|--------|
| SAF-035 (developer + tester edge cases) | 56 | **56 passed** |
| SAF-024 (generic deny messages) | 20 | **20 passed** |
| Full regression suite (excl. yaml import errors) | 4482 passed, 76 failed, 2 skipped | Same 76 failures as main |
| Full regression suite (with yaml imports) | 14 collection errors | Pre-existing (yaml not installed) |

### Pre-existing failures (76) — verified identical on main

All 76 failures are present on the `main` branch with the exact same count (76 failed,
4426 passed). The SAF-035 branch adds 56 net new passing tests (4482 − 4426 = 56).
Zero new failures introduced by SAF-035.

Affected WPs: FIX-009, FIX-019, FIX-028, FIX-031, FIX-036, FIX-037, FIX-038,
FIX-039, FIX-049, FIX-050, INS-004, INS-019, SAF-010, SAF-022, SAF-025.

---

## Bugs Filed (Iteration 1) — Now Fixed

| Bug ID | Severity | Title |
|--------|----------|-------|
| BUG-094 | High | SAF-035 counter causes SAF-024 test regressions | **Fixed** |
| BUG-095 | High | Counter writes .hook_state.json to template directory during tests | **Fixed** |

---

## Verification Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | All 56 SAF-035 tests pass | PASS |
| 2 | All 20 SAF-024 tests pass (previously 7 failed) | PASS |
| 3 | No `.hook_state.json` in `templates/coding/.github/hooks/scripts/` after test run | PASS |
| 4 | Full regression suite: zero new failures vs main | PASS (76 = 76) |
| 5 | BUG-094 marked "Fixed" in bugs.csv | PASS |
| 6 | BUG-095 marked "Fixed" in bugs.csv | PASS |
| 7 | Counter increments on each deny | PASS |
| 8 | Session locks at threshold M | PASS |
| 9 | Session isolation (independent counters) | PASS |
| 10 | OTel JSONL extraction (session.id + gen_ai.conversation.id) | PASS |
| 11 | UUID fallback when JSONL missing | PASS |
| 12 | "Block N of M" in deny reason | PASS |
| 13 | Locked session denies ALL tools (including always-allow) | PASS |
| 14 | Corrupt/empty state file handled gracefully | PASS |
| 15 | Atomic write (tempfile + os.replace) | PASS |
| 16 | `.gitignore` excludes `.hook_state.json` and `copilot-otel.jsonl` | PASS |
| 17 | OTel settings added to `.vscode/settings.json` | PASS |

---

## Code Review Observations

### Implementation Quality
- **Atomic writes**: `_save_state` uses `tempfile.mkstemp` + `os.replace` — correct for
  preventing partial-write corruption.
- **Defensive parsing**: `_load_state` handles corrupt JSON, non-dict JSON, missing files,
  and permissions errors. Returns empty dict on any failure.
- **OTel parsing**: `_read_otel_session_id` uses type checks at every level of the nested
  structure, catching all possible malformed data shapes.
- **Lock check placement**: Session lock is checked in `main()` before `decide()`, ensuring
  locked sessions are denied immediately without executing gate logic.
- **_DENY_REASON unchanged**: The generic policy message constant is preserved, and
  "Block N of M" is prepended as a prefix — SAF-024 compliance maintained.

### Security Analysis
- **Path traversal in session IDs**: Session IDs are dictionary keys only — never used to
  construct file paths. Verified by EC-08/EC-09/EC-10 edge-case tests.
- **No information leakage**: Deny messages contain only "Block N of M" + generic policy
  text. Zone names never appear in deny responses. Verified by EC-13/EC-14 tests.
- **State file location**: Fixed in `.github/hooks/scripts/` — within the same directory
  structure already controlled by the security gate.

### Conftest Fixture Architecture
The `_prevent_hook_state_writes` fixture in `tests/conftest.py` is well-designed:
1. Mocks `_load_state` → returns `{}`
2. Mocks `_save_state` → no-op
3. Mocks `_get_session_id` → returns `("test-fixture-session", {})`
4. Teardown: removes `.hook_state.json` if created by subprocess tests
5. SAF-035 conftest: no-op override so unit tests can call real functions

### Edge Cases Covered (Tester Tests)
- Malformed/trailing-whitespace JSONL handling (EC-01, EC-02, EC-03)
- State file with unexpected keys (EC-04)
- Zero and negative threshold (EC-05, EC-06)
- Very large deny_count 10,000+ (EC-07)
- Session IDs with path traversal, null bytes, special JSON characters (EC-08–EC-10)
- Locked flag consistency (EC-11)
- Locked session persistence across invocations (EC-12)
- Block-N-of-M content and zone-leak prevention (EC-13)
- SAF-024 regression guard (EC-14)

---

## Test Log References

| TST ID | Description | Result |
|--------|-------------|--------|
| TST-2022 | SAF-035 Iteration 2: regression + pollution fix | Pass |
| TST-2024 | SAF-035: targeted suite (56 tests) | Pass |

---

## Verdict: PASS

All acceptance criteria verified. BUG-094 and BUG-095 confirmed fixed. No regressions
introduced. Template directory remains clean. Counter logic is correct and tested
comprehensively with 56 tests covering all 11 ACs plus 14 additional edge cases.

---

## Code Review Notes

- Implementation is clean and well-structured
- Atomic write pattern (tempfile + os.replace) is correct
- Error handling is comprehensive — all JSON/IO operations wrapped in try/except
- `_read_otel_session_id` properly validates all types before accessing nested fields
- `_increment_deny_counter` handles missing/malformed session entries
- `_DENY_THRESHOLD = 20` hardcoded as expected (SAF-036 will make it configurable)
- Lock check in `main()` happens before `decide()` — correct order
- Counter only increments on deny, not on allow — confirmed by integration test

---

## TODOs for Developer (Fix Before Re-Review)

1. **Update SAF-024 tests** to mock counter functions (`_load_state`, `_save_state`, `_get_session_id`) when calling `main()`. This prevents the counter from modifying deny messages and from writing state to the template directory.

2. **Add conftest fixture** (or update existing conftest.py) to automatically mock the counter state functions for ALL tests that import security_gate. This prevents any future test from accidentally polluting the template directory. Example:
   ```python
   @pytest.fixture(autouse=True)
   def _mock_counter_state(monkeypatch):
       """Prevent counter from writing .hook_state.json during tests."""
       monkeypatch.setattr("security_gate._load_state", lambda path: {})
       monkeypatch.setattr("security_gate._save_state", lambda path, state: None)
       monkeypatch.setattr("security_gate._get_session_id", lambda d, s: ("test-session", s))
   ```

3. **Delete** `templates/coding/.github/hooks/scripts/.hook_state.json` (artifact from test runs).

4. **Re-run the full test suite** and verify 0 SAF-035-caused failures before setting to Review.
