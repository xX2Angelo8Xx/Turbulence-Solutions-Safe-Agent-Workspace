# Dev Log — MNT-013: Pre-Release Draft Workflow

**Status:** In Progress  
**Branch:** `MNT-013/pre-release-draft-workflow`  
**Developer:** Developer Agent  
**Date Started:** 2026-04-04  

---

## ADR Check

- **ADR-001** ("Use Draft GitHub Releases for Pre-Release Testing") — **Directly relevant.** This WP formalises the human approval gate that ADR-001 mandates. The new CI/CD section in orchestrator.agent.md makes the draft→test→publish flow explicit, in full alignment with ADR-001.
- **ADR-002** ("Mandatory CI Test Gate Before Release Builds") — Referenced. The new Step 1 preserves the validate-version and full test-gate CI jobs.

---

## Scope

Rewrite the `## CI/CD Pipeline Trigger` section in `.github/agents/orchestrator.agent.md` to introduce an explicit **Human Approval Gate** with three named steps:

1. **Step 1 — Create Draft Release** — Run `release.py`; CI builds artifacts as a draft.
2. **Step 2 — Human Approval Gate (MANDATORY STOP)** — Orchestrator halts and reports to the user. No publication without explicit user verdict.
3. **Step 3a — On Approval** — Orchestrator instructs user to publish on GitHub Releases; logs the release.
4. **Step 3b — On Rejection** — Orchestrator creates FIX workpackages from feedback, spawns Developers, returns to Step 1 with bumped version.

The `--rc` flag is clarified as cosmetic (no behavioral effect on draft/publish flow).

The `### Primary Method` and `### Fallback` subsections are retained to keep existing DOC-034 passing tests green for the orchestrator.agent.md file.

---

## Implementation Summary

### Files Changed

- `.github/agents/orchestrator.agent.md` — CI/CD Pipeline Trigger section rewritten

### Changes Made

Replaced the old 7-step primary flow (which had no explicit human gate) with a 4-step structure. The new flow:
- Uses `### Primary Method — Release Script (Draft → Human Approval → Publish)` as the primary subsection header
- Adds `#### Step 1`, `#### Step 2`, `#### Step 3a`, `#### Step 3b` subsections
- Makes the stop-and-wait behaviour unambiguous ("MANDATORY STOP")
- Clarifies `--rc` as cosmetic
- Retains all constraints that DOC-034 tests check (scripts/release.py reference, --dry-run, validate-version, venv path, 5 version file names, ### Fallback, no git tag -a in primary section)

---

## Tests Written

- `tests/MNT-013/test_mnt013_human_approval_gate.py` — 10 unit tests verifying:
  1. Human Approval Gate section exists
  2. MANDATORY STOP language present
  3. Step 1 (draft creation) present
  4. Step 2 (stop and report) present
  5. Step 3a (on approval) present
  6. Step 3b (on rejection) present
  7. FIX workpackage creation mentioned in rejection path
  8. --rc flag clarified as cosmetic
  9. Draft must not be published automatically
  10. User verdict required before publication

---

## Known Limitations

- CLOUD-orchestrator.agent.md does not exist; the DOC-034 tests that check it are in the regression baseline and pre-date this WP.
- This WP does not create or restore CLOUD-orchestrator.agent.md (out of scope).
