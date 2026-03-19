# Maintenance Log — 2026-03-14

**Performed by:** Maintenance Agent (GitHub Copilot)

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Git Hygiene | Warning | Stale merged remote branch `origin/fix/FIX-007` not deleted after merge; all committed work otherwise clean |
| 2 | WP–US Consistency | Warning | US-013 Linked WPs column omits SAF-011, which references US-013; all other WP↔US references consistent |
| 3 | CSV Integrity | Fail | ~100 duplicate TST IDs in `test-results.csv` across 6 collision ranges (TST-261–301, TST-481–511, TST-522–544, TST-578–582, TST-718, TST-782) |
| 4 | Documentation Freshness | Warning | `docs/architecture.md` templates diagram shows `creative/` but actual directory is `templates/creative-marketing/` |
| 5 | WP Folder Integrity | Fail | FIX-001–FIX-007 WP folders all lack `test-report.md`; INS-008 (decomposed Done WP) has no WP folder at all |
| 6 | Orphan Detection | Pass | No orphan WP folders; Default-Project/Project/ contains only expected template files; no obvious dead code |
| 7 | Test Coverage Gaps | Fail | FIX-003, FIX-004, FIX-005 are Done with test results logged but no `tests/<WP-ID>/` directory; FIX-001, FIX-002 have no test dir or test results; FIX-006, FIX-007 have test dirs but no dedicated CSV entries |
| 8 | Bug Tracking | Pass | All 24 bugs are Closed with assigned WPs and filled required fields |
| 9 | Structural Integrity | Pass | `copilot-instructions.md` is 33 lines (< 40 limit); all 5 agent files have valid YAML frontmatter; `Default-Project/` unmodified |

---

## Detailed Findings

### Check 1 — Git Hygiene (WARNING)

Working tree is clean (no uncommitted changes). HEAD is at the latest commit on `main` (`931a2a3`). All completed workpackages are committed and pushed.

**Stale merged remote branch:** `origin/fix/FIX-007` was branched for FIX-007 implementation, merged into `main` (confirmed via `git branch -r --merged main`), and its last commit is dated 2026-03-13. Per the repo rule *"After merging a feature branch, delete it immediately — both locally and remotely"*, this branch should have been deleted but was not.

---

### Check 2 — WP–US Consistency (WARNING)

All 48 workpackages reference either a valid User Story ID (e.g., US-009) or `Enabler`. No dangling or invalid US references found.

All user story statuses are consistent with their linked WPs — every US in `Done` status has all linked WPs in `Done` status.

**Discrepancy:** SAF-011 references `US-013` in the `User Story` column, but `user-stories.csv` row for US-013 lists `Linked WPs = SAF-008` only. SAF-011 is missing from US-013's `Linked WPs`.

---

### Check 3 — CSV Integrity (FAIL)

`workpackages.csv`, `user-stories.csv`, and `bugs.csv` have no duplicate IDs, valid status values, and all required fields filled.

**`test-results.csv` — duplicate TST IDs (new occurrence of BUG-009 pattern):** A PowerShell scan of every row's TST ID prefix found the following groups of duplicated IDs:

| Duplicate Range | Count | Pattern |
|-----------------|-------|---------|
| TST-261 – TST-301 | 41 IDs each duplicated | Multiple WPs assigned overlapping ID ranges |
| TST-481 – TST-511 | 31 IDs each duplicated | Multiple WPs assigned overlapping ID ranges |
| TST-522 – TST-544 | 23 IDs each duplicated | Multiple WPs assigned overlapping ID ranges |
| TST-578 – TST-582 | 5 IDs each duplicated | Multiple WPs assigned overlapping ID ranges |
| TST-718 | 1 ID duplicated | Single collision |
| TST-782 | 1 ID duplicated | INS-017 dev entry reused same ID as INS-016 Tester PASS entry |

This is a recurrence of BUG-009 (previously resolved for TST-125–TST-165 during the 2026-03-11 maintenance). New duplicates were introduced during workpackages implemented after that fix.

---

### Check 4 — Documentation Freshness (WARNING)

`docs/work-rules/index.md` correctly lists all 9 rule files, all of which exist on disk. No dead links found.

All file paths referenced in documentation verified as valid.

**Stale reference:** `docs/architecture.md` templates architecture diagram shows:
```
└── creative/        ← Future: marketing/creative template
```
The actual directory on disk is `templates/creative-marketing/`. The folder name does not match.

---

### Check 5 — WP Folder Integrity (FAIL)

All 47 WP folders that exist contain a `dev-log.md`. ✓

**Missing `test-report.md` (7 Done WP folders):**

| WP | Status | test-report.md |
|----|--------|----------------|
| FIX-001 | Done | ✗ Missing |
| FIX-002 | Done | ✗ Missing |
| FIX-003 | Done | ✗ Missing |
| FIX-004 | Done | ✗ Missing |
| FIX-005 | Done | ✗ Missing |
| FIX-006 | Done | ✗ Missing |
| FIX-007 | Done | ✗ Missing |

FIX-008 is the only FIX workpackage with a `test-report.md`.

**Missing WP folder — INS-008 (Done, decomposed):** INS-008 ("CI/CD Pipeline") is in `Done` status in `workpackages.csv` but has no `docs/workpackages/INS-008/` folder. The WP comments note it was "Decomposed into sub-workpackages INS-013 through INS-017 — all Done." The sub-workpackages each have their own folders and test-report.md files.

---

### Check 6 — Orphan Detection (PASS)

No WP folders found in `docs/workpackages/` without a matching entry in `workpackages.csv`. ✓

`Default-Project/Project/` contains only: `app.py`, `README.md`, `requirements.txt` — expected template starter files, none modified for testing. ✓

No obviously unreferenced source files or dead code identified via structural scan. ✓

---

### Check 7 — Test Coverage Gaps (FAIL)

| WP | Done? | tests/<WP-ID>/ | Test Results in CSV | Assessment |
|----|-------|----------------|---------------------|------------|
| FIX-001 | Yes (human) | ✗ Missing | ✗ None | Warning — human fix, no test process |
| FIX-002 | Yes (human) | ✗ Missing | ✗ None | Warning — human fix, no test process |
| FIX-003 | Yes | ✗ Missing | ✓ TST-600, TST-603 | Fail — test dir absent |
| FIX-004 | Yes | ✗ Missing | ✓ TST-598, TST-602 | Fail — test dir absent |
| FIX-005 | Yes | ✗ Missing | ✓ TST-599, TST-601 | Fail — test dir absent |
| FIX-006 | Yes | ✓ Exists | ✗ No dedicated entries | Warning — tests run but not individually logged |
| FIX-007 | Yes | ✓ Exists | ✗ No dedicated entries | Warning — tests run but not individually logged |
| INS-008 | Yes (decomposed) | ✗ Missing | ✗ None | Info — decomposed; sub-WPs cover all deliverables |
| All other Done WPs | Yes | ✓ Exists | ✓ Present | Pass |

FIX-003, FIX-004, FIX-005 were agent-implemented workpackages whose tests were run as part of the WP they fixed (e.g., FIX-004 tests run against INS-006 test suite). No permanent `tests/FIX-003/`, `tests/FIX-004/`, `tests/FIX-005/` directories were created to house dedicated test files as permanent artifacts.

---

### Check 8 — Bug Tracking (PASS)

All 24 bugs in `docs/bugs/bugs.csv` are in `Closed` status. Every bug has a `Fixed In WP` value assigned. All required fields (ID, Title, Status, Severity, Reported By, Description, Fixed In WP) are populated for every entry. ✓

---

### Check 9 — Structural Integrity (PASS)

- `copilot-instructions.md`: **33 lines** — within the 40-line limit. ✓
- Agent files in `.github/agents/` (5 files): All present with valid YAML frontmatter (`---` delimiters, `description`, `tools`, `model` fields). ✓
- `Default-Project/`: Git diff clean; no test-related modifications detected. Template files intact. ✓

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Warning | Delete stale merged remote branch: `git push origin --delete fix/FIX-007` | Remote refs |
| Warning | Renumber duplicate TST IDs in `test-results.csv` to restore unique IDs across all ~100 collision entries (recurrence of BUG-009 pattern — log a new bug and assign a fix workpackage) | `docs/test-results/test-results.csv` |
| Warning | Create `test-report.md` for FIX-001, FIX-002, FIX-003, FIX-004, FIX-005, FIX-006, FIX-007 WP folders (retroactive Tester sign-off) | `docs/workpackages/FIX-001/` through `docs/workpackages/FIX-007/` |
| Warning | Create permanent test directories `tests/FIX-003/`, `tests/FIX-004/`, `tests/FIX-005/` with at least one test file each (or formally document exemption) | `tests/` |
| Warning | Add dedicated test result CSV entries for FIX-006 and FIX-007 (WP Reference column) referencing the tests in their test directories | `docs/test-results/test-results.csv` |
| Info | Update US-013 `Linked WPs` column to include SAF-011 | `docs/user-stories/user-stories.csv` |
| Info | Update `docs/architecture.md` templates diagram: change `creative/` to `creative-marketing/` | `docs/architecture.md` |
| Info | Create `docs/workpackages/INS-008/dev-log.md` noting decomposition (no direct implementation; sub-WPs INS-013–INS-017 cover all deliverables) — or formally document that decomposed WPs are exempt from folder requirements in the workpackage rules | `docs/workpackages/INS-008/` or `docs/work-rules/workpackage-rules.md` |
| Info | Clarify in testing-protocol.md whether human-implemented FIX WPs (FIX-001, FIX-002) are exempt from test directory and CSV logging requirements; if not exempt, create test artifacts retroactively | `docs/work-rules/testing-protocol.md`, `tests/FIX-001/`, `tests/FIX-002/` |

---

## Status

**Awaiting human review** — Do NOT implement any changes until approved.
