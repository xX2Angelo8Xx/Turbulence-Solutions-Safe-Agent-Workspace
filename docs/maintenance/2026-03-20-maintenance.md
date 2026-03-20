# Maintenance Log — 2026-03-20

**Performed by:** Maintenance Agent (GitHub Copilot)

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Git Hygiene | Warning | 3 merged branches not deleted: `origin/copilot/fix-test-failure-issues`, `origin/copilot/hotfix-v3-0-1-bundled-python-runtime`, and local `main-QuantenComputer`; all have 0 unmerged commits but persist in the repo. Branch naming convention (`<WP-ID>/<short-description>`) not followed. |
| 2 | WP–US Consistency | Pass | All WPs reference a valid US ID or `Enabler`. All US Linked WPs match actual WPs. All US statuses match aggregate WP status. Prior issue (US-013 missing SAF-011) confirmed resolved. |
| 3 | CSV Integrity | Fail | 9 duplicate TST IDs detected in `test-results.csv`: TST-599, TST-1557, TST-1810, TST-1854, TST-1855, TST-1856, TST-1868, TST-1869, TST-1870. Third occurrence of this recurring pattern. No duplicate WP IDs or Bug IDs found. |
| 4 | Documentation Freshness | Pass | `architecture.md` structure matches actual directory layout. `Default-Project/` removal (FIX-046) correctly reflected. `creative-marketing/` reference correct. `work-rules/index.md` lists all 9 rule files. Minor cosmetic: FIX-031–035 entries in architecture.md appear out of order after FIX-042. |
| 5 | WP Folder Integrity | Warning | 3 Done WP folders missing `test-report.md`: FIX-058 (completed today), INS-008 (decomposed WP — sub-WPs have reports), MNT-001 (maintenance WP). All WP folders have `dev-log.md`. |
| 6 | Orphan Detection | Pass | All `docs/workpackages/` folders correspond to valid WP IDs in workpackages.csv. `tests/shared/` is a utility folder, not an orphan. No obvious dead code detected. |
| 7 | Test Coverage Gaps | Warning | 4 Done WPs without `tests/<WP-ID>/` folder: FIX-043 (fix test expected value — trivial), SAF-027 (write tests for python -c scanning — potentially significant, tests may reside in SAF-026). Historical gaps FIX-001–005, FIX-024, FIX-025, FIX-027 (investigation WPs) and INS-008 (decomposed WP) remain. `docs/workpackages/` folders also missing for FIX-023–027. |
| 8 | Bug Tracking | Warning | BUG-085 has status `Open` but `Fixed In WP = FIX-055` which is `Done` (Tester PASS confirmed). Should be Closed. BUG-078, BUG-079, BUG-080, BUG-084 correctly Open with assigned WPs (FIX-051–054). All mandatory fields filled. |
| 9 | Structural Integrity | Warning | `copilot-instructions.md` is ~40 lines without detailed process rules ✓. All 10 agent files (5 standard + 5 CLOUD-) have valid YAML frontmatter ✓. Maintenance protocol check 9 references `Default-Project/` template (removed in FIX-046) — protocol text is stale. |
| 10 | Recurring Issue Tracking | Fail | (A) Duplicate TST IDs: 3rd occurrence — BUG-009 (2026-03-11), BUG-035 (2026-03-13), now 9 new duplicates. FIX-009 and FIX-049 addressed symptoms but no prevention rule was added to testing-protocol.md. (B) Stale undeleted branches: recurring — origin/fix/FIX-007 (2026-03-14), now 3 more. (C) 2026-03-19 maintenance log file exists but is empty — incomplete maintenance cycle, no prior findings to cross-reference. (D) Test coverage gaps for FIX-001–005 still unresolved from 2026-03-14 log. |

---

## Detailed Findings

### Check 1 — Git Hygiene (WARNING)

Working tree is clean; `HEAD` is at `v3.0.3` (latest tag). All Done WPs are committed and pushed to `origin/main`.

**Undeleted merged branches (3):**
- `origin/copilot/fix-test-failure-issues` — 0 unique commits vs. `main`, last commit 2026-03-19. Not following `<WP-ID>/<short-description>` convention.
- `origin/copilot/hotfix-v3-0-1-bundled-python-runtime` — 0 unique commits vs. `main`, last commit 2026-03-19. Not following convention.
- `main-QuantenComputer` (local) — 0 unique commits vs. `main`, last commit 2026-03-19. Should have been deleted after merge.

None are >30 days old so they are not "stale" by the protocol definition, but they violate the "delete immediately after merge" rule.

---

### Check 2 — WP–US Consistency (PASS)

All 117 workpackages reference a valid User Story ID or `Enabler`. US-013 Linked WPs now correctly includes both `SAF-008` and `SAF-011` — prior 2026-03-14 finding confirmed resolved.

Open Enabler WPs (FIX-051–054) are not linked to user stories — correct.

---

### Check 3 — CSV Integrity (FAIL)

**`test-results.csv` has 9 duplicate TST IDs (1,784 data rows):**

| Duplicate ID | Count |
|---|---|
| TST-599 | 2 |
| TST-1557 | 2 |
| TST-1810 | 2 |
| TST-1854 | 2 |
| TST-1855 | 2 |
| TST-1856 | 2 |
| TST-1868 | 2 |
| TST-1869 | 2 |
| TST-1870 | 2 |

`workpackages.csv`, `user-stories.csv`, and `bugs.csv`: no duplicate IDs, valid enum values, all required fields populated.

---

### Check 4 — Documentation Freshness (PASS)

`architecture.md` accurately reflects the current directory layout. `Default-Project/` removal, `creative-marketing/` path, `templates/coding/` as sole shipping template, and the `src/installer/shims/` directory are all correctly documented.

**Minor cosmetic issue:** Within the `tests/` directory listing in `architecture.md`, entries FIX-031 through FIX-035 appear after FIX-042 (out of numeric order). Does not affect usability but is inconsistent.

`work-rules/index.md` correctly lists all 9 rule files (agent-workflow.md, bug-tracking-rules.md, coding-standards.md, commit-branch-rules.md, index.md, maintenance-protocol.md, security-rules.md, testing-protocol.md, workpackage-rules.md).

---

### Check 5 — WP Folder Integrity (WARNING)

All WP folders contain `dev-log.md` ✓

**Missing `test-report.md` in Done WP folders (3):**
- `docs/workpackages/FIX-058/` — completed 2026-03-20 (today); fresh Done, likely oversight.
- `docs/workpackages/INS-008/` — decomposed WP; work tracked through sub-WPs INS-013–INS-017.
- `docs/workpackages/MNT-001/` — maintenance sweep WP; arguably a test-report.md is not meaningful here.

---

### Check 6 — Orphan Detection (PASS)

All 103 folders under `docs/workpackages/` correspond to valid workpackage IDs. No orphan folders.

Note: Done WPs FIX-023, FIX-024, FIX-025, FIX-026, FIX-027 have no `docs/workpackages/<WP-ID>/` folders (investigation WPs that required no code changes and were not given WP folders). This is not an orphan situation but a documentation gap for those WPs.

---

### Check 7 — Test Coverage Gaps (WARNING)

**Done WPs without `tests/<WP-ID>/` folder:**

| WP ID | Status | Reason |
|-------|--------|--------|
| FIX-001–005 | Done | Historical — pre-dates test folder enforcement; no code to test |
| FIX-024, FIX-025, FIX-027 | Done | Investigation WPs — resolved with no code changes |
| FIX-043 | Done | Fixed a single test assertion in INS-005; trivial change |
| INS-008 | Done | Decomposed WP — tested via INS-013–017 |
| SAF-027 | Done | **Significant:** SAF-027 = "Write tests for `_scan_python_inline_code`". No `tests/SAF-027/` folder exists. Tests may have been placed inside `tests/SAF-026/` rather than a dedicated SAF-027 folder. Requires verification. |

---

### Check 8 — Bug Tracking (WARNING)

**BUG-085 should be Closed:**
`BUG-085` ("FIX-055 re-introduces ArchitecturesAllowed") has Status = `Open` but `Fixed In WP = FIX-055`. FIX-055 is `Done` with Tester PASS confirmed (marker in workpackages.csv). The bug was resolved as part of FIX-055 Iteration 2 which updated the stale tests. The `Open` status is a data entry oversight.

Currently Open bugs correctly referencing assigned WPs:
- BUG-078 → FIX-051
- BUG-079 → FIX-052
- BUG-080 → FIX-053
- BUG-084 → FIX-054

---

### Check 9 — Structural Integrity (WARNING)

**`copilot-instructions.md`:** ~40 lines, no detailed process rules embedded. ✓

**Agent files:** All 10 files in `.github/agents/` are syntactically valid with YAML frontmatter (`---`). ✓

**Stale protocol reference:** `maintenance-protocol.md` Check 9 reads: "Is the `Default-Project/` template unmodified (no accidental test changes)?" `Default-Project/` was removed by FIX-046 (v3.0.0). This check item needs to be updated to reference `templates/coding/` instead.

---

### Check 10 — Recurring Issue Tracking (FAIL)

#### (A) Duplicate TST IDs — 3rd Recurrence

| Occurrence | Date | Reported As | Fixed By |
|---|---|---|---|
| 1st | 2026-03-11 | BUG-009 | Maintenance sweep |
| 2nd | 2026-03-13 | BUG-035 | FIX-009 |
| 3rd | 2026-03-20 | This log | TBD |

Root cause: `testing-protocol.md` has no rule specifying how to determine and assign the next TST-ID. Agents independently add rows using the same TST-IDs without checking for existing maximum. **Proposed rule change:** Add a mandatory TST-ID lookup step to `testing-protocol.md`: before adding any test result row, agents must find the current maximum TST-ID in the file and increment from there.

#### (B) Stale Undeleted Branches — Recurring

2026-03-14 found `origin/fix/FIX-007` undeleted. Today 3 more undeleted merged branches found. The rule "delete immediately after merge" exists in `copilot-instructions.md` but is not being enforced. **Proposed rule change:** Add a mandatory branch-deletion verification step to the workpackage completion checklist in `workpackage-rules.md`.

#### (C) Empty 2026-03-19 Maintenance Log

`docs/maintenance/2026-03-19-maintenance.md` exists but is completely empty. No prior maintenance findings available to cross-reference from yesterday. **Proposed action:** The 2026-03-20 maintenance log (this document) replaces the 2026-03-19 as the current reference baseline.

#### (D) Historical Test Coverage Gaps Persist

FIX-001–005 test coverage gaps were identified in the 2026-03-14 maintenance log. No corrective action was taken across two maintenance cycles. These are low-priority (historical/human-implemented WPs) but the persistence indicates no one is tracking whether maintenance-proposed actions get implemented.

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Critical | Add mandatory TST-ID lookup rule to `testing-protocol.md`: before adding test rows, find current max TST-ID and increment. Resolves 3rd occurrence of duplicate TST-IDs. | `docs/work-rules/testing-protocol.md` |
| Critical | Close BUG-085 in `bugs.csv` — FIX-055 is Done with Tester PASS; bug is resolved. | `docs/bugs/bugs.csv` |
| Warning | Delete merged branches: `origin/copilot/fix-test-failure-issues`, `origin/copilot/hotfix-v3-0-1-bundled-python-runtime`, and local `main-QuantenComputer`. | Git repository |
| Warning | Add branch-deletion verification step to workpackage completion checklist in `workpackage-rules.md` to prevent recurrence. | `docs/work-rules/workpackage-rules.md` |
| Warning | Create `test-report.md` in `docs/workpackages/FIX-058/`. | `docs/workpackages/FIX-058/test-report.md` |
| Warning | Verify whether SAF-027 tests exist inside `tests/SAF-026/`. If so, move them to `tests/SAF-027/` and update architecture.md. If not, create the missing test suite. | `tests/SAF-027/`, `docs/architecture.md` |
| Warning | Update `maintenance-protocol.md` Check 9 to replace `Default-Project/` reference with `templates/coding/`. | `docs/work-rules/maintenance-protocol.md` |
| Warning | Deduplicate 9 duplicate TST IDs in `test-results.csv` (TST-599, TST-1557, TST-1810, TST-1854–1856, TST-1868–1870). | `docs/test-results/test-results.csv` |
| Info | Fix cosmetic ordering of FIX-031–035 entries in `architecture.md` tests/ listing (currently appear after FIX-042). | `docs/architecture.md` |
| Info | Create `tests/SAF-027/` organisational note or stub if tests were merged into SAF-026 (after verification above). | `tests/SAF-027/`, `docs/architecture.md` |
| Info | Create `docs/workpackages/` folders for FIX-023–027 (Done investigation WPs currently missing WP folders). | `docs/workpackages/FIX-023/` through `docs/workpackages/FIX-027/` |

---

## Status
**Awaiting human review** — Do NOT implement any changes until approved.
