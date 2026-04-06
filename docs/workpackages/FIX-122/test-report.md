# Test Report — FIX-122

**Tester:** Tester Agent
**Date:** 2026-04-07
**Iteration:** 1

## Summary

FIX-122 correctly relocates `MANIFEST.json` from both template roots to `.github/hooks/scripts/MANIFEST.json`. The core implementation is sound — new file locations are correct, consumer code (`generate_manifest.py`, `workspace_upgrader.py`, `verify_parity.py`, and both CI workflows) is properly updated, and the developer's 12 regression tests all pass. However, **two issues block the PASS verdict**:

1. **Genuine regression** — `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py::test_manifest_no_agentdocs_entry` still references the deleted root-level `MANIFEST.json`. This test fails both in isolation and in the full suite with `FileNotFoundError`. The developer missed this file when updating path assertions.
2. **Inadequate pycache fix** — The dev-log claims `__pycache__` pollution in `templates/clean-workspace/.github/hooks/scripts/` was "fixed" by deletion. In reality, every full-suite run recreates the `__pycache__` because `tests/DOC-063/test_doc063_clean_workspace_creation.py::TestSecurityGateFunctional` calls `py_compile.compile()` and imports the template Python scripts. This causes `GUI-035::TestNoTemplatePollution` to fail consistently in the full suite. BUG-211 has been filed.

**Verdict: FAIL** — return to Developer.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-122 targeted suite (32 tests, TST-2727) | Regression | PASS | All 12 developer + 20 tester edge-case tests pass |
| Full test suite (TST-2726) | Regression | FAIL | 214 failed; FIX-119 test is genuine new regression |
| Modified consumer tests (DOC-057, DOC-062, DOC-063, SAF-077, FIX-102, GUI-035, MNT-029) | Regression | PARTIAL | 165 passed; 2 GUI-035 pycache tests fail in sequence |
| generate_manifest.py --check (both templates) | Integration | PASS | Both templates in sync |
| FIX-122 tester edge cases (20 tests) | Unit / Security | PASS | Schema, symlink guard, path traversal, stale-path checks |

---

## File Verification Results

| Check | Result |
|-------|--------|
| `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` exists | PASS |
| `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json` exists | PASS |
| `templates/agent-workbench/MANIFEST.json` removed | PASS |
| `templates/clean-workspace/MANIFEST.json` removed | PASS |
| `scripts/generate_manifest.py` uses `_MANIFEST_SUBPATH` | PASS |
| `scripts/generate_manifest.py` `_SKIP_FILES` uses new path | PASS |
| `src/launcher/core/workspace_upgrader.py` `_MANIFEST_NAME` updated | PASS |
| `scripts/verify_parity.py` `_MANIFEST_PATH` updated | PASS |
| `.github/workflows/test.yml` updated | PASS |
| `.github/workflows/staging-test.yml` updated | PASS |
| `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` updated | **FAIL** — stale `TEMPLATE_ROOT / "MANIFEST.json"` at line 88 |

---

## Failures Detail

### Failure 1 — Genuine Regression: FIX-119 test uses old root path

**Test:** `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py::test_manifest_no_agentdocs_entry`

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory:
  'templates/agent-workbench/MANIFEST.json'
```

**Root Cause:** Line 88 of `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` reads:
```python
manifest = TEMPLATE_ROOT / "MANIFEST.json"
```
After FIX-122, the file is at `TEMPLATE_ROOT / ".github" / "hooks" / "scripts" / "MANIFEST.json"`.
The developer ran `grep` to find stale path assertions but missed this file — it is not in the standard `DOC-*`, `SAF-*`, or `MNT-*` test directories that were updated.

**Fix required:** Update line 88 to:
```python
manifest = TEMPLATE_ROOT / ".github" / "hooks" / "scripts" / "MANIFEST.json"
```

---

### Failure 2 — Pycache Pollution: DOC-063 contaminates GUI-035 (BUG-211)

**Tests failing in full suite:**
- `tests/GUI-035/test_gui035_edge_cases.py::TestNoTemplatePollution::test_no_pycache_directories`
- `tests/GUI-035/test_gui035_edge_cases.py::TestNoTemplatePollution::test_no_pyc_files`

**Error (in full suite, after DOC-063 runs):**
```
AssertionError: clean-workspace must not contain __pycache__ directories:
  [WindowsPath('.../templates/clean-workspace/.github/hooks/scripts/__pycache__')]
```

**Root cause:** `tests/DOC-063/test_doc063_clean_workspace_creation.py::TestSecurityGateFunctional` runs:
1. `py_compile.compile(sg_path, doraise=True)` — writes a `.pyc` file to `__pycache__/`
2. `importlib.import_module("security_gate")` — creates `__pycache__/` as a side effect

DOC-063 runs before GUI-035 in alphabetical order. The pycache it creates persists for the duration of the test session, so GUI-035 pollution tests see the contamination.

The dev-log states "Removed `__pycache__` directory... Fixed to keep GUI-035 tests passing." This fix is ephemeral — it only held for the developer's local session. Every full suite run recreates `__pycache__`.

**The GUI-035 pollution tests PASS in isolation** (when no other test has created pycache). They only fail when the full suite runs DOC-063 first. This is a test design issue in DOC-063 where side effects pollute the shared template directory.

**Note:** `templates/clean-workspace/.gitignore` correctly covers `__pycache__/`, so these files are not tracked in git. However, the on-disk presence still causes the test failure.

**Fix required (in `tests/DOC-063/test_doc063_clean_workspace_creation.py`):**

a) `test_security_gate_no_syntax_errors` — prevent pycache creation:
```python
def test_security_gate_no_syntax_errors(self):
    import os, tempfile
    sg_path = str(CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py")
    with tempfile.NamedTemporaryFile(suffix=".pyc", delete=False) as f:
        tmp = f.name
    try:
        py_compile.compile(sg_path, cfile=tmp, doraise=True)
    finally:
        os.unlink(tmp)
```

b) `test_security_gate_importable_and_decide_returns_action` — clean up pycache in finally:
```python
finally:
    import shutil
    pycache = CLEAN_TEMPLATE / ".github" / "hooks" / "scripts" / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
    # restore original modules
    ...
```

---

## Full Suite Failure Analysis

Of the 214 full-suite failures, the breakdown is:
- **106 in regression baseline** — expected, pre-existing known failures
- **1 genuine FIX-122 regression** — FIX-119 test (old MANIFEST.json root path, see Failure 1)
- **2 pycache pollution** — GUI-035 tests (caused by DOC-063; see Failure 2 / BUG-211)
- **53 SAF-073/074 timeout** — pre-existing subprocess timeout issues under full-suite resource contention; pass in isolation
- **3 SAF-077 subprocess** — pre-existing subprocess state issues; pass in isolation
- **46 other pre-existing** — version mismatch, CRLF, git-history-dependent tests, etc.; none introduced by FIX-122

The only failure directly introduced by FIX-122 is the FIX-119 stale path (Failure 1).

---

## ADR Compliance

- **ADR-003** (Template Manifest and Workspace Upgrade System) — acknowledged in dev-log. The WP changes the manifest subpath within each template, consistent with ADR-003's intent. No supersession required.
- **ADR-008** (Tests Track Code) — **VIOLATION**: `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` was not updated to track the new manifest path. ADR-008 mandates that path changes update all test assertions in the same commit.

---

## Bugs Found

- **BUG-211**: DOC-063 py_compile creates `__pycache__` in clean-workspace template, polluting GUI-035 tests (logged 2026-04-07)

---

## TODOs for Developer

- [ ] **REQUIRED**: Update `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` line 88: change `TEMPLATE_ROOT / "MANIFEST.json"` to `TEMPLATE_ROOT / ".github" / "hooks" / "scripts" / "MANIFEST.json"`.
- [ ] **REQUIRED**: Fix `tests/DOC-063/test_doc063_clean_workspace_creation.py::TestSecurityGateFunctional::test_security_gate_no_syntax_errors` to write compiled output to a tempfile (`cfile=tmp`) instead of allowing `py_compile.compile()` to write into the template `__pycache__/` directory.
- [ ] **REQUIRED**: Fix `tests/DOC-063/test_doc063_clean_workspace_creation.py::TestSecurityGateFunctional::test_security_gate_importable_and_decide_returns_action` to remove `__pycache__` in a `finally` block after the import test.
- [ ] After both fixes, run the full test suite via `scripts/run_tests.py --full-suite` and verify GUI-035 `TestNoTemplatePollution` passes and FIX-119 `test_manifest_no_agentdocs_entry` passes.
- [ ] Search for any other stale `TEMPLATE_ROOT / "MANIFEST.json"` patterns in the full test suite using: `grep -r '"MANIFEST.json"' tests/` and verify no remaining instances reference the old root-level path.

---

## Verdict

**FAIL — return to Developer (Iteration 1)**

Two existing tests fail due to issues that FIX-122 must address: one genuine regression (FIX-119 stale MANIFEST.json path) and one inadequate pycache fix (DOC-063 contaminates GUI-035). Both are actionable and narrowly scoped. The core FIX-122 implementation is correct.
