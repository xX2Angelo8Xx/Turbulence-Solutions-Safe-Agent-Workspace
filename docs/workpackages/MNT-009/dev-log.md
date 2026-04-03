# Dev Log — MNT-009: Tester add_bug.py Mandate

## WP Summary
Fix gap G-01/X-02: `tester.agent.md` never mentioned `scripts/add_bug.py`. Added to the Edit Permissions section and Pre-Done Checklist that bugs MUST be logged via `scripts/add_bug.py` (mandatory — direct CSV editing prohibited). Aligned with `agent-workflow.md` Mandatory Script Usage table entry: `Log a bug | scripts/add_bug.py | Tester`.

**User Story:** Enabler  
**Branch:** `MNT-009/tester-add-bug-mandate`  
**ADR Check:** No relevant ADRs found in `docs/decisions/index.csv` for this domain.

---

## Changes Made

### `.github/agents/tester.agent.md`

1. **Edit Permissions section** — Updated `docs/bugs/bugs.csv` bullet to clarify it must be accessed via `scripts/add_bug.py` (direct CSV editing prohibited).

2. **Pre-Done Checklist** — Added explicit checklist item requiring bugs to be logged via `scripts/add_bug.py` (mandatory — never edit `docs/bugs/bugs.csv` directly).

3. **Constraints section** — Updated the `ALWAYS log bugs` constraint to explicitly state `scripts/add_bug.py` must be used.

---

## Tests Written

- `tests/MNT-009/test_mnt009_tester_add_bug_mandate.py`
  - Verifies `add_bug.py` is referenced in the Edit Permissions section
  - Verifies `add_bug.py` is referenced in the Pre-Done Checklist
  - Verifies `add_bug.py` is referenced in the Constraints section
  - Verifies direct CSV editing is mentioned as prohibited (in context of bugs.csv)

---

## Known Limitations

None. This is a pure documentation change to an agent instruction file.
