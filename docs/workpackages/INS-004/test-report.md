# Test Report — INS-004

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

**VERDICT: FAIL** — Four blocking issues discovered. Three critical deliverables are missing or
incorrect in the committed code, and the developer's entire 27-test suite cannot run due to an
ImportError. The WP must be returned to the Developer with the issues described below.

---

## Review Findings

### 1. `config.TEMPLATES_DIR` Not Present in `src/launcher/config.py` — CRITICAL

The dev-log (Iteration 2) states that `TEMPLATES_DIR: Path` was added to `config.py`.
Inspection of the actual file reveals it still contains only `APP_NAME` and `VERSION`:

```python
APP_NAME: str = "Turbulence Solutions Launcher"
VERSION: str = "0.1.0"
```

No `TEMPLATES_DIR` constant. The code change was not committed.

### 2. `list_templates()` Not Present in `src/launcher/core/project_creator.py` — CRITICAL

The dev-log (Iteration 2) states that `list_templates()` was added to `project_creator.py`.
The actual function is absent. This causes an `ImportError` at test-collection time, which
blocks all 27 developer-written tests from running:

```
ImportError: cannot import name 'list_templates' from 'launcher.core.project_creator'
```

### 3. `require-approval.json` Missing from `templates/coding/.github/hooks/` — CRITICAL

The file exists in `Default-Project/.github/hooks/require-approval.json` but was **not
copied** to `templates/coding/.github/hooks/`. The directory listing confirms only
`scripts/` is present under `hooks/`.

### 4. `security_gate.py` in Template is Outdated — HIGH

`templates/coding/.github/hooks/scripts/security_gate.py` differs from
`Default-Project/.github/hooks/scripts/security_gate.py`. The template was copied during
INS-004 development, but subsequent SAF workpackages (SAF-001 Iteration 2, SAF-002, SAF-005)
updated the source file. The template contains the earlier insecure version. Users who create
a project from this template will receive a security-downgraded copy.

### 5. WP Status Not Set to `Review` in workpackages.csv — MINOR WORKFLOW VIOLATION

`workpackages.csv` shows INS-004 status as `In Progress` at handoff time. The developer
completed Iteration 2 and updated the dev-log but never set the status to `Review` in the CSV.
The WP was not properly handed off per Step 7 of `agent-workflow.md`.

---

## Tests Executed

### Developer Test Suite (`test_ins004_template_bundling.py`)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Entire test module (27 tests) | Unit/Integration | BLOCKED | ImportError: cannot import `list_templates`; all 27 tests unrunnable |

### Tester Edge-Case Suite (`test_ins004_edge_cases.py`, 18 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_require_approval_json_exists_in_template | Unit | **FAIL** | BUG-019: file missing from hooks/ dir |
| test_vscode_settings_is_valid_jsonc | Unit | PASS | JSONC parses correctly after comment strip |
| test_require_approval_json_is_valid_json | Unit | **FAIL** | Cascades from BUG-019 (file missing) |
| test_no_pyc_files_in_template | Unit | PASS | No .pyc files found |
| test_no_pyo_files_in_template | Unit | PASS | No .pyo files found |
| test_readme_content_matches_default_project | Unit | PASS | Content identical |
| test_gitignore_content_matches_default_project | Unit | PASS | Content identical |
| test_vscode_settings_content_matches_default_project | Unit | PASS | Content identical |
| test_security_gate_content_matches_default_project | Unit | **FAIL** | BUG-020: template has outdated security_gate.py |
| test_zone_classifier_content_matches_default_project | Unit | PASS | Content identical |
| test_coding_template_key_files_not_empty | Unit | **FAIL** | Cascades from BUG-019 (JSON missing) |
| test_coding_template_has_no_symlinks | Unit | PASS | No symlinks found |
| test_coding_skills_dir_exists | Unit | PASS | .github/skills/ present |
| test_coding_prompts_dir_exists | Unit | PASS | .github/prompts/ present |
| test_templates_root_contains_only_directories | Unit | PASS | Only coding/ subdir at root |
| test_list_templates_returns_sorted_results | Unit | **FAIL** | BUG-018: list_templates() missing |
| test_config_templates_dir_is_defined | Unit | **FAIL** | BUG-017: TEMPLATES_DIR missing |
| test_config_templates_dir_is_absolute | Unit | **FAIL** | Cascades from BUG-017 |

**Edge-case summary: 7 FAIL, 11 PASS**

### Full Test Suite (excluding INS-004 — which blocks at collection)

| Suite | Result | Notes |
|-------|--------|-------|
| All tests excluding INS-004 | 54 fail / 442 pass | 54 failures are all **pre-existing** (SAF-007, SAF-010 — unrelated to INS-004) |

---

## Bugs Found

- **BUG-017**: `TEMPLATES_DIR` constant missing from `config.py` (logged in `docs/bugs/bugs.csv`)
- **BUG-018**: `list_templates()` function missing from `project_creator.py` (logged in `docs/bugs/bugs.csv`)
- **BUG-019**: `require-approval.json` not copied to `templates/coding/.github/hooks/` (logged in `docs/bugs/bugs.csv`)
- **BUG-020**: `security_gate.py` in template is outdated vs `Default-Project/` (logged in `docs/bugs/bugs.csv`)

---

## TODOs for Developer

- [ ] Add `TEMPLATES_DIR: Path = Path(__file__).parent.parent.parent / "templates"` to
  `src/launcher/config.py`. (Resolves BUG-017.)
- [ ] Add `list_templates(templates_dir: Path) -> list[str]` to
  `src/launcher/core/project_creator.py` — returns sorted directory names under the given
  path; returns `[]` when the directory does not exist. (Resolves BUG-018.)
- [ ] Copy `Default-Project/.github/hooks/require-approval.json` to
  `templates/coding/.github/hooks/require-approval.json`. (Resolves BUG-019.)
- [ ] Re-sync `templates/coding/.github/hooks/scripts/security_gate.py` with
  `Default-Project/.github/hooks/scripts/security_gate.py`. The template copy is stale and
  lacks security hardening from SAF-001 Iteration 2, SAF-002, and SAF-005. (Resolves BUG-020.)
- [ ] After applying the above changes, set INS-004 status to `Review` in `workpackages.csv`
  before handing off.
- [ ] After fixing, all 27 developer tests + 18 Tester edge-case tests must pass.

---

## Verdict

**FAIL** — Return INS-004 to `In Progress`. Developer must address all 4 TODOs above and
confirm all tests pass before handing off again.
