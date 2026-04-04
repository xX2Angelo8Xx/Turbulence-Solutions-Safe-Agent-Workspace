# Dev Log — MNT-012: Story Writer ADR Check

## WP Summary
Add `docs/decisions/index.csv` to the `story-writer.agent.md` Startup sequence and add an ADR-contradiction check item to its Quality Checklist.

## ADR Prior Art Check
- **ADR-004** ("Adopt Architecture Decision Records") — explicitly lists MNT-012 as a related WP. This WP _implements_ a consequence of ADR-004 (agents should be ADR-aware). No contradiction.
- **ADR-005** ("No Rollback UI") — cited in the WP description as a motivating example. Not affected.
- No other ADRs conflict with this change.

## Implementation

### Files Changed
- `.github/agents/story-writer.agent.md`
  - Added step 4 to the **Startup** section: read `docs/decisions/index.csv` and check for ADRs that may conflict with the user's request.
  - Added checklist item to the **Quality checklist before presenting the draft**: `No contradiction with existing ADRs (check decisions/index.csv)`.

### Decisions Made
- Inserted the ADR check as step 4 (after step 3 which reads user-stories.csv), so the agent has full context before drafting.
- Phrasing matches the style of existing startup steps and checklist items.

## Tests Written
- `tests/MNT-012/test_mnt012_story_writer_adr_check.py`
  - Verifies step 4 text appears in the Startup section.
  - Verifies the ADR checklist item appears in the Quality checklist section.
  - Verifies the overall file is valid Markdown with the required YAML front-matter.

## Test Results
All tests passed via `scripts/run_tests.py`.

## Known Limitations
None.
