# Test Report — SAF-035

**Tester:** Tester Agent  
**Date:** 2026-03-21  
**Verdict:** FAIL

---

## Summary

SAF-035 implements a session-scoped denial counter in `security_gate.py`. The counter logic itself is well-implemented: it increments correctly, locks at threshold, persists atomically, handles corrupt/missing state, and isolates sessions independently. All 56 WP-specific tests pass.

However, the WP introduces **critical regressions in 7 SAF-024 tests** and creates a **template directory pollution problem**. These must be fixed before the WP can pass.

---

## Test Results

| Run | Scope | Result | Details |
|-----|-------|--------|---------|
| TST-2018 | SAF-035 targeted (56 tests) | **PASS** | All developer + tester edge-case tests pass |
| TST-2019 | SAF-035 targeted (dup) | **PASS** | 56 passed in 0.90s |
| TST-2020 | SAF-024 regression check | **FAIL** | 7 tests fail due to counter prefix in deny message |
| TST-2021 | Template pollution check | **FAIL** | .hook_state.json created in templates/ dir |
| TST-2017 | Full regression suite | **FAIL** | 83 failures total (7 caused by SAF-035, rest pre-existing) |

---

## Bugs Filed

| Bug ID | Severity | Title |
|--------|----------|-------|
| BUG-094 | High | SAF-035 counter causes SAF-024 test regressions |
| BUG-095 | High | Counter writes .hook_state.json to template directory during tests |

---

## Detailed Findings

### Issue 1 (Critical): SAF-024 Test Regressions — BUG-094

**Root cause:** SAF-035 modifies `main()` to prepend "Block N of M" to deny messages and return "Session locked" after threshold. SAF-024 tests call `main()` without mocking the counter functions, so the deny reason no longer matches the exact generic message.

**7 failing tests:**
1. `tests/SAF-024/test_saf024_edge_cases.py::test_main_write_tool_deny_is_generic`
2. `tests/SAF-024/test_saf024_edge_cases.py::test_main_multi_replace_deny_is_generic`
3. `tests/SAF-024/test_saf024_edge_cases.py::test_main_get_errors_deny_is_generic`
4. `tests/SAF-024/test_saf024_edge_cases.py::test_main_grep_search_deny_is_generic`
5. `tests/SAF-024/test_saf024_edge_cases.py::test_main_semantic_search_deny_is_generic`
6. `tests/SAF-024/test_saf024_edge_cases.py::test_main_unknown_tool_deny_is_generic`
7. `tests/SAF-024/test_saf024_generic_deny_messages.py::test_main_stdout_generic_on_deny`

**Fix required:** Update SAF-024 tests that call `main()` to either:
- Mock `_load_state`, `_save_state`, `_get_session_id` so the counter doesn't run, OR
- Change assertions from `reason == _GENERIC_MESSAGE` to verify `_GENERIC_MESSAGE in reason` (since the counter message still contains the generic text as a suffix), OR
- Add a conftest-level fixture that automatically mocks the counter for all test modules that import security_gate and call `main()`

### Issue 2 (Critical): Template Directory Pollution — BUG-095

**Root cause:** When any test calls `sg.main()`, the counter computes `scripts_dir = os.path.dirname(os.path.abspath(__file__))` which resolves to the actual `templates/coding/.github/hooks/scripts/` directory. The counter then writes `.hook_state.json` there.

**Consequences:**
- `templates/coding/` is the shipping template — it must never be modified by tests
- State accumulates across test runs: after 20 `main()` calls with deny outcomes, the session locks permanently
- SAF-024 tests become non-deterministic depending on execution order and history
- Confirmed: `.hook_state.json` existed with `deny_count: 20, locked: true` in the template directory

**Fix required:** Any test calling `main()` must mock `_load_state`, `_save_state`, and `_get_session_id` (or use a temporary directory). Consider adding this as an autouse conftest fixture alongside the existing safety-net mocks (conftest.py Layer 1–3).

**Cleanup required:** Delete `templates/coding/.github/hooks/scripts/.hook_state.json` from the repo.

---

## Verification Checklist

| # | Requirement | Status | Notes |
|---|------------|--------|-------|
| 1 | Counter increments on each DENY | PASS | Tests 1, EC-07 |
| 2 | Block N of M in deny reason | PASS | Tests 2, EC-13 |
| 3 | Session locked at M=20 | PASS | Test 3 |
| 4 | Locked session denies ALL tools | PASS | Test 4 |
| 5 | Independent session counters | PASS | Test 5 |
| 6 | New session starts at 0 | PASS | Test 6 |
| 7 | Returning to locked session stays locked | PASS | EC-12 |
| 8 | OTel JSONL session.id extraction | PASS | Test 7 |
| 9 | Fallback to gen_ai.conversation.id | PASS | Test 7 |
| 10 | Fallback to UUID4 when JSONL missing | PASS | Test 8 |
| 11 | .hook_state.json persistence | PASS | Test 9 |
| 12 | Corrupt/empty state handled gracefully | PASS | Test 10 |
| 13 | Atomic writes (temp + os.replace) | PASS | Test 11, code review |
| 14 | 3 OTel settings in settings.json | PASS | Verified in file |
| 15 | .gitignore entries added | PASS | copilot-otel.jsonl and .hook_state.json present |
| 16 | Hashes updated | PASS | Hash constants updated in security_gate.py |
| 17 | Malformed JSON in JSONL | PASS | EC-01 |
| 18 | State file with unexpected keys | PASS | EC-04 |
| 19 | Session ID with special chars/null | PASS | EC-08, EC-09, EC-10 |
| 20 | Very large deny_count | PASS | EC-07 |
| — | No regression in SAF-024 tests | **FAIL** | 7 tests broken by counter prefix |
| — | No template dir pollution | **FAIL** | .hook_state.json created in templates/ |

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
