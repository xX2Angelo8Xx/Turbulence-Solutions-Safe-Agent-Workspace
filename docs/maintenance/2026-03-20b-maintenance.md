# Maintenance Log — 2026-03-20 (Run 2)

**Performed by:** Maintenance Agent (GitHub Copilot — Claude Sonnet 4.6)

---

## Results

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Git Hygiene | Warning | One unstaged deletion in working tree: `docs/workpackages/FIX-063/.finalization-state.json`. No stale/undeleted branches (3 previous branches resolved ✓). HEAD at tag v3.1.0. All Done WPs committed and pushed. |
| 2 | WP–US Consistency | Warning | FIX-036, FIX-040, FIX-047 have corrupted "User Story" fields due to CSV row malformation (see Check 3). FIX-037 has no independent CSV row. US-024 and US-026 have corrupted "Linked WPs" fields. Underlying references are valid — corruption is structural. |
| 3 | CSV Integrity | Fail | `workpackages.csv`: 3 malformed rows — FIX-036 row embeds FIX-037 data (missing row delimiter), FIX-040 row embeds FIX-039 data, FIX-047 "Comments" field has unescaped comma creating spurious extra columns. FIX-037 has no independent parseable row. `user-stories.csv`: US-024 Linked WPs field and US-026 Linked WPs field corrupted with escaped-quote artefacts. `test-results.csv` and `bugs.csv`: no issues. |
| 4 | Documentation Freshness | Pass | All key directories exist. Default-Project not referenced in architecture.md. All 10 rule files listed in work-rules/index.md (2 new files since last log: `recovery.md`, `user-story-rules.md`). |
| 5 | WP Folder Integrity | Warning | Missing `test-report.md` in INS-008 (decomposed WP — intentional) and MNT-001 (maintenance WP — intentional). FIX-058, FIX-062, FIX-063 all have test-report.md ✓ (gap from previous log resolved). All 142 Done/InProgress WP folders present; all have `dev-log.md`. |
| 6 | Orphan Detection | Warning | `docs/workpackages/FIX-037/` folder exists but FIX-037 has no independent CSV row (due to Check 3 corruption). All other WP folders match CSV entries. |
| 7 | Test Coverage Gaps | Warning | INS-008 has no `tests/INS-008/` folder and no TST records (decomposed WP — tested via INS-013–017). All other Done WPs have test folders and TST entries. SAF-027 gap from previous log now resolved ✓. |
| 8 | Bug Tracking | Warning | BUG-088, BUG-089, BUG-090 have status `Open` with no assigned WP but were resolved by FIX-062/FIX-063 (Done, Tester PASS). BUG-086 is Open with no WP assigned. BUG-084 has non-standard status `Resolved` (should be `Open` or `Closed`). All mandatory fields populated. |
| 9 | Structural Integrity | Pass | `copilot-instructions.md`: 39 lines (under 40 limit) ✓. All 10 agent files have valid YAML frontmatter ✓. All 12 scripts parse without errors ✓. |
| 10 | Recurring Issue Tracking | Warning | (A) TST ID duplicates: 4th historical occurrence — **resolved this cycle** (0 duplicates). Prevention rule still absent from testing-protocol.md. (B) Missing test-report.md for INS-008/MNT-001: 2nd consecutive cycle unfixed (justified). (C) CSV row corruption: new pattern — FIX-036/037 and FIX-040 rows malformed. No rule exists to validate CSV well-formedness on write. (D) Bugs not closed after fixing WP completes: BUG-088/089/090 pattern — new occurrence. |
| 11 | Automated Validation | Pass | `scripts/validate_workspace.py --full` returned "All checks passed." with exit code 0. |

---

## Detailed Findings

### Check 1 — Git Hygiene (WARNING)

Working tree has one unstaged deletion:
- `D docs/workpackages/FIX-063/.finalization-state.json` — a finalization tracking file deleted but not committed/staged.

Branches: Only `main` (local and remote). All 3 previously undeleted merged branches have been cleaned up since the earlier 2026-03-20 log ✓.

HEAD is at tag `v3.1.0` commit `8878e5e`. All Done WPs are committed and pushed to `origin/main`. No Done WPs awaiting commit.

---

### Check 3 — CSV Integrity (FAIL)

**`workpackages.csv` — 3 malformed rows:**

| Affected WP | Issue | Effect |
|------------|-------|--------|
| FIX-036 | Row missing closing delimiter; FIX-037's content is embedded in it | FIX-037 has no independent parseable row; FIX-036's "User Story" and "Depends On" fields contain raw FIX-037 data |
| FIX-040 | Row embeds FIX-039 metadata in its "User Story" column | FIX-040's User Story value contains FIX-039 description text |
| FIX-047 | "Comments" field contains unescaped comma | Trailing columns shift; "User Story" reads as `Default-Project removal, audit documentation.",Enabler` |

Consequence: The CSV parser produces 144 rows instead of the expected 145 (FIX-037 is missing). Any script reading workpackages.csv will miss FIX-037 entirely.

**`user-stories.csv` — 2 corrupted fields:**
- US-024 "Linked WPs" field contains literal text debris from adjacent cell escaping
- US-026 "Linked WPs" field starts with `\"FIX-031` (escaped quote artefact)

These do not affect the actual WP-US linkage (the underlying relationships are valid) but will cause programmatic validation failures.

**`bugs.csv`:**
- BUG-084 has status `Resolved` — not a valid enum value (valid: `Open`, `Closed`). Should be `Closed` given it was addressed in FIX-054.

**`test-results.csv`:** 1,846 rows, 0 duplicate TST IDs ✓

---

### Check 6 — Orphan Detection (WARNING)

`docs/workpackages/FIX-037/` folder exists but FIX-037 is not parseable as a separate CSV row (it is embedded inside FIX-036's corrupted row). This is a direct consequence of the Check 3 CSV corruption. From a filesystem perspective the folder is correct; from a CSV traceability perspective FIX-037 is invisible to validation tools.

---

### Check 7 — Test Coverage Gaps (WARNING)

**INS-008** (CI/CD Pipeline) is the only Done WP missing a `tests/<WP-ID>/` folder. This is expected — INS-008 was decomposed into sub-WPs INS-013 through INS-017, each of which has full test coverage. INS-008 itself performed no direct code changes.

Previous issue: **SAF-027** had no test folder in the earlier 2026-03-20 log. Now resolved — `tests/SAF-027/` exists containing `test_saf027_tests_exist_in_saf026.py` ✓.

---

### Check 8 — Bug Tracking (WARNING)

**Bugs fixed but not closed (3):**

| Bug ID | Title | Fixed By WP | WP Status |
|--------|-------|-------------|-----------|
| BUG-088 | macOS codesign fails on TS-Logo.png | FIX-062 | Done (Tester PASS) |
| BUG-089 | macOS codesign fails on non-code files in _internal/ | FIX-063 | Done (Tester PASS) |
| BUG-090 | FIX-063 removes Step 3.2 but FIX-062 tests not updated | FIX-063 Iter 2 | Done (Tester PASS) |

These should be moved to `Closed` and their "Fixed In WP" fields populated.

**Bug with no assigned WP (1):**
- BUG-086: "FIX-050 version tests hardcode 3.0.2 — fails after version bump". No WP created yet. Open.

**Non-standard status (1):**
- BUG-084 has `Resolved` status. The valid enum defined in bug-tracking-rules.md uses `Open`/`Closed`. Should be `Closed` (FIX-054 Done, Tester PASS).

---

### Check 10 — Recurring Issue Tracking (WARNING)

**(A) TST ID Duplicates — Recurring (4th occurrence)**
- Occurrences: 2026-03-11 (BUG-009), 2026-03-13 (BUG-035), 2026-03-20 9 duplicates, 2026-03-20 cycle 2: 0 duplicates (resolved).
- Root cause: No rule specifies checking for max TST-ID before assigning new ones.
- Proposed rule addition: testing-protocol.md should mandate running `scripts/dedup_test_ids.py` or checking `scripts/add_test_result.py --next-id` before every new TST entry block.

**(B) Missing test-report.md for INS-008 / MNT-001 — Recurring (2nd consecutive cycle)**
- Both are justified exceptions (decomposed WP, maintenance WP) but not formally documented as exceptions.
- Proposed: Add a note to INS-008 and MNT-001 dev-logs explicitly stating "test-report.md not applicable — reason: [decomposed/maintenance]" to stop this being flagged each cycle.

**(C) CSV Row Corruption — New Pattern**
- FIX-036/037 and FIX-040 rows are corrupted. This appears to result from CSV fields containing unescaped double-quote characters or newlines appended without proper RFC 4180 quoting.
- Proposed: The `scripts/csv_utils.py` write functions should be audited to enforce proper quoting on all field writes.

**(D) Bugs Not Closed After Fixing WP Completes — New Pattern**
- BUG-088, BUG-089, BUG-090 were resolved as part of FIX-062/FIX-063 but remain `Open`.
- Proposed: Add a step to `docs/work-rules/bug-tracking-rules.md` requiring finalization of linked bugs (status → Closed, Fixed In WP populated) as part of WP finalization.

---

## Proposed Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| Warning | Repair 3 malformed rows in `workpackages.csv` (FIX-036 embeds FIX-037 content; FIX-040 row corrupted; FIX-047 unescaped comma). Ensure FIX-037 appears as an independent row with correct Status=Done and User Story=US-026. | `docs/workpackages/workpackages.csv` |
| Warning | Fix 2 corrupted "Linked WPs" fields in `user-stories.csv` (US-024, US-026). | `docs/user-stories/user-stories.csv` |
| Warning | Close BUG-088, BUG-089, BUG-090 — set Status=Closed, populate Fixed In WP (FIX-062/FIX-063). | `docs/bugs/bugs.csv` |
| Warning | Fix BUG-084 status from `Resolved` to `Closed`. | `docs/bugs/bugs.csv` |
| Warning | Populate "Fixed In WP" for BUG-088 (FIX-062), BUG-089 (FIX-063), BUG-090 (FIX-063). | `docs/bugs/bugs.csv` |
| Warning | Stage and commit the deletion of `docs/workpackages/FIX-063/.finalization-state.json` (currently unstaged). | `docs/workpackages/FIX-063/.finalization-state.json` |
| Info | Add explicit "test-report.md N/A" notes to INS-008 and MNT-001 dev-logs to suppress recurring false-positive in WP Folder Integrity check. | `docs/workpackages/INS-008/dev-log.md`, `docs/workpackages/MNT-001/dev-log.md` |
| Info | Add TST-ID uniqueness enforcement rule to `docs/work-rules/testing-protocol.md` — mandate checking max ID before assigning new TST blocks. | `docs/work-rules/testing-protocol.md` |
| Info | Add bug-closure step to `docs/work-rules/bug-tracking-rules.md` — when a WP is finalized, all linked bugs must be set to Closed with Fixed In WP populated. | `docs/work-rules/bug-tracking-rules.md` |
| Info | Create a WP for BUG-086 (FIX-050 version tests hardcode 3.0.2) — assign and track fix. | `docs/workpackages/workpackages.csv` |
| Info | Audit `scripts/csv_utils.py` write functions for proper RFC 4180 quoting enforcement to prevent future CSV row corruption. | `scripts/csv_utils.py` |

---

## Status
**Awaiting human review** — Do NOT implement any changes until approved.
