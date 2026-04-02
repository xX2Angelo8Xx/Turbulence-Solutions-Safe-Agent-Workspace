# Test Report — SAF-072: Add deny-event audit logging to security gate

**WP ID:** SAF-072  
**Verdict:** FAIL  
**Tester:** Tester Agent  
**Date:** 2026-04-02  
**Branch:** SAF-072/deny-event-audit-logging  

---

## Summary

SAF-072 implements deny-event audit logging via `_audit_deny()` in `security_gate.py`. All 10 developer tests pass and all 13 Tester edge-case tests pass. However, the implementation introduces **1 new regression** in the SAF-036 test suite that was passing before this change. The WP is returned to the Developer for a targeted fix.

---

## Test Runs

| TST-ID | Test Suite | Type | Status | Details |
|--------|-----------|------|--------|---------|
| TST-2435 | SAF-072 Developer Tests (T01–T10) | Unit | **Pass** | 10/10 |
| TST-2436 | SAF-072 Tester Edge-Cases (EC-01–EC-10) | Security | **Pass** | 23/23 |
| TST-2437 | SAF Regression (SAF-001 to SAF-072) | Regression | **Fail** | 2678 passed, 26 failed (1 NEW regression) |

---

## Code Review

### `_audit_deny` helper (lines 1098–1133)

- Correct: Entire function wrapped in `try/except Exception: pass` — fail-safe by design.
- Correct: ISO-8601 UTC timestamp.
- Correct: 36 call sites confirmed across `sanitize_terminal_command()` (17) and `decide()` (19).
- Correct: Targets use verb or basename only. No full paths, no credential values.
- Correct: `audit.jsonl` placed in `Path(__file__).parent` = same dir as security gate.
- **Issue:** `_audit_deny` calls `_load_state()` unconditionally (when OTel SID is unavailable) to fetch the fallback session ID. This happens even when the denial counter is disabled (`counter_enabled=False`), violating the SAF-036 invariant.

### `.gitignore` update

Correct: `audit.jsonl` added so audit log is not tracked by git.

### No sensitive data review

- Targets limited to command verb or path basename. No `$env:` values, no file contents.
- Confirmed by T06 and EC-09.

---

## Bugs Found

### BUG-179 — NEW REGRESSION (BLOCKING) ★

**Test:** `tests/SAF-036/test_saf036_counter_config.py::TestDisabledCounter::test_disabled_counter_no_state_file_written`  
**Was passing before SAF-072, now fails.**

**Root cause:** `_audit_deny` reads the fallback session ID via `_load_state()` when OTel SID is unavailable. The SAF-036 test asserts that `_load_state` is never called when `counter_enabled=False`. SAF-072 violates this invariant because auditing fires independently of the counter setting.

**Failure output:**
```
AssertionError: Expected '_load_state' to not have been called. Called 1 times.
Calls: [call('.../.hook_state.json')]
```

### Pre-existing failures (NOT introduced by SAF-072)

The following test failures existed on `main` before this branch and are NOT caused by SAF-072:

| Suite | Count | Root cause |
|-------|-------|-----------|
| SAF-008 | 1 | Hash mismatch — security_gate.py modified (SAF-071 pending) |
| SAF-010 | 2 | Pre-existing (uses `python` command) |
| SAF-025 | 5 | Hash mismatch — same root cause as SAF-008 |
| SAF-047 | 2 | Pre-existing venv backslash tests |
| SAF-049 | 12 | Pre-existing agent rules doc |
| SAF-056 | 12 | Pre-existing AGENT-RULES.md |

---

## Edge-Case Analysis

| Test | Result | Notes |
|------|--------|-------|
| EC-01: Concurrent writes (20 threads) | Pass | No corruption, all lines valid JSON |
| EC-02: Unicode in tool/target | Pass | UTF-8 round-trips correctly |
| EC-03: 100 000-char target | Pass | No crash, full string written |
| EC-04: None/empty args | Pass | Fail-safe swallows all errors |
| EC-05: All lines valid JSON | Pass | ts/sid/tool/decision/reason/target present |
| EC-06: `_load_state` called for fallback SID | Pass (documents regression) | Confirms BUG-179 |
| EC-07: Timestamp is ISO-8601 UTC | Pass | `tzinfo` present |
| EC-08: File location is scripts dir | Pass | Co-located with security_gate.py |
| EC-09: Reason is documented category | Pass | All from `{zone_violation, restricted_command, restricted_tool, obfuscation_detected, env_exfiltration}` |
| EC-10: Tool name matches input | Pass | read_file/create_file/replace_string_in_file all logged correctly |

---

## Acceptance Criteria Checklist (US-075)

| AC | Met? | Notes |
|----|------|-------|
| 1. Every deny appends a JSON line to audit.jsonl | ✅ | 36 call sites confirmed |
| 2. Each entry: timestamp, session_id, tool_name, decision, reason, sanitized target | ✅ | T02/EC-05 verified |
| 3. Audit log is append-only, never truncated | ✅ | T04 verified |
| 4. File is inside denied zone (agents cannot read/modify it) | ✅ | `.github/hooks/scripts/` is denied; in `.gitignore` |
| 5. No sensitive data (full contents, credentials) | ✅ | T06/EC-09 verified |

All AC are met. The only blocker is the SAF-036 regression.

---

## Verdict: FAIL

### Required fix for Developer

**BUG-179:** Remove the `_load_state` call from `_audit_deny` to not violate SAF-036's invariant.

**Current code in `_audit_deny` (lines 1108–1116):**
```python
try:
    otel_sid = _read_otel_session_id(str(scripts_dir))
    if otel_sid:
        sid = otel_sid
    else:
        _state = _load_state(str(scripts_dir / _STATE_FILE_NAME))
        _fb = _state.get("_fallback_session_id")
        if isinstance(_fb, str) and _fb:
            sid = _fb
except Exception:
    pass
```

**Required change:** Remove the `else` branch that calls `_load_state`. When OTel SID is unavailable, fall back to `"unknown"` without reading the state file. `_audit_deny` should be fully stateless with respect to `.hook_state.json`.

**Suggested replacement:**
```python
try:
    otel_sid = _read_otel_session_id(str(scripts_dir))
    if otel_sid:
        sid = otel_sid
except Exception:
    pass
```

This change:
- Restores the SAF-036 invariant (no state file read when counter is disabled)
- Preserves OTel SID retrieval (the primary source)
- Falls back to `"unknown"` gracefully (already the default)
- Keeps `_audit_deny` fully non-invasive with respect to state management

After the fix, verify that `test_disabled_counter_no_state_file_written` passes again.

---

## Files Reviewed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — `_audit_deny` function + 36 call sites
- `templates/agent-workbench/.gitignore` — `audit.jsonl` entry added
- `tests/SAF-072/test_saf072.py` — 10 developer tests
- `tests/SAF-072/test_saf072_edge_cases.py` — 13 Tester edge-case tests (added)
