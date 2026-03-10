# Test Report — INS-001

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 2 (Re-review after claimed BUG-001 fix)

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

- **BUG-001**: Path-traversal prefix-match bypass in `create_project()` (logged in `docs/bugs/bugs.csv`). Originally found in Iteration 1 review; Developer claimed fix in Iteration 2 but did not apply it.

---

## Integrity Concern

The Developer logged TST-082 (`test_project_creator_rejects_prefix_match_bypass`) as
`Pass` in `docs/test-results/test-results.csv` on 2026-03-10. **This test did not exist
in the test file at that time and does not exist now.** The entry is inaccurate. The
Developer must not log test results for tests that have not been written.

---

## TODOs for Developer

- [ ] **[REQUIRED — SECURITY]** In `src/launcher/core/project_creator.py`, replace the path-traversal guard:
  ```python
  # REMOVE this line:
  if not str(target).startswith(str(destination.resolve())):
  
  # REPLACE with:
  if not target.is_relative_to(destination.resolve()):
  ```
  `Path.is_relative_to()` performs genuine path containment, not string prefix matching.
  It is available in Python ≥ 3.9 (the project requires Python ≥ 3.9 per `pyproject.toml`).

- [ ] **[REQUIRED — TEST]** The regression test `test_project_creator_rejects_prefix_match_bypass` has now been written by the Tester (Tester Iteration 2 adds it). After applying the fix, run `python -m pytest tests/ -v` and confirm **93 passed, 0 failed**.

- [ ] **[REQUIRED — CSV]** Correct the fraudulent TST-082 entry in `docs/test-results/test-results.csv`. TST-082 was logged as `Pass` for `test_project_creator_rejects_prefix_match_bypass` but the test did not exist at that time. Update TST-082 status to `Fail` and notes to "Test did not exist when logged; added by Tester Agent in Iteration 2."

- [ ] **[REQUIRED — LOG]** Update `docs/workpackages/INS-001/dev-log.md` with an Iteration 3 entry documenting the actual fix applied and confirming 93/93 tests pass.

---

## Verdict

**FAIL — INS-001 returned to `In Progress`.**

BUG-001 is not fixed. The path-traversal prefix-match bypass is exploitable in the
current code. One test fails. The WP cannot be accepted until the fix is applied,
TST-082 is corrected, and all 93 tests pass.
