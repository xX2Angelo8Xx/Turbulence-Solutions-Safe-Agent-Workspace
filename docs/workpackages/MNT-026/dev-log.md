# Dev Log — MNT-026: Create ADR-009 cross-WP test impact

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-05

## Prior Art Check

- ADR-008 (`docs/decisions/ADR-008-tests-track-code.md`) is directly related — it established the rule that tests must track code changes. ADR-009 extends ADR-008 by adding enforcement tooling (advisory pre-commit hook). Referenced in this ADR.
- MNT-025 created `scripts/check_test_impact.py` — the hook being documented here.

## Implementation Summary

Created `docs/decisions/ADR-009-cross-wp-test-impact.md` documenting the decision to add an advisory pre-commit hook (`scripts/check_test_impact.py`) for cross-WP test impact detection.

Added ADR-009 entry to `docs/decisions/index.jsonl`.

## Files Changed

- `docs/decisions/ADR-009-cross-wp-test-impact.md` — new ADR
- `docs/decisions/index.jsonl` — new entry for ADR-009
- `tests/MNT-026/test_adr_009.py` — tests verifying ADR existence, index entry, and content

## Tests Written

- `tests/MNT-026/test_adr_009.py`
  - `test_adr_009_file_exists` — verifies the ADR file exists
  - `test_adr_009_required_sections` — verifies Title, Status, Context, Decision, Consequences sections
  - `test_adr_009_index_entry` — verifies index.jsonl has the ADR-009 entry
  - `test_adr_009_references_mnt025` — verifies ADR-009 content references MNT-025

## Known Limitations

None. This WP is purely documentation.
