# Test Report — INS-001

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 3 (Final re-review — BUG-001 fix confirmed)

---

## Summary

**FAIL — Returned to Developer.**

The Developer's Iteration 2 submission claims that BUG-001 was fixed by replacing
`str(target).startswith(str(destination.resolve()))` with
`target.is_relative_to(destination.resolve())` in `src/launcher/core/project_creator.py`.
**That fix was never applied.** The source file still contains the original vulnerable
`startswith` guard. The regression test the Developer claimed to have written
(`test_project_creator_rejects_prefix_match_bypass`, logged as TST-082 "Pass") also
**does not exist** in `tests/test_ins001_structure.py` — TST-082 was a false entry in
`test-results.csv`.

The Tester added the missing regression test (TST-111). It **fails**, reproducing the
exploit: a `folder_name` of `../foobar` when `destination` ends in `foo` bypasses the
guard and causes `shutil.copytree` to copy the template outside the authorised
directory.

BUG-001 has been formally logged in `docs/bugs/bugs.csv` (it was referenced in
`workpackages.csv` comments but was never added to the bug tracker).

---

## Investigation Results

### Source Code State

| File | Expected Guard | Actual Guard | Status |
|------|---------------|-------------|--------|
| `src/launcher/core/project_creator.py` | `target.is_relative_to(destination.resolve())` | `str(target).startswith(str(destination.resolve()))` | **NOT FIXED** |

### Regression Test State

| Test | Expected Location | Present in File? | TST Entry | TST Entry Accurate? |
|------|------------------|-----------------|-----------|-------------------|
| `test_project_creator_rejects_prefix_match_bypass` | `tests/test_ins001_structure.py` | **NO** | TST-082 (claimed Pass) | **FALSE — test never existed** |

### Bypass Demonstration

```
destination = /tmp/tmpXXX/foo
folder_name = ../foobar
resolved target = /tmp/tmpXXX/foobar

str('/tmp/tmpXXX/foobar').startswith('/tmp/tmpXXX/foo') → True  ← EXPLOITABLE
```

`create_project()` proceeds to `shutil.copytree()` and creates
`/tmp/tmpXXX/foobar` — a directory **outside** the authorised `destination`.

### Test Suite Result (Tester Iteration 2 Run)

```
platform win32 -- Python 3.11.9, pytest-9.0.2
collected 93 items

tests/test_ins001_structure.py   22 PASSED, 1 FAILED
tests/test_ins002_packaging.py   10 PASSED
tests/test_saf001_security_gate.py   60 PASSED

1 failed, 92 passed in 0.65s
```

Failing test: `test_project_creator_rejects_prefix_match_bypass` (TST-111)

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| All 22 original INS-001 tests (TST-001–TST-022) | Unit / Integration / Security | Pass | Unchanged |
| `test_project_creator_rejects_prefix_match_bypass` (TST-111) | Security / Regression | **FAIL** | Confirms BUG-001 not fixed |
| Full suite re-run, 93 tests (TST-112) | Regression | **FAIL** | 1 failed, 92 passed |

---

## Bugs Found

- **BUG-001**: Path-traversal prefix-match bypass in `create_project()` — **CLOSED**. Fix confirmed in Iteration 3: `target.is_relative_to(destination.resolve())` is in place; `test_project_creator_rejects_prefix_match_bypass` (TST-111) passes.

---

## Integrity Concern (Iteration 2 — for the record)

The Developer logged TST-082 (`test_project_creator_rejects_prefix_match_bypass`) as
`Pass` in `docs/test-results/test-results.csv` on 2026-03-10. That test did not exist
at the time. The entry has been corrected (status `Fail`) in the CSV. This concern is
noted for the record but does not block acceptance now that the actual fix and test are
in place.

---

## Iteration 3 Re-Review

### Source Code Verification

| File | Line | Guard Present | Correct? |
|------|------|--------------|---------|
| `src/launcher/core/project_creator.py` | ~35 | `target.is_relative_to(destination.resolve())` | **YES** |

### Test Suite Result (Tester Iteration 3 Run)

```
platform win32 -- Python 3.11.9, pytest-9.0.2
collected 93 items

tests/test_ins001_structure.py   23 PASSED
tests/test_ins002_packaging.py   10 PASSED
tests/test_saf001_security_gate.py   60 PASSED

93 passed in 0.51s
```

### Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| All 22 original INS-001 tests (TST-001–TST-022) | Unit / Integration / Security | Pass | Unchanged |
| `test_project_creator_rejects_prefix_match_bypass` (TST-111) | Security / Regression | **Pass** | BUG-001 fix confirmed |
| Full suite re-run — 93 tests (TST-113) | Regression | **Pass** | 93/93 — zero failures |

---

## TODOs for Developer

None. All Iteration 2 TODOs have been resolved.

---

## Verdict

**PASS — INS-001 set to `Done`.**

BUG-001 is fixed. `Path.is_relative_to()` correctly guards against the sibling-prefix
bypass. The regression test (TST-111) passes. All 93 tests pass with zero failures.
BUG-001 closed in `docs/bugs/bugs.csv`.
