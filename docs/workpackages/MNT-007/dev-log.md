# Dev Log — MNT-007

**Developer:** Developer Agent
**Date started:** 2026-04-03
**Iteration:** 1

## Objective

Fix contradiction C-01: three documentation files give different, conflicting test commands for the pre-handoff test run. Standardize all three to mandate `scripts/run_tests.py` as the single final pre-handoff test tool. Remove raw `pytest -v` from the developer checklist. Clarify that `add_test_result.py` is a manual fallback only (for cases where `run_tests.py` cannot be used).

## ADR Check

No ADRs in `docs/decisions/index.csv` are directly related to the test command chain. ADR-002 ("Mandatory CI Test Gate Before Release Builds") is tangentially related but covers CI gate selection, not developer pre-handoff tooling. No supersession needed.

## Implementation Summary

Three files were edited to resolve contradiction C-01:

1. **`docs/work-rules/agent-workflow.md`** — Step 5 in the Phase 1 table updated to mandate `scripts/run_tests.py` for the test run, and to clarify `add_test_result.py` is a fallback for manual result logging only.

2. **`.github/agents/developer.agent.md`** — Pre-Handoff Checklist updated:
   - Replaced: `All tests pass: .venv\Scripts\python -m pytest tests/ -v`
   - With: `All tests pass: run via scripts/run_tests.py …` (mandatory)
   - The `add_test_result.py` bullet is now labeled "fallback only — if run_tests.py was not used".

3. **`docs/work-rules/testing-protocol.md`** — TST-ID Uniqueness section updated to label `add_test_result.py` as "fallback" explicitly (paragraph previously implied equivalence with `run_tests.py`).

## Files Changed

- `docs/work-rules/agent-workflow.md` — Step 5 table cell clarified
- `.github/agents/developer.agent.md` — Pre-Handoff Checklist items 3 & 4 updated
- `docs/work-rules/testing-protocol.md` — TST-ID Uniqueness section clarified
- `docs/workpackages/workpackages.csv` — MNT-007 status → In Progress → Review

## Tests Written

This is a documentation WP — no production code changes. Verification tests are in `tests/MNT-007/`:

- `test_mnt007_no_raw_pytest.py` — asserts that no agent or work-rules file contains the banned pattern `pytest tests/ -v`
- `test_mnt007_run_tests_mandatory.py` — asserts that all three target files mention `run_tests.py`
- `test_mnt007_add_test_result_fallback.py` — asserts that `add_test_result.py` is described as fallback in the developer checklist

## Known Limitations

None — this is a purely editorial change to documentation files.
