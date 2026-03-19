# Maintenance Log — 2026-03-13

**Performed by:** Maintenance Agent (GitHub Copilot)

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Git Hygiene | Fail | 11 commits ahead of `main` containing Done WPs never merged; 5 unstaged modified files; 12+ untracked files/folders; 4 local-only branches not pushed to remote |
| 2 | WP–US Consistency | Warning | 6 User Stories whose linked WPs are all Done but the US status is still `Open` (US-003, US-004, US-005, US-006, US-013, US-014, US-015); US-001 and US-002 use status `Closed` — validity of this value needs confirmation against user-story-rules.md |
| 3 | CSV Integrity | Warning | BUG-026 status is `Open` despite its fix being confirmed in GUI-008 Done (Tester PASS Iteration 2); `workpackages.csv` and `test-results.csv` have uncommitted/unstaged changes on disk |
| 4 | Documentation Freshness | Warning | `docs/architecture.md` `tests/` section lists only 19 test subfolders; actual directory contains 33. Missing: GUI-002, GUI-005, GUI-006, GUI-007, GUI-008, GUI-009, GUI-010, INS-005, INS-006, INS-007, INS-010, SAF-004, SAF-008, SAF-009 |
| 5 | WP Folder Integrity | Fail | 4 Done WPs lack `test-report.md` (INS-007, INS-010, GUI-006, GUI-007); `docs/workpackages/SAF-008/` missing `dev-log.md`; folders for GUI-005, GUI-006, INS-010 are untracked (exist on disk, never committed) |
| 6 | Orphan Detection | Warning | Untracked files not yet committed: `src/launcher/core/downloader.py`; `docs/workpackages/GUI-005/`, `docs/workpackages/GUI-006/`, `docs/workpackages/INS-010/`; `tests/GUI-005/`, `tests/GUI-006/`, `tests/INS-010/`; edge-case test files inside GUI-007 and INS-007 test folders |
| 7 | Test Coverage Gaps | Warning | `tests/GUI-005/`, `tests/GUI-006/`, `tests/INS-010/` exist on disk but are untracked — not verifiably committed; test-results.csv has no entries for GUI-005 or GUI-006 (committed file portion); INS-010 test entries not yet staged/committed |
| 8 | Bug Tracking | Warning | BUG-026 is `Open` but GUI-008 is `Done` (Tester PASS) — `Fixed In WP` = GUI-008 already recorded; BUG-027 (update_hashes.py missing) is `Open` with no assigned workpackage for the fix |
| 9 | Structural Integrity | Pass | `copilot-instructions.md` is exactly 40 lines (at the stated limit); all 5 agent files present with valid YAML frontmatter; `Default-Project/` is unmodified (git diff clean) |

---

## Detailed Findings

### Check 1 — Git Hygiene (FAIL)

**Commits ahead of `main` (11 commits, never merged):**
The current branch `GUI-007/input-validation-error-ux` is 11 commits ahead of `main`. These commits contain completed Done workpackages that should have been merged and the feature branches deleted:

| Commit | Content | WP Status |
|--------|---------|-----------|
| a48b662 | GUI-009, GUI-010: Update Notification Banner + Check for Updates | Done |
| be5ba82 | SAF-009: Tester PASS | Done |
| a096201 | INS-006: Tester PASS | Done |
| 700d052 | SAF-009: cross-platform test suite | Done |
| 594a247 | INS-006: macOS DMG build script | Done |
| 50e210b | GUI-008: Version Display Iteration 2 PASS | Done |
| 32f53b6 | SAF-008: Hook file integrity | Done |
| d2115de | INS-005: Inno Setup PASS | Done |
| b491d92 | test(GUI-008): Tester FAIL (historical) | — |
| 9bde07d | GUI-002: project type dropdown PASS | Done |

**Staged but uncommitted changes:**
- `docs/test-results/test-results.csv`
- `docs/workpackages/GUI-007/dev-log.md` (new)
- `docs/workpackages/INS-007/dev-log.md` (new)
- `docs/workpackages/workpackages.csv`
- `src/installer/linux/build_appimage.sh` (new)
- `tests/GUI-007/__init__.py` (new)
- `tests/GUI-007/test_gui007_validation.py` (new)
- `tests/INS-007/__init__.py` (new)
- `tests/INS-007/test_ins007_build_appimage.py` (new)

**Unstaged (modified) files:**
- `docs/bugs/bugs.csv`
- `docs/test-results/test-results.csv`
- `docs/workpackages/workpackages.csv`
- `src/launcher/gui/app.py`
- `tests/conftest.py`

**Untracked files/directories:**
- `docs/workpackages/GUI-005/`
- `docs/workpackages/GUI-006/`
- `docs/workpackages/INS-010/`
- `src/launcher/core/downloader.py`
- `tests/GUI-005/`
- `tests/GUI-006/`
- `tests/GUI-007/test_gui007_edge_cases.py`
- `tests/GUI-007/test_gui007_tester_additions.py`
- `tests/INS-007/test_ins007_edge_cases.py`
- `tests/INS-007/test_ins007_tester.py`
- `tests/INS-007/test_ins007_tester_additions.py`
- `tests/INS-010/`

**Local-only branches not pushed to remote:**
- `GUI-002/project-type-selection`
- `GUI-007/input-validation-error-ux`
- `INS-007/linux-appimage-build-script`
- `SAF-008/hook-file-integrity`

**Stale / should-be-deleted branches (Done WPs, not cleaned up):**
- `GUI-002/project-type-selection` (local only)
- `GUI-005/project-creation-logic` (local + remote)
- `GUI-008/version-display` (local + remote)
- `INS-005/windows-installer` (local + remote)
- `INS-006/macos-dmg-installer` (local + remote)
- `SAF-008/hook-file-integrity` (local only)
- `SAF-009/cross-platform-test-suite` (local + remote)

### Check 2 — WP–US Consistency (WARNING)

**US Status out of sync — all linked WPs are Done but US is still Open:**

| User Story | Current Status | Linked WPs | WP Statuses |
|------------|---------------|------------|-------------|
| US-003 | Open | GUI-002 | Done |
| US-004 | Open | GUI-003, GUI-004, GUI-007 | All Done |
| US-005 | Open | GUI-005 | Done |
| US-006 | Open | GUI-006 | Done |
| US-013 | Open | SAF-008 | Done |
| US-014 | Open | GUI-008 | Done |
| US-015 | Open | GUI-009, GUI-010, INS-009 | All Done |

**US-016** correctly remains `Open` because INS-011 (Update Apply and Restart) is still `Open`.

**Status value `Closed`:** US-001 and US-002 use status `Closed`. This value does not appear in the user-stories.csv for any other story. Valid statuses used elsewhere are `Open` and `Done`. Recommend confirming whether `Closed` is an intentional split/superseded state distinct from `Done`.

### Check 3 — CSV Integrity (WARNING)

- **BUG-026:** Status is `Open`; `Fixed In WP` is `GUI-008`; GUI-008 is `Done` with Tester PASS confirmed. The bug was fixed — status should be updated to `Fixed`/`Closed`.
- **workpackages.csv:** Has both staged and unstaged changes — the on-disk version is ahead of what is committed.
- **test-results.csv:** Has both staged and unstaged changes — entries for recent WPs not yet committed.
- No duplicate IDs detected in the committed portions of all CSVs.
- All WP status values in the committed CSV are either `Open` or `Done` — both valid.

**WPs marked `Done` with comments indicating "Pending human test execution":**

| WP | Status | Comment concern |
|----|--------|----------------|
| GUI-006 | Done | "Pending human test execution" |
| GUI-007 | Done | "Pending human test execution" |
| INS-007 | Done | "Pending human test execution" |
| INS-010 | Done | "Pending human test execution" |

These WPs were marked `Done` before human execution of the test suite was confirmed — potentially a process violation (WPs should only reach `Done` after all tests pass including human execution).

### Check 4 — Documentation Freshness (WARNING)

`docs/architecture.md` `tests/` section is significantly out of date. It lists 19 test subfolders; actual `tests/` directory (on disk) contains 33.

**Missing from `architecture.md` test section:**
GUI-002, GUI-005, GUI-006, GUI-007, GUI-008, GUI-009, GUI-010, INS-005, INS-006, INS-007, INS-010, SAF-004, SAF-008, SAF-009

All other referenced file paths in documentation appear valid. `docs/work-rules/index.md` lists all 9 existing rule files correctly.

### Check 5 — WP Folder Integrity (FAIL)

**Missing `test-report.md` in Done WP folders:**

| WP | Status | dev-log.md | test-report.md |
|----|--------|-----------|----------------|
| INS-007 | Done | Yes (staged) | **Missing** |
| INS-010 | Done | Yes (untracked) | **Missing** |
| GUI-006 | Done | Yes (untracked) | **Missing** |
| GUI-007 | Done | Yes (staged) | **Missing** |

**Missing `dev-log.md`:**

| WP | Status | dev-log.md | test-report.md |
|----|--------|-----------|----------------|
| SAF-008 | Done | **Missing** | Yes |

**Untracked WP folders (exist on disk, not committed):**
- `docs/workpackages/GUI-005/` — untracked
- `docs/workpackages/GUI-006/` — untracked
- `docs/workpackages/INS-010/` — untracked

### Check 6 — Orphan Detection (WARNING)

**Untracked source and test files** (not committed to git):
- `src/launcher/core/downloader.py` — referenced by INS-010, not committed
- `tests/GUI-005/` (entire folder) — not committed
- `tests/GUI-006/` (entire folder) — not committed
- `tests/INS-010/` (entire folder) — not committed
- `tests/GUI-007/test_gui007_edge_cases.py` — not committed
- `tests/GUI-007/test_gui007_tester_additions.py` — not committed
- `tests/INS-007/test_ins007_edge_cases.py` — not committed
- `tests/INS-007/test_ins007_tester.py` — not committed
- `tests/INS-007/test_ins007_tester_additions.py` — not committed

No WP folders found without a matching CSV entry (no orphan WP folders).
No obvious dead imports detected without running static analysis.

### Check 7 — Test Coverage Gaps (WARNING)

**Done WPs with no test results entries in committed `test-results.csv`:**
- **GUI-005**: No entries in committed test-results.csv (tests/GUI-005/ untracked)
- **GUI-006**: No entries in committed test-results.csv (tests/GUI-006/ untracked)
- **INS-010**: No entries in committed test-results.csv (tests/INS-010/ untracked)

**Done WPs missing `test-report.md`** (covered in Check 5): INS-007, INS-010, GUI-006, GUI-007.

All other Done WPs have test results entries in the CSV and test-report.md files present.

### Check 8 — Bug Tracking (WARNING)

**Open bugs:**

| Bug ID | Title | Severity | Issue |
|--------|-------|----------|-------|
| BUG-026 | version_label widget never added to app.py | High | Fixed in GUI-008 (Done/PASS) — status not updated to Fixed/Closed |
| BUG-027 | update_hashes.py missing from scripts/ | Medium | Open with no assigned workpackage (comment says "recommend follow-up task") |

Both open bugs have known fixes. BUG-026 is already fixed and needs status update only. BUG-027 requires a new workpackage to create `update_hashes.py`.

**All mandatory bug fields are filled** in both open entries. No open bugs with a blank `Fixed In WP` field except BUG-027 (which is intentionally unfixed).

### Check 9 — Structural Integrity (PASS)

- `copilot-instructions.md`: **40 lines** — exactly at the stated limit of 40. No detailed process rules present. Pass (at ceiling).
- **Agent files**: All 5 files present (`developer.agent.md`, `maintenance.agent.md`, `orchestrator.agent.md`, `story-writer.agent.md`, `tester.agent.md`) with valid YAML frontmatter.
- **`Default-Project/` template**: `git diff HEAD -- Default-Project/` is clean — no accidental test changes.

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Critical | Commit all staged changes on `GUI-007/input-validation-error-ux` branch to capture GUI-007 and INS-007 dev work | `docs/workpackages/GUI-007/dev-log.md`, `docs/workpackages/INS-007/dev-log.md`, `tests/GUI-007/__init__.py`, `tests/GUI-007/test_gui007_validation.py`, `tests/INS-007/__init__.py`, `tests/INS-007/test_ins007_build_appimage.py`, `src/installer/linux/build_appimage.sh`, CSVs |
| Critical | Stage and commit all untracked files (GUI-005, GUI-006, INS-010 folders and test files) so permanent test artifacts are not lost | `docs/workpackages/GUI-005/`, `docs/workpackages/GUI-006/`, `docs/workpackages/INS-010/`, `src/launcher/core/downloader.py`, `tests/GUI-005/`, `tests/GUI-006/`, `tests/INS-010/`, remaining GUI-007/INS-007 test files |
| Critical | Stage and commit all unstaged modified files (`bugs.csv`, `test-results.csv`, `workpackages.csv`, `app.py`, `conftest.py`) | `docs/bugs/bugs.csv`, `docs/test-results/test-results.csv`, `docs/workpackages/workpackages.csv`, `src/launcher/gui/app.py`, `tests/conftest.py` |
| Critical | Merge `GUI-007/input-validation-error-ux` (and all ancestor Done-WP commits) into `main`, then delete merged feature branches locally and remotely | Local and remote branches: GUI-002, GUI-005, GUI-007, GUI-008, INS-005, INS-006, INS-007, SAF-008, SAF-009 |
| Critical | Add `test-report.md` to Done WP folders currently missing them | `docs/workpackages/INS-007/test-report.md`, `docs/workpackages/INS-010/test-report.md`, `docs/workpackages/GUI-006/test-report.md`, `docs/workpackages/GUI-007/test-report.md` |
| Warning | Update `user-stories.csv` statuses to `Done` for US-003, US-004, US-005, US-006, US-013, US-014, US-015 (all linked WPs are Done) | `docs/user-stories/user-stories.csv` |
| Warning | Update BUG-026 status from `Open` to `Fixed` (or `Closed`) — fix was confirmed with GUI-008 Tester PASS | `docs/bugs/bugs.csv` |
| Warning | Create `dev-log.md` for SAF-008 (folder exists, test-report present, but dev-log missing) | `docs/workpackages/SAF-008/dev-log.md` |
| Warning | Update `docs/architecture.md` `tests/` section to include all 33 test subfolders (add GUI-002, GUI-005–010, INS-005–007, INS-010, SAF-004, SAF-008, SAF-009) | `docs/architecture.md` |
| Warning | Create a new workpackage to implement `update_hashes.py` and close BUG-027 | `docs/workpackages/workpackages.csv`, new WP folder + script |
| Warning | Clarify the "Pending human test execution" status for GUI-006, GUI-007, INS-007, INS-010 — confirm whether `Done` is premature or human runs have been completed | `docs/workpackages/workpackages.csv` |
| Info | Add test entries for GUI-005, GUI-006, INS-010 to `test-results.csv` once committed | `docs/test-results/test-results.csv` |
| Info | Confirm whether `Closed` (US-001, US-002) is a valid user story status per `user-story-rules.md`, or if it should be updated to `Done` | `docs/user-stories/user-stories.csv` |
| Info | Monitor `copilot-instructions.md` — currently at exactly 40 lines (ceiling); any future addition will violate the rule | `.github/instructions/copilot-instructions.md` |

---

## Status
**Awaiting human review** — Do NOT implement any changes until approved.
