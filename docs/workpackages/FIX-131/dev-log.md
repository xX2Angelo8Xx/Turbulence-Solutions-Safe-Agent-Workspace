# Dev Log — FIX-131: CI clean-workspace .vscode tracking

**WP ID:** FIX-131  
**Branch:** FIX-131/ci-clean-workspace-vscode  
**Date:** 2026-04-08  
**Agent:** Developer Agent  

---

## ADR Check

- **ADR-011** ("Drop settings.json from Security Gate Integrity Hash", Active, 2026-04-06) is related to `.vscode/settings.json` in the agent-workbench template. It confirms settings.json was intentionally excluded from the security gate integrity hash. No conflict with this WP — we are force-tracking the clean-workspace settings.json for CI availability, not adding it to any hash check.

---

## Root Cause

The repository-level `.gitignore` contains `.vscode/` which prevents `templates/clean-workspace/.vscode/settings.json` from being committed. On CI, `actions/checkout` only provides tracked files, so the file is absent on CI. This causes:

1. `tests.DOC-063` tests failing because `create_project()` copies the template but the destination lacks `.vscode/settings.json`.
2. `tests.DOC-064` and `tests.FIX-122` failing because MANIFEST.json references the file but it doesn't exist on CI.
3. `pytest.internal` appearing as a CI failure because it's not in the regression baseline.

The `templates/agent-workbench/.vscode/settings.json` was previously force-added — the same approach is applied here.

---

## Implementation

### Fix 1: Force-track `templates/clean-workspace/.vscode/settings.json`

```bash
git add -f templates/clean-workspace/.vscode/settings.json
```

This overrides `.gitignore` for this specific file with no changes to `.gitignore`.

### Fix 2: Add `pytest.internal` to regression baseline

Added entry to `tests/regression-baseline.json`:
```json
"pytest.internal": {"reason": "CI-only pytest collection artifact, not a real test"}
```
`_count` incremented from 220 to 221.

### Fix 3: Regenerate MANIFEST.json

Ran `scripts/generate_manifest.py` to ensure the manifest reflects the now-tracked settings.json.

---

## Files Changed

- `templates/clean-workspace/.vscode/settings.json` — force-tracked in git (content unchanged)
- `tests/regression-baseline.json` — added `pytest.internal` entry, `_count` 220 → 221
- `templates/clean-workspace/MANIFEST.json` — regenerated (hash unchanged, tracking status updated)
- `docs/workpackages/workpackages.jsonl` — WP status updated
- `docs/workpackages/FIX-131/dev-log.md` — this file

---

## Tests

No new test files needed for this WP (it's a CI infrastructure fix). The 5 previously-failing tests pass after the fix:

- `tests.DOC-063.test_doc063_clean_workspace_creation.TestCreateProjectStructure.test_vscode_settings_exists`
- `tests.DOC-063.test_doc063_clean_workspace_creation.TestCreateProjectStructure.test_vscode_settings_excludes_github`
- `tests.DOC-063.test_doc063_clean_workspace_creation.TestCreateProjectStructure.test_vscode_settings_excludes_vscode`
- `tests.DOC-064.test_doc064_tester_edge_cases.test_clean_workspace_manifest_is_current`
- `tests.FIX-122.test_fix122_manifest_relocation.test_generate_manifest_check_clean_workspace`

Full test run via `scripts/run_tests.py` — see test-results.jsonl.

---

## Regression Baseline Update

Per FIX-131 scope, added `pytest.internal` to the known-failures baseline. This is a CI-only pytest collection artifact (not a real test) that should not block CI.

Per workflow rules: since FIX-131 is a FIX-xxx WP, the regression baseline entry was ADDED (not removed) because we are acknowledging the artifact, not fixing a test that previously failed.

Note: The 5 failing tests (DOC-063, DOC-064, FIX-122) were not in the baseline — they were genuine CI failures fixed by this WP.
