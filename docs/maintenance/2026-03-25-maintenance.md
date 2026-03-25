# Maintenance Log — 2026-03-25

**Performed by:** Maintenance Agent (GitHub Copilot — Claude Sonnet 4.6)

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 0 | Action Tracker Review | Fail | 7 proposed actions from the 2026-03-24 log were **never added** to `action-tracker.json`. Tracker still ends at ACT-011 (2026-03-20b cycle). Positives: US-033–039 added ✓; 13 WP back-references corrected ✓; BUG-093/094/095 closed ✓; orphaned `.finalization-state.json` files deleted ✓. |
| 1 | Git Hygiene | Fail | Dirty working tree: 4 uncommitted files (`docs/user-stories/user-stories.csv`, `docs/workpackages/workpackages.csv`, `scripts/_add_stories_batch.py` deleted, `scripts/_add_wps_batch.py` modified). 7 stale local branches for Done WPs: SAF-038, SAF-039, SAF-042, DOC-012, DOC-013, DOC-014, DOC-015. All branches follow `<WP-ID>/<description>` convention. No Done WPs are uncommitted — the dirty changes are CSV formatting + new Open WPs + status cascades. |
| 2 | WP–US Consistency | Warning | All structural issues from 2026-03-24 cycle are resolved: US-033–039 present; 13 back-references corrected. New gap: US-035–039 status should be `Done` (their linked WPs are all Done) but the cascade is only in the working tree (uncommitted). US-040–051 appropriately `Open`. New WPs (DOC-016–028, GUI-023, FIX-071, DOC-017) all reference valid Open US IDs. |
| 3 | CSV Integrity | Warning | `workpackages.csv`: working-tree version has 197 rows (+16 new Open WPs) with proper RFC-4180 quoting — uncommitted. `user-stories.csv`: uncommitted status cascades for US-035–039. `bugs.csv`: BUG-097 has Status=`Fixed`, fixing WP SAF-039 is Done — should be `Closed`. BUG-102 Status=`Open` with no `Fixed In WP`. `test-results.csv`: TST-1580 Status=`XFail` — non-standard enum value (persists from 2026-03-24 cycle). |
| 4 | Documentation Freshness | Pass | `architecture.md` last confirmed updated to v3.1.2 (2026-03-24 cycle). `work-rules/index.md` lists all 10 rule files; all present on disk. `copilot-instructions.md` is 32 lines (limit 40) ✓. No path references broken. SAF-036/037 counter-config features may warrant a minor architecture.md mention — low priority. |
| 5 | WP Folder Integrity | Pass | No In Progress or Review WPs. Automated validator confirms all Done WP folders have `dev-log.md`. `test-report.md` exceptions: INS-008 and MNT-001 (both registered in `validation-exceptions.json`) ✓. |
| 6 | Orphan Detection | Pass | No orphaned `.finalization-state.json` files found (previous cycle's FIX-070 and SAF-037 orphans have been deleted ✓). No orphaned WP folders. |
| 7 | Test Coverage Gaps | Pass | Automated validator reports all Done WPs have TST entries. INS-008 is a registered exception. New Done WPs (SAF-036–045, DOC-011–015, GUI-019–022, INS-022–023, MNT-002) all have test coverage per validator. TST-1580 `XFail` status unchanged from previous cycle. |
| 8 | Bug Tracking | Warning | BUG-097 (`SAF-039: percent-encoded path traversal`) has Status=`Fixed` but its fixing WP SAF-039 is `Done` — should be `Closed`. BUG-102 (`file_search allows relative .git/ queries`) is `Open` with no `Fixed In WP` assignment. No Open bugs with missing mandatory fields. |
| 9 | Structural Integrity | Pass | `copilot-instructions.md`: 32 lines ✓ (limit 40). All 10 agent files in `.github/agents/` have valid YAML frontmatter ✓ (5 standard + 5 CLOUD variants). `templates/coding/` unmodified (git diff = 0 lines) ✓. All 4 tested scripts (`validate_workspace.py`, `add_test_result.py`, `finalize_wp.py`, `csv_utils.py`) pass AST syntax check ✓. |
| 10 | Recurring Issue Tracking | Warning | **(A) Bug lifecycle stuck at "Fixed"**: 4th consecutive cycle. BUG-088/089/090 (cycle 2026-03-20), BUG-093/094/095 (cycle 2026-03-24), BUG-097 (this cycle). FIX-066/067 added tooling but auto-cascade only triggers at `finalize_wp.py` time; bugs created/linked after finalization are missed. **(B) Stale local branches**: 2nd consecutive cycle. Previous cycle noted SAF-038/039/042 + FIX-064. This cycle: same SAF-038/039/042 + now DOC-012/013/014/015 added. `finalize_wp.py` does not appear to be deleting local branches reliably. **(C) Action tracker not updated between cycles**: Proposed actions from 2026-03-24 were never entered into `action-tracker.json`. This is a protocol gap — the protocol requires adding actions to the tracker but has no enforcement step. |
| 11 | Automated Validation | Pass | `scripts/validate_workspace.py --full` returned **"All checks passed."** No violations detected by the automated script. |

---

## Detailed Findings

### Check 0 — Action Tracker Review (FAIL)

The 2026-03-24 maintenance log proposed **7 actions** — none were added to `action-tracker.json`:

| Proposed Action from 2026-03-24 Log | Status |
|--------------------------------------|--------|
| Create missing US-033–039 (Critical) | Resolved ✓ (US-033–051 now in user-stories.csv) |
| Close BUG-093/094/095 (Warning) | Resolved ✓ (all now Closed) |
| Delete orphaned .finalization-state.json files (Warning) | Resolved ✓ (no files found) |
| Add 13 missing WP back-references (Warning) | Resolved ✓ (all 13 corrected) |
| Accept XFail or recode TST-1580 (Warning) | **Not resolved** — TST-1580 still XFail |
| Post-finalization sanity check in agent-workflow.md (Info) | Status unknown |
| Tester checklist: check Fixed bugs → Closed (Info) | Status unknown (but pattern recurs) |

None of these were added as ACT-012 through ACT-018 to `action-tracker.json`.

---

### Check 1 — Git Hygiene (FAIL)

**Dirty working tree — uncommitted changes:**

| File | Change | Nature |
|------|--------|--------|
| `docs/workpackages/workpackages.csv` | +197 rows replacing 181 (+16 net) | CSV requoting + 16 new Open WPs (DOC-016–028, GUI-023, FIX-071, DOC-017) |
| `docs/user-stories/user-stories.csv` | +104 lines diff | Status cascade US-035–039 → Done + US-040–051 additions |
| `scripts/_add_stories_batch.py` | Deleted | One-time batch helper — obsolete after use |
| `scripts/_add_wps_batch.py` | Modified | Batch helper updates |

**Stale local branches for Done WPs:**

| Branch | WP Status | Age |
|--------|-----------|-----|
| `SAF-038/memory-create-directory` | Done | ~10 hours |
| `SAF-039/lsp-tools-project-scope` | Done | ~9 hours |
| `SAF-042/git-allowlist-expand` | Done | ~3 days |
| `DOC-012/mcp-research` | Done | ~26 min (just merged) |
| `DOC-013/multi-agent-research` | Done | ~20 min (just merged) |
| `DOC-014/audit-logging-research` | Done | ~14 min (just merged) |
| `DOC-015/agent-id-research` | Done | ~9 min (just merged) |

Per non-negotiable rules: *"After merging a feature branch, delete it immediately."*

---

### Check 3 — CSV Integrity (WARNING)

**BUG-097 — Status "Fixed" not "Closed":**
- Bug: `SAF-039: percent-encoded path traversal bypasses zone check in LSP tool URIs`
- `Fixed In WP` = SAF-039, which has Status = `Done`
- Per `bug-tracking-rules.md`, status should be `Closed`

**BUG-102 — Open with no WP assigned:**
- Bug: `file_search allows relative .git/ queries not in search.exclude`
- Severity: Low
- No `Fixed In WP` field — needs a WP assignment or explicit deferral

**TST-1580 XFail status (persists from 2026-03-24):**
- `validate_workspace.py` does not recognise `XFail` as a valid test status
- Either add `XFail` to the validator enum or recode this entry as `Skipped`

---

### Check 8 — Bug Tracking (WARNING)

Confirmed instances:
- BUG-097: Status=`Fixed`, Fixed In WP=SAF-039 (Done) → should be `Closed`
- BUG-102: Status=`Open`, no WP → open defect without owner

---

### Check 10 — Recurring Issue Tracking (WARNING)

**(A) Bug lifecycle stuck at "Fixed" after WP Done — 4th consecutive cycle**

| Cycle | Bugs affected | Resolved? |
|-------|--------------|-----------|
| 2026-03-11 | BUG-026 | ✓ |
| 2026-03-20b | BUG-088/089/090 (ACT-003) | ✓ |
| 2026-03-24 | BUG-093/094/095 | ✓ |
| 2026-03-25 (this) | BUG-097 | ✗ — still Fixed |

**Root cause analysis**: FIX-066 added auto-cascade in `finalize_wp.py` that scans dev-log and test-report for bug refs. But BUG-097 was referenced in tests (not necessarily in the dev-log/test-report body scan). The cascade does not run retroactively after finalization.

**Proposed rule addition:** Add a mandatory step to the Tester post-finalization checklist: *"Search `bugs.csv` for any entry with `Fixed In WP` = this WP and Status = `Fixed`. Set Status to `Closed`."*

**(B) Stale local branches after merge — 2nd consecutive cycle**

The previous cycle (2026-03-24) noted SAF-038/039/042/FIX-064 as pre-created local branches pointing to HEAD. This cycle: SAF-038/039/042 still present (not deleted) + 4 new ones (DOC-012–015) immediately after merge.

`finalize_wp.py` contains branch deletion logic (from FIX-068) but it appears agents are not running finalize_wp.py consistently, or the local branch deletion step is failing silently.

**Proposed rule addition:** Add step to `agent-workflow.md` Developer Post-Merge checklist: *"Verify local branch is deleted: `git branch -d <branch>`. If finalize_wp.py did not delete it, delete manually."*

**(C) Action tracker not updated between cycles — new recurring pattern**

The 2026-03-24 log proposed 7 actions. None were entered into `action-tracker.json`. The protocol says to review the action tracker at the start of each cycle (Check 0) but does not explicitly require writing new entries after each cycle closes.

**Proposed rule addition:** Add to `maintenance-protocol.md` Output section: *"After writing the maintenance log, add all Proposed Actions to `action-tracker.json` as new ACT-NNN entries with status=`Open`."*

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Warning | Commit the dirty working tree: `git add -A; git commit` with message covering CSV requoting + Phase 3 WP additions + US cascades. Verify diff before committing. | `docs/workpackages/workpackages.csv`, `docs/user-stories/user-stories.csv`, `scripts/_add_stories_batch.py`, `scripts/_add_wps_batch.py` |
| Warning | Delete 7 stale local branches: `git branch -d SAF-038/memory-create-directory SAF-039/lsp-tools-project-scope SAF-042/git-allowlist-expand DOC-012/mcp-research DOC-013/multi-agent-research DOC-014/audit-logging-research DOC-015/agent-id-research` | Local git repository |
| Warning | Add proposed actions from 2026-03-24 maintenance log to `action-tracker.json` as ACT-012 through ACT-018 (or subset for those still unresolved). | `docs/maintenance/action-tracker.json` |
| Warning | Close BUG-097: set `Status` = `Closed` in `docs/bugs/bugs.csv`. Fixing WP SAF-039 is Done. | `docs/bugs/bugs.csv` |
| Warning | Assign BUG-102 to a WP or formally mark as deferred/accepted-risk with a comment. Bug: `file_search allows relative .git/ queries not in search.exclude` (Low severity). | `docs/bugs/bugs.csv` |
| Warning | Add to `maintenance-protocol.md` Output section: after writing the log, add all proposed actions to `action-tracker.json` as new ACT-NNN entries. | `docs/work-rules/maintenance-protocol.md` |
| Info | Add to `agent-workflow.md` Tester post-finalization checklist: "Search `bugs.csv` for Fixed entries referencing this WP and set Status to Closed." Addresses recurring 4-cycle bug lifecycle pattern. | `docs/work-rules/agent-workflow.md` |
| Info | Add to `agent-workflow.md` Developer post-merge checklist: "Verify local branch is deleted (`git branch -d <branch>`). Delete manually if finalize_wp.py did not." Addresses recurring stale-branch pattern. | `docs/work-rules/agent-workflow.md` |
| Info | Update `validate_workspace.py` to accept `XFail` as a valid test status, OR recode TST-1580 as `Skipped`. Persists from 2026-03-24 cycle. | `scripts/validate_workspace.py` or `docs/test-results/test-results.csv` |
| Info | Consider minor update to `docs/architecture.md` to mention SAF-036/037 counter configuration and reset features added in v3.2. | `docs/architecture.md` |

---

## Status
**Awaiting human review** — Do NOT implement any changes until approved.