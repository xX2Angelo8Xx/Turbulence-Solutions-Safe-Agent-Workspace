# Dev Log — FIX-122: Move MANIFEST.json inside .github/hooks/scripts/

**Status:** Review  
**Branch:** FIX-122/manifest-relocation  
**Assigned To:** Developer Agent  
**Bug Reference:** BUG-207

---

## ADR Review

**ADR-003** (Template Manifest and Workspace Upgrade System) is the primary ADR for this domain. It specifies that `MANIFEST.json` lives in `templates/agent-workbench/`. This WP changes the *internal location within each template* (from root to `.github/hooks/scripts/`) but does not change the overall MANIFEST concept. ADR-003 is noted but not superseded — the decision text references the template-level manifest, not a specific subpath. The path change will be noted here and will need to be reflected in a future ADR update if desired.

---

## Scope

Relocate `MANIFEST.json` from the template root to `.github/hooks/scripts/MANIFEST.json` in both:
- `templates/agent-workbench/`
- `templates/clean-workspace/`

Update all code consumers:
1. `scripts/generate_manifest.py` — write path
2. `src/launcher/core/workspace_upgrader.py` — read path
3. `.github/workflows/test.yml` — CI manifest-check path
4. `.github/workflows/staging-test.yml` — CI manifest-check path
5. `scripts/verify_parity.py` — manifest load path
6. Test files that assert the old location

---

## Implementation Plan

1. Update `scripts/generate_manifest.py`:
   - `_MANIFEST_PATH` constant → new subpath
   - `_SKIP_FILES` exclude entry → new relative path
   - `write_manifest()` function → new subpath
   - `check_manifest()` function → new subpath

2. Update `src/launcher/core/workspace_upgrader.py`:
   - `_MANIFEST_NAME` → relative subpath `".github/hooks/scripts/MANIFEST.json"`
   - `_load_manifest()` → use the new path directly

3. Update `.github/workflows/test.yml` → new manifest path

4. Update `.github/workflows/staging-test.yml` → new manifest path

5. Update `scripts/verify_parity.py` → `_MANIFEST_PATH` constant

6. Update failing tests:
   - `tests/DOC-057/test_doc057_manifest_scope.py`
   - `tests/DOC-062/test_doc062_clean_workspace_docs.py`
   - `tests/DOC-063/test_doc063_clean_workspace_creation.py`
   - `tests/SAF-077/test_saf077_parity.py`

7. Run `scripts/generate_manifest.py` for both templates → creates at new location

8. Delete old MANIFEST.json files from template roots

---

## Files Changed

- `scripts/generate_manifest.py` — `_MANIFEST_SUBPATH` constant and `_SKIP_FILES` updated to new path; `write_manifest()` and `check_manifest()` use `_MANIFEST_SUBPATH` relative to each template root.
- `src/launcher/core/workspace_upgrader.py` — `_MANIFEST_NAME` updated to `Path(".github") / "hooks" / "scripts" / "MANIFEST.json"`.
- `.github/workflows/test.yml` — inline manifest-check path updated.
- `.github/workflows/staging-test.yml` — inline manifest-check path updated.
- `scripts/verify_parity.py` — `_MANIFEST_PATH` constant updated to new subpath.
- `templates/agent-workbench/MANIFEST.json` — DELETED (old root location).
- `templates/clean-workspace/MANIFEST.json` — DELETED (old root location).
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` — CREATED (new location).
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json` — CREATED (new location).
- `tests/DOC-057/test_doc057_manifest_scope.py` — path assertions updated.
- `tests/DOC-062/test_doc062_clean_workspace_docs.py` — path assertions updated.
- `tests/DOC-063/test_doc063_clean_workspace_creation.py` — path assertions updated.
- `tests/FIX-102/test_fix102_ci_fixes.py` — path assertions updated.
- `tests/GUI-035/test_gui035_clean_workspace_template.py` — path assertions updated.
- `tests/GUI-035/test_gui035_edge_cases.py` — path assertions updated.
- `tests/MNT-029/test_mnt029_edge_cases.py` — path assertions updated.
- `tests/MNT-029/test_mnt029_manifest.py` — path assertions updated.
- `tests/SAF-077/test_saf077_parity.py` — path assertions updated.
- `docs/workpackages/FIX-122/dev-log.md` — this file.
- `tests/FIX-122/test_fix122_manifest_relocation.py` — new regression tests.

---

## Tests Written

- `tests/FIX-122/test_fix122_manifest_relocation.py` — 12 regression and unit tests verifying:
  - MANIFEST.json exists at new location in both templates.
  - MANIFEST.json does NOT exist at template root.
  - `generate_manifest.py --check` passes for both templates.
  - `_MANIFEST_SUBPATH` constant in `generate_manifest.py` is correct.
  - MANIFEST.json excluded from tracking itself.
  - `workspace_upgrader.py _MANIFEST_NAME` points to new location.
  - `verify_parity.py _MANIFEST_PATH` points to new location.
  - CI workflow files reference new manifest path.
- TST-2725: 12 passed, 0 failed (Windows 11 + Python 3.11).

---

## Additional Fix

Removed `__pycache__` directory from `templates/clean-workspace/.github/hooks/scripts/` — created by test runners importing template scripts, not part of the FIX-122 changes but discovered during test run. Fixed to keep GUI-035 template-pollution tests passing.

---

## Known Limitations

None.

---

## Iteration 2 — Tester Findings (2026-04-07)

**Tester verdict (Iteration 1):** FAIL — two blocking issues returned to developer.

### Issue 1 Fixed — FIX-119 stale MANIFEST.json path

`tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` line 88 still referenced the old root-level `TEMPLATE_ROOT / "MANIFEST.json"`. Updated to `TEMPLATE_ROOT / ".github" / "hooks" / "scripts" / "MANIFEST.json"`.

During verification, a deeper root cause was found: `GUI-034` had re-added `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` (which FIX-119 was supposed to have deleted). This caused both `test_duplicate_file_does_not_exist` and `test_manifest_no_agentdocs_entry` to fail with content assertion errors after the path fix. The duplicate file was deleted and `MANIFEST.json` regenerated via `scripts/generate_manifest.py` to restore the FIX-119 invariant.

### Issue 2 Fixed — DOC-063 pycache pollution (BUG-211)

`tests/DOC-063/test_doc063_clean_workspace_creation.py::TestSecurityGateFunctional` was creating `__pycache__/` in the template directory. Fixed:
- `test_security_gate_no_syntax_errors`: now uses `cfile=tmp` (NamedTemporaryFile) to redirect compiled output instead of letting `py_compile.compile()` write to the template `__pycache__/`.
- `test_security_gate_importable_and_decide_returns_action`: `finally` block now calls `shutil.rmtree(pycache)` to clean up any `__pycache__/` created by `importlib.import_module()`.

### Additional files changed in Iteration 2

- `tests/FIX-119/test_fix119_no_duplicate_agent_rules.py` — path updated to new MANIFEST.json location.
- `tests/DOC-063/test_doc063_clean_workspace_creation.py` — pycache pollution fixed in both security gate tests.
- `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` — DELETED (GUI-034 regression; FIX-119 invariant restored).
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` — regenerated (entry for deleted file removed).

### Iteration 2 Test Results

- TST-2728: FIX-122 targeted suite — 32 passed (Windows 11 + Python 3.13)
- TST-2729: FIX-122 targeted suite — 32 passed (Windows 11 + Python 3.13) [post-iteration-2]
- FIX-119 full suite: 13 passed, 0 failed
- GUI-035 TestNoTemplatePollution: 3 passed, 0 failed
- DOC-063 TestSecurityGateFunctional: 2 passed, 0 failed

---

## Iteration 3 — Tester Findings (2026-04-07)

**Tester verdict (Iteration 2):** FAIL — one additional pycache issue returned to developer.

### Issue Fixed — TestMissingACCoverage::test_security_gate_denies_noagentzone also pollutes pycache

`test_security_gate_denies_noagentzone` in `TestMissingACCoverage` imports `security_gate` via `importlib.import_module()` but its `finally` block did not clean up `__pycache__`. Added identical `shutil.rmtree(pycache)` cleanup at end of `finally` block (matching fix already applied to `TestSecurityGateFunctional::test_security_gate_importable_and_decide_returns_action`).

### Additional file changed in Iteration 3

- `tests/DOC-063/test_doc063_clean_workspace_creation.py` — pycache cleanup added to `test_security_gate_denies_noagentzone` finally block.

### Iteration 3 Test Results

- TST-2731: FIX-122 targeted suite — 32 passed (Windows 11 + Python 3.13)
- DOC-063 full suite + GUI-035 TestNoTemplatePollution in sequence: 28 passed, 0 failed
