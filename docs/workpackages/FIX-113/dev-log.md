# Dev Log — FIX-113

**WP:** FIX-113  
**Name:** Prevent infinite-recursion and hanging tests  
**Assigned To:** Developer Agent  
**Date:** 2026-04-06  
**Branch:** FIX-113/prevent-hanging-tests  
**Status:** In Progress → Review  

---

## Prior Art Check

No ADRs directly related to pytest configuration or test recursion prevention. ADR-008 (tests-track-code) is related but exists in US-077 scope. No conflicts identified.

---

## Implementation Summary

### Root Cause

`tests/MNT-029/test_mnt029_edge_cases.py::test_baseline_no_stale_entries` called:
```python
subprocess.run([sys.executable, "-m", "pytest", "tests/", ...])
```
with no `timeout=`. This spawns a full pytest run inside pytest, which discovers and executes the same test, which spawns another pytest — infinite recursion. The test suite hangs forever.

### Layer 1 — Fix the hanging test (tests/MNT-029/test_mnt029_edge_cases.py)

Replaced the subprocess pytest approach with static file analysis:
- Read `tests/regression-baseline.json` to get `known_failures` keys
- Validate each key follows the dotted-path format (`tests.<WP-ID>.<module>.<test>`)
- Check that the module portion maps to an actual `.py` test file on disk
- Catches stale entries where test files were deleted or renamed
- Does NOT run pytest or any subprocess — no recursion possible

### Layer 2 — Add pytest-timeout (pyproject.toml)

Added `"pytest-timeout>=2,<3"` to `[project.optional-dependencies] dev` (alphabetical order) and added:
```toml
[tool.pytest.ini_options]
timeout = 30
```
Every test now has a 30-second hard limit. Tests exceeding the limit are killed and reported as FAILED. This prevents any future runaway test from blocking CI indefinitely.

### Layer 3 — Update testing-protocol.md

- Rule 6: Replaced "Never use `--timeout`" with documentation of the new 30-second default and how to extend it per-test.
- New Rule 8: **Subprocess and recursion safety** — prohibits spawning pytest via subprocess, requires `timeout=` on all `subprocess.run()` calls in test code, and recommends `pytester` fixture as the correct way to test pytest behavior.

### Layer 4 — FIX-113 regression tests (tests/FIX-113/test_fix113_timeout_guardrail.py)

6 tests verifying all guardrails are in place:
1. `pyproject.toml` has `timeout = 30` in `[tool.pytest.ini_options]`
2. `pyproject.toml` lists `pytest-timeout` in dev deps
3. `testing-protocol.md` contains MUST NOT spawn subprocess pytest rule
4. `testing-protocol.md` contains timeout= requirement for subprocess.run()
5. `test_mnt029_edge_cases.py` does not contain `"-m", "pytest"` pattern
6. No test file in `tests/` contains both `subprocess.run` and `"-m", "pytest"`

---

## Files Changed

| File | Change |
|------|--------|
| `tests/MNT-029/test_mnt029_edge_cases.py` | Replaced subprocess pytest with static analysis |
| `pyproject.toml` | Added pytest-timeout dep + [tool.pytest.ini_options] timeout=30 |
| `docs/work-rules/testing-protocol.md` | Updated rule 6, added rule 8 |
| `tests/FIX-113/test_fix113_timeout_guardrail.py` | New FIX-113 regression tests |
| `docs/workpackages/docs/workpackages/FIX-113/dev-log.md` | This file |
| `docs/workpackages/workpackages.jsonl` | FIX-113 claimed and set to Review |

---

## Tests Written

| Test | Description |
|------|-------------|
| `test_pyproject_has_timeout_ini_option` | Verifies timeout=30 in pyproject.toml |
| `test_pyproject_has_pytest_timeout_dependency` | Verifies pytest-timeout in dev deps |
| `test_protocol_has_subprocess_recursion_rule` | Verifies rule 8 text in protocol |
| `test_protocol_has_subprocess_timeout_requirement` | Verifies timeout= requirement text |
| `test_mnt029_test_does_not_spawn_subprocess_pytest` | Verifies MNT-029 fix applied |
| `test_no_test_file_spawns_subprocess_pytest` | Global recursion guard for all tests |

---

## Regression Baseline

FIX-113 is a new fix WP. No entry for FIX-113 exists in `tests/regression-baseline.json` — nothing to remove.

---

## Known Limitations

- The static analysis in Layer 1 detects missing test FILES but not individual test functions that have been renamed within a file. This is an acceptable approximation — the original test ran full pytest which caused the recursion, and any more precise check would require running pytest.
- pytest-timeout must be installed in the venv (`.venv\Scripts\pip install "pytest-timeout>=2,<3"`). CI pipelines that use `pip install -e ".[dev]"` will pick it up automatically from pyproject.toml.
