# Dev Log — SAF-078

**Developer:** Developer Agent
**Date started:** 2026-04-04
**Iteration:** 1

## Objective
Extend the golden-file snapshot system to lock in intentional feature behavior.
When a feature changes `security_gate.py` decisions (deny→allow or allow→deny),
the snapshot test fails with an explicit, actionable message. The developer must
update the snapshot AND document the change in `dev-log.md` under a required
`## Behavior Changes` section. This prevents future agents from silently
reverting intentional decisions. The snapshot IS the documentation.

## Prior Art / ADR Check
No ADRs directly address snapshot update workflows. SAF-076 (Done) created the
initial golden-file infrastructure this WP extends.

## Implementation Summary

### 1. `tests/snapshots/security_gate/conftest.py`
Added `pytest_addoption` to register `--update-snapshots` CLI flag. Added a
session-scoped `update_snapshots` fixture that exposes the flag value to tests.

### 2. `tests/snapshots/security_gate/test_snapshots.py`
- Changed the assertion failure message to the canonical format:
  `"Security decision changed from X to Y for scenario Z. If intentional, update
  the snapshot with --update-snapshots and document in dev-log.md."`
- Added `--update-snapshots` update path: when the flag is set and the decision
  differs from the snapshot, the snapshot JSON file is rewritten in-place with
  the new `expected_decision` value, and the test passes (allowing one-shot bulk
  updates followed by a clean re-run without the flag).

### 3. `tests/snapshots/README.md`
- Added `--update-snapshots` usage, prerequisites, and safety rules.
- Documented the dev-log `## Behavior Changes` requirement.
- Clarified "the snapshot IS the documentation" principle.
- Replaced the old manual-edit update procedure with the new flag-based one.

### 4. `docs/work-rules/agent-workflow.md`
- Added optional `## Behavior Changes` section to the dev-log template.
- Explains when to include it (only when snapshot files are updated) and what
  to document (scenario name, old decision, new decision, justification).

## Files Changed
- `tests/snapshots/security_gate/conftest.py` — added `--update-snapshots` option + fixture
- `tests/snapshots/security_gate/test_snapshots.py` — new failure message + update-snapshots path
- `tests/snapshots/README.md` — documented flag, dev-log requirement, philosophy
- `docs/work-rules/agent-workflow.md` — added Behavior Changes section to dev-log template
- `tests/SAF-078/test_saf078_behavior_locking.py` — unit tests for SAF-078

## Tests Written
- `test_snapshot_passes_when_decision_matches` — snapshot test passes when actual == expected
- `test_snapshot_fails_with_decision_change_message` — canonical error message appears when decision changes
- `test_snapshot_message_includes_scenario_name` — error message includes scenario name
- `test_snapshot_message_includes_both_decisions` — error message includes from/to decisions
- `test_update_snapshots_flag_rewrites_file` — `--update-snapshots` overwrites expected_decision in JSON
- `test_update_snapshots_flag_passes_after_rewrite` — test passes (no assert) after rewrite
- `test_readme_documents_update_snapshots_flag` — README contains --update-snapshots
- `test_readme_documents_devlog_requirement` — README mentions dev-log.md behavior change requirement
- `test_devlog_template_has_behavior_changes_section` — agent-workflow.md devlog template has ## Behavior Changes

## Known Limitations
- `--update-snapshots` rewrites only `expected_decision`. It does not update
  `expected_reason` if that field exists in the snapshot (out of scope for SAF-078).
- The update mode does not add new snapshot files — it only modifies existing ones.
