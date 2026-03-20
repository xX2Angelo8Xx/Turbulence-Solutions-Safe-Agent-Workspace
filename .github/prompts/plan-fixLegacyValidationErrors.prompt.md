# Plan: Fix 45 Pre-Existing Legacy Validation Errors

Two sequential workpackages — **FIX-059** (validator bug + CSV normalization) then **FIX-060** (all missing artifacts) — with **5 parallel subagents** within FIX-060 for maximum throughput and zero file conflicts.

---

### Error Inventory (45 errors, 24 unique WPs)

| Category | Count | WPs |
|----------|-------|-----|
| Missing `tests/{WP}/` directory | 10 | FIX-001–005, FIX-024/025/027, FIX-043, MNT-001 |
| Empty test dir (no `test_*.py`) | 3 | SAF-004, SAF-027, FIX-046 |
| Missing `dev-log.md` | 5 | FIX-023–027 |
| Missing `test-report.md` | 5 | FIX-023–027 |
| Leftover `tmp_*` files | 3 | SAF-033, FIX-046, FIX-055 |
| No passing TST entry | 19 | GUI-005/006, INS-010, FIX-001/002/023–027/032/035/041/042, SAF-027/032/033/034, FIX-046 |

**Root cause discovery:** The validator checks `Status == "Pass"` (case-sensitive), but legacy entries use `"PASS"` (confirmed for FIX-042's 8 entries). This causes **false positive errors** — the tests passed, the validator just can't see them. Additionally, 10+ WPs have genuinely zero entries at all.

---

### WP-1: FIX-059 — Fix Validator Case-Sensitivity + Normalize CSV

**Branch:** `FIX-059/validator-case-sensitivity` | **Single agent, no subagents.**

**Steps**

1. Fix `_check_tst_coverage()` in `scripts/validate_workspace.py` — change `.strip() == "Pass"` to `.strip().lower() == "pass"` (*line ~167*)
2. Normalize all Status values in `docs/test-results/test-results.csv` — `"PASS"` → `"Pass"`, `"FAIL"` → `"Fail"`
3. Verify `scripts/run_tests.py` always writes `"Pass"`/`"Fail"` (already does — confirm)
4. Create `docs/workpackages/FIX-059/` with `dev-log.md` + `test-report.md`
5. Create `tests/FIX-059/test_fix059_case_insensitive_status.py` — test that "PASS", "Pass", "pass" all recognized
6. Run `validate_workspace.py --full` → record the **true** remaining error count (this defines FIX-060's scope)
7. Run tests via `run_tests.py`, commit, merge via `finalize_wp.py`

---

### WP-2: FIX-060 — Fix All Legacy Artifacts (Parallel Subagents)

**Branch:** `FIX-060/legacy-artifact-cleanup` | **Depends on: FIX-059 merged first.**

#### Phase A: Parallel Filesystem Operations (5 Subagents)

Each subagent owns a **disjoint set of directories** — zero conflict risk. No subagent touches `test-results.csv`.

**Subagent 1 — tmp_ cleanup + FIX-023→027 artifact creation**
Touches: `docs/workpackages/{SAF-033,FIX-046,FIX-055,FIX-023,FIX-024,FIX-025,FIX-026,FIX-027}/`
- Delete 3 leftover tmp_ files
- Create 5 `dev-log.md` + 5 `test-report.md` — reconstructed from git history (descriptions available from workpackages.csv)

**Subagent 2 — Create test dirs + real tests for FIX-001→005**
Touches: `tests/FIX-001/` through `tests/FIX-005/`

| WP | Test | Verifies |
|----|------|----------|
| FIX-001 | `test_fix001_mock_isolation_fix.py` | GUI-004 test uses `call_args_list` pattern (not bare `call_args`) |
| FIX-002 | `test_fix002_hook_config_migration.py` | `require-approval.json` references `security_gate.py`, not legacy bash |
| FIX-003 | `test_fix003_template_sync.py` | Key files in `templates/coding/` exist and are non-empty |
| FIX-004 | `test_fix004_shell_line_endings.py` | `build_dmg.sh` and `build_appimage.sh` use LF (no `\r\n`) |
| FIX-005 | `test_fix005_launcher_spec_untracked.py` | `.gitignore` contains `*.spec` pattern |

**Subagent 3 — Create test dirs + verification tests for investigation WPs**
Touches: `tests/FIX-024/`, `tests/FIX-025/`, `tests/FIX-027/`, `tests/FIX-043/`

| WP | Test | Verifies |
|----|------|----------|
| FIX-024 | `test_fix024_absolute_path_verification.py` | `zone_classifier.py` uses `Path.relative_to()` for absolute path resolution |
| FIX-025 | `test_fix025_cat_type_in_allowlist.py` | `"cat"` and `"type"` present in `security_gate.py` allowlist / `_PROJECT_FALLBACK_VERBS` |
| FIX-027 | `test_fix027_absolute_path_handling.py` | `zone_classifier.py` Method 1 uses `pathlib.relative_to()` for Windows paths |
| FIX-043 | `test_fix043_inno_setup_regex.py` | `tests/INS-005/` source contains `"filesandordirs"` (correct spelling) |

**Subagent 4 — Populate empty test dirs + create MNT-001 tests**
Touches: `tests/SAF-004/`, `tests/SAF-027/`, `tests/FIX-046/`, `tests/MNT-001/`

| WP | Test | Verifies |
|----|------|----------|
| SAF-004 | `test_saf004_design_doc_validation.py` | `terminal-sanitization-design.md` exists, >100 lines, has required sections |
| SAF-027 | `test_saf027_tests_exist_in_saf026.py` | Tests co-located in `tests/SAF-026/` (by design), contain scan test functions |
| FIX-046 | `test_fix046_default_project_removed.py` | `Default-Project/` gone, `templates/coding/` exists |
| MNT-001 | `test_mnt001_maintenance_verification.py` | No `pytest_*.txt` in repo root, `dev-log.md` exists |

**Subagent 5 — Create FIX-060 WP artifacts**
Touches: `docs/workpackages/FIX-060/`
- `dev-log.md` documenting the full remediation
- `test-report.md` summarizing results

#### Phase B: Run Tests + Log Results (Sequential, Main Agent)

*Depends on: all Phase A subagents complete.*

Why sequential: Each `run_tests.py` writes to `test-results.csv` under FileLock. Sequential avoids contention and keeps TST-ID ordering clean.

```
# Group 1: New tests from Subagent 2
run_tests.py --wp FIX-001 ... through FIX-005

# Group 2: New tests from Subagent 3
run_tests.py --wp FIX-024, FIX-025, FIX-027, FIX-043

# Group 3: New tests from Subagent 4
run_tests.py --wp SAF-004, SAF-027, FIX-046, MNT-001

# Group 4: Existing tests that just need TST entries logged
run_tests.py --wp FIX-023, FIX-026, GUI-005, GUI-006, INS-010

# Group 5: Check which WPs still need entries after FIX-059 normalization
# (FIX-032/035/041/042, SAF-032/033/034) — validate first, run only if needed
```

#### Phase C: Verify + Commit (Main Agent)

1. `validate_workspace.py --full` → **must return 0 errors**
2. `git add -A` + `git diff --cached --stat`
3. `git commit` — pre-commit hook **must pass cleanly** (no `--no-verify`)
4. `finalize_wp.py FIX-060` — merge, delete branch, push

---

### Conflict Safety Matrix

| Resource | Phase A (parallel) | Phase B (sequential) | Risk |
|----------|-------------------|---------------------|------|
| `tests/{WP}/` dirs | One subagent each | Read-only (pytest) | **ZERO** — disjoint |
| `docs/workpackages/{WP}/` | One subagent each | Not touched | **ZERO** — disjoint |
| `test-results.csv` | Not touched | Sequential writes | **ZERO** — FileLock + serial |
| Git working tree | Creates only, disjoint dirs | Not modified | **ZERO** |
| Git index | Not touched | Not touched | **ZERO** — single `git add -A` in Phase C |

---

### Verification

1. `validate_workspace.py --full` → **0 errors, 0 warnings** for all 24 WPs
2. All 13 new test files pass via `pytest`
3. Zero `tmp_*` files remain in any WP directory
4. All 24 WPs have ≥1 "Pass" entry in `test-results.csv`
5. Clean `git commit` — pre-commit hook passes without `--no-verify`

---

### Decisions

- **Two WPs**: FIX-059 (validator) → FIX-060 (artifacts), strictly sequential
- **Both**: case-insensitive validator + CSV Status normalization
- **Reconstruct** artifacts from git history and CSV descriptions
- **Real verification tests** that confirm each WP's fix still holds
- **Design-doc validation test** for SAF-004 (>100 lines, required sections)
- **Pre-commit hook must pass** for FIX-060 commit (no `--no-verify`)

### Further Considerations

1. **Group 5 uncertainty**: After FIX-059 normalizes Status values, some of the 7 WPs in Group 5 (FIX-032/035/041/042, SAF-032/033/034) may already have valid "Pass" entries. Run `validate_workspace.py --wp {WP}` for each before creating unnecessary test runs. _Recommendation: check first, run only if needed._
2. **FIX-060 test count**: If all 19 TST errors need new entries, Phase B runs ~22 `run_tests.py` invocations. If FIX-059 resolves some, this drops. The plan handles both cases.
