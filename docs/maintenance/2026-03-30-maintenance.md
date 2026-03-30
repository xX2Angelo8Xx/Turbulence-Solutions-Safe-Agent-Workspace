# Maintenance Log — 2026-03-30

**Performed by:** Maintenance Agent (GitHub Copilot)

---

## Check 0 — Action Tracker Review

All 28 actions (ACT-001 through ACT-028) in `docs/maintenance/action-tracker.json` have status `Done`. No Open actions remain from previous cycles.

**Result: Pass**

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 0 | Action Tracker Review | Pass | All 28 actions Done; no Open actions outstanding |
| 1 | Git Hygiene | Warning | Uncommitted deletion of `FIX-080/.finalization-state.json` in working tree |
| 2 | WP–US Consistency | Pass | 13 Open WPs correctly linked to 5 Open User Stories; all Done WPs have valid US or Enabler reference |
| 3 | CSV Integrity | Warning | 21 bugs stuck in `Fixed` status with `Fixed In WP` set — cascade to `Closed` not triggered |
| 4 | Documentation Freshness | Pass | `docs/work-rules/index.md` lists all 10 rule files; directory structure unchanged since last cycle |
| 5 | WP Folder Integrity | Pass | All 223 Done WPs have folders and dev-logs; 2 missing test-reports (INS-008, MNT-001) are registered exceptions |
| 6 | Orphan Detection | Warning | 11 orphaned `.finalization-state.json` files in Done WP folders; FIX-080 deletion uncommitted |
| 7 | Test Coverage Gaps | Pass | INS-008 has no test folder (registered exception); 0 duplicate TST-IDs across 2,162 entries |
| 8 | Bug Tracking | Warning | 21 bugs in `Fixed` status need to be closed; BUG-102 Open/deferred with no WP (explicitly accepted) |
| 9 | Structural Integrity | Pass | `copilot-instructions.md` is exactly 40 lines; agent YAML frontmatter correct since FIX-073 |
| 10 | Recurring Issue Tracking | Warning | Orphaned state files: 4th consecutive cycle with this finding; bug auto-cascade also recurs |
| 11 | Automated Validation | Pass | `validate_workspace.py --full` reports 11 warnings (all orphaned state files), 0 errors |

---

## Detailed Findings

### Check 1 — Git Hygiene

- **Working tree dirty**: `D docs/workpackages/FIX-080/.finalization-state.json` is deleted locally but not committed. This is likely a leftover from the FIX-080 finalisation step.
- **Branches**: Only `main` exists locally and remotely (`origin/main`). No stale or undeleted feature branches.
- **Latest tag**: `v3.2.4` on HEAD (commit `8dc016e`). All Done WPs appear committed.

### Check 2 — WP–US Consistency

Open workpackages (13) and their user stories are correctly linked:
- **US-040** (Windows Code Signing): DOC-016 Done, INS-024 and INS-025 Open
- **US-056** (Workspace Health Dashboard): GUI-024, GUI-025, GUI-026 Open
- **US-057** (Session Statistics Data Layer): SAF-053, SAF-054 Open
- **US-058** (Real-Time Dashboard Statistics): GUI-027, GUI-028, GUI-029, GUI-030 Open
- **US-059** (Session Block Management): GUI-031, GUI-032 Open

No missing back-references or status mismatches detected.

### Check 3 — CSV Integrity

- **test-results.csv**: 2,162 entries; **0 duplicate TST-IDs** — clean.
- **bugs.csv**: 141 entries; status breakdown: 119 Closed, 21 Fixed, 1 Open.
  - **WARNING**: 21 bugs in `Fixed` status. All have `Fixed In WP` populated. The `finalize_wp.py` cascade should have set these to `Closed` when their respective WPs were finalised. They have not been progressed.
- **workpackages.csv**: 236 entries, all parseable with UTF-8-sig encoding.
- **user-stories.csv**: Parseable; 5 Open stories consistent with pipeline state.

### Check 5 — WP Folder Integrity

- All 223 Done WPs have `docs/workpackages/<WP-ID>/` folder and `dev-log.md`.
- **2 missing test-report.md**: INS-008 and MNT-001. Both are registered in `docs/workpackages/validation-exceptions.json` as known exemptions. No action required.

### Check 6 — Orphan Detection

**11 orphaned `.finalization-state.json` files** found in Done WP folders:
- DOC-016, DOC-019, DOC-028
- FIX-071, FIX-075
- INS-029
- SAF-049, SAF-051, SAF-055, SAF-059, SAF-061

Additionally, `docs/workpackages/FIX-080/.finalization-state.json` has been deleted in the working tree but the deletion is unstaged/uncommitted.

No orphaned WP folders (folders without a corresponding CSV entry) were found.

### Check 7 — Test Coverage Gaps

- **INS-008** has no `tests/INS-008/` folder and no test results. This WP was decomposed into INS-013 through INS-017; registered exception.
- All other 222 Done WPs have test results.
- TST-ID uniqueness: **0 duplicates** (previously a recurring issue; now clean).

### Check 8 — Bug Tracking

**21 bugs in `Fixed` status** (awaiting cascade to `Closed`):

| Bug ID | Fixed In WP | Short Title |
|--------|------------|-------------|
| BUG-111 | SAF-046 | Workspace root access blocked |
| BUG-113 | SAF-048 | Memory tool blanket-blocked |
| BUG-114 | SAF-049 | Search tool docs vs enforcement mismatch |
| BUG-115 | SAF-050 | grep_search surfaces denied content |
| BUG-117 | FIX-075 | Launcher window title incorrect |
| BUG-119 | FIX-076 | Reset Agent Blocks button missing |
| BUG-135 | SAF-057 | .git directory selected as project folder |
| BUG-136 | SAF-058 | get_changed_files bypasses zone enforcement |
| BUG-137 | SAF-060 | Memory tool still blocked |
| BUG-138 | SAF-055 | Copilot instructions waste Block 1 |
| BUG-139 | SAF-055 | Skill files inaccessible |
| BUG-140 | SAF-059 | Remove-Item blocked but del alias allowed |
| BUG-141 | SAF-059 | dir -Name blocked (false positive) |
| BUG-142 | SAF-059 | Parenthesized subexpressions blocked |
| BUG-143 | SAF-059 | Test-Path not in terminal allowlist |
| BUG-144 | SAF-061 | Parallel denial batching non-deterministic |
| BUG-145 | SAF-056 | No .venv despite AGENT-RULES reference |
| BUG-146 | FIX-079 | NoAgentZone hidden from VS Code explorer |
| BUG-147 | INS-026 | macOS launcher SIGKILL crash |
| BUG-148 | INS-026 | macOS code signature corrupted after copy |
| BUG-149 | INS-026 | macOS Gatekeeper blocks app |

**BUG-102 (Open, Low)**: `file_search allows relative .git/ queries` — explicitly deferred per comment: "Low risk; .git/ excluded by VS Code default settings. Will address if elevated." No action needed.

### Check 9 — Structural Integrity

- `copilot-instructions.md`: Exactly **40 lines** — at the limit and compliant.
- Agent files in `.github/agents/`: Updated via FIX-073 with correct VS Code tool categories and model syntax.
- `templates/agent-workbench/`: No test modifications since last verified cycle.
- All scripts in `scripts/` are syntactically valid (validate_workspace.py runs successfully).

### Check 10 — Recurring Issue Tracking

**Recurring: Orphaned `.finalization-state.json` files** (4th consecutive cycle)
- Found in every maintenance cycle since MNT-001 (2026-03-19), 2026-03-24, 2026-03-25, and now 2026-03-30.
- FIX-068 was created to automate cleanup at finalization. It verifies branch deletion and deletes the state file as the final step. Yet files persist across multiple WPs.
- **Proposed rule change**: Verify that `finalize_wp.py` Step 10 (delete state file) is actually executing. Add explicit step to `agent-workflow.md` Developer checklist: "After `finalize_wp.py` completes, confirm `docs/workpackages/<WP-ID>/.finalization-state.json` does not exist." If the file exists, manually delete it.

**Recurring: Bugs stuck in `Fixed` status** (3rd cycle)
- Previous cycles (2026-03-20b, 2026-03-24) had similar findings. ACT-007 and ACT-018 added closure rules to documentation, but the cascade is still not reliably working.
- **Proposed rule change**: The Tester agent, as part of the WP finalisation handoff, should manually set all referenced bugs from `Fixed` to `Closed` in `docs/bugs/bugs.csv` using `scripts/_repair_csvs.py` or direct CSV edit. Do not rely solely on the `finalize_wp.py` auto-cascade.

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Warning | Commit the staged deletion of `FIX-080/.finalization-state.json` | `docs/workpackages/FIX-080/` |
| Warning | Delete 11 orphaned `.finalization-state.json` files: DOC-016, DOC-019, DOC-028, FIX-071, FIX-075, INS-029, SAF-049, SAF-051, SAF-055, SAF-059, SAF-061 | `docs/workpackages/*/` |
| Warning | Progress 21 `Fixed` bugs to `Closed` status: BUG-111, BUG-113, BUG-114, BUG-115, BUG-117, BUG-119, BUG-135, BUG-136, BUG-137, BUG-138, BUG-139, BUG-140, BUG-141, BUG-142, BUG-143, BUG-144, BUG-145, BUG-146, BUG-147, BUG-148, BUG-149 | `docs/bugs/bugs.csv` |
| Info | Investigate why `finalize_wp.py` Step 10 (delete state file) is not reliably executing; add explicit dev-checklist step to `agent-workflow.md` | `scripts/finalize_wp.py`, `docs/work-rules/agent-workflow.md` |
| Info | Add explicit Tester checklist step: manually set all referenced bugs with status `Fixed` to `Closed` during finalisation (do not rely solely on auto-cascade) | `docs/work-rules/agent-workflow.md` |

---

## Action Tracker Update Required

After human review and approval, add the following 5 entries to `docs/maintenance/action-tracker.json` as ACT-029 through ACT-033 with status `Open`:

- **ACT-029**: Commit staged deletion of FIX-080/.finalization-state.json
- **ACT-030**: Delete 11 orphaned .finalization-state.json files (DOC-016, DOC-019, DOC-028, FIX-071, FIX-075, INS-029, SAF-049, SAF-051, SAF-055, SAF-059, SAF-061)
- **ACT-031**: Progress 21 Fixed bugs to Closed (BUG-111 through BUG-149 as listed above)
- **ACT-032**: Investigate and fix finalize_wp.py Step 10 state file deletion
- **ACT-033**: Add Tester checklist step for manual bug closure at finalisation

---

## Status

**All phases complete.**

- Phase 0: Data cleanup — MNT-003 (Done)
- Phase 1: Bug cascade fix — FIX-081 (Done)
- Phase 2: Tooling improvements — FIX-082 (Done)
- Phase 3: Workflow documentation — FIX-083 (Done)
