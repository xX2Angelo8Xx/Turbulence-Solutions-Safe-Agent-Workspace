# Test Report — GUI-015: Rename Root Folder to TS-SAE-{ProjectName}

## Summary

| Field | Value |
|-------|-------|
| WP ID | GUI-015 |
| Tester | Tester Agent |
| Date | 2026-03-17 |
| Verdict | **PASS** |

---

## Code Review

### `src/launcher/core/project_creator.py`

- `create_project()` prepends `"TS-SAE-"` to `folder_name` before constructing the target path. ✓
- Path-traversal guard (`is_relative_to`) is applied **after** prepending, on the resolved path. ✓
- With the prefix in place, a **3-level** traversal is required to escape the destination — confirmed correct by manual path-normalization trace. ✓
- `shutil.copytree()` called with the prefixed target path; template contents are copied correctly. ✓

### `src/launcher/gui/app.py`

- `_on_create_project()` passes the raw `folder_name` to `create_project()` (prefix handled inside the function). ✓
- Duplicate check updated: `check_duplicate_folder(f"TS-SAE-{folder_name}", ...)`. ✓
- Error message text updated: `'A folder named "TS-SAE-{folder_name}" already exists...'`. ✓
- Success message still uses the original `folder_name` (not prefixed) — cosmetically acceptable; success path shows the full `created_path`. ✓

---

## Acceptance Criteria Verification

| AC | Requirement | Status |
|----|-------------|--------|
| AC1 | Entering "MatlabDemo" creates `TS-SAE-MatlabDemo/` folder | PASS |
| AC2 | Returned path from `create_project()` names the prefixed folder | PASS |
| AC3 | Folder with raw (unprefixed) name is NOT created | PASS |
| AC4 | Duplicate check detects `TS-SAE-{name}` prefix collision | PASS |
| AC5 | Path-traversal guard still functional (3-level test) | PASS |

---

## Test Execution

### Developer Tests (`tests/GUI-015/test_gui015_rename_root_folder.py`)

| Suite | Tests | Result |
|-------|-------|--------|
| `TestCreateProjectPrefix` | 7 | PASS |
| `TestCreateProjectTraversalGuard` | 2 | PASS |
| `TestCreateProjectErrors` | 3 | PASS |
| `TestDuplicateFolderCheck` | 3 | PASS |
| **Total** | **15** | **15 PASS** |

### Tester Edge-Case Tests (`tests/GUI-015/test_gui015_tester_edge_cases.py`)

| Suite | Tests | Result |
|-------|-------|--------|
| `TestSpecialCharactersInName` | 5 | PASS |
| `TestEmptyFolderName` | 1 | PASS |
| `TestVeryLongFolderName` | 1 | PASS |
| `TestUnicodeNames` | 2 | PASS |
| `TestCasePreservation` | 3 | PASS |
| `TestTwoLevelTraversalBoundary` | 1 | PASS |
| **Total** | **13** | **13 PASS** |

### Full Regression Suite

| Run | Command | Result |
|-----|---------|--------|
| Pre-edge-case | `.venv\Scripts\python -m pytest tests/ --tb=short -q` | 2975 passed, 1 pre-existing fail (INS-005/BUG-045), 29 skipped |
| Post-edge-case | `.venv\Scripts\python -m pytest tests/ --tb=short -q` | 2988 passed, 1 pre-existing fail (INS-005/BUG-045), 29 skipped |

**No new regressions introduced by GUI-015.**

---

## Edge-Case Analysis

### Special Characters
Hyphens, underscores, embedded dots, and digits in the folder name are all handled correctly — the raw string is concatenated with the `"TS-SAE-"` literal prefix with no character filtering or transformation.

### Empty Name
Passing `""` to `create_project()` creates a folder named `"TS-SAE-"`. This is only reachable via direct API usage; the GUI rejects empty names through `validate_folder_name()`. Documented behavior, not a defect.

### Long Names
100-character names result in a 107-character prefixed folder name. Well within POSIX (255 chars) and Windows MAX_PATH (260 chars for typical tmpdir depths) limits, and confirmed on disk.

### Unicode Names
Latin-extended (e.g., `Café`) and CJK (e.g., `プロジェクト`) characters in the folder name are preserved exactly. Modern Windows, macOS, and Linux filesystems support Unicode filenames.

### Case Sensitivity
`create_project()` applies zero case normalization. Mixed-case, all-lowercase, and all-uppercase names are stored exactly as supplied. Cross-platform behavior (case-insensitive filesystems on Windows/macOS vs. case-sensitive on Linux) is the expected OS-level behavior and is not manipulated by the function.

### Two-Level Traversal Boundary
The `TS-SAE-` prefix introduces one extra path component (`TS-SAE-..` when followed by traversal input). Path normalization treats `TS-SAE-..` as a literal directory name; a following `..` cancels that one component, returning to the destination. Therefore a **2-level** traversal (`../../x`) resolves to `dest/x` — inside destination — and does **not** trigger the ValueError guard. A **3-level** traversal (`../../../x`) escapes and is blocked. Verified by:
1. Direct path-normalization trace (mathematical proof)
2. `test_two_level_traversal_absorbed_stays_in_dest` (empirical)
3. `test_path_traversal_still_rejected` (developer test, 3-level — still passes)

**Security assessment:** This is NOT a security regression. `validate_folder_name()` rejects `/` and `\` at the GUI boundary, preventing traversal input. The `create_project()` guard is defense-in-depth for direct API usage and remains effective against the real attack vector (3-level+).

### Prefix Immutability
The prefix `"TS-SAE-"` is a hardcoded string literal in `project_creator.py`. It is not configurable, not read from external input, and not constructed dynamically — eliminating injection risk.

---

## Regression Tests Modified by Developer

The developer updated the following existing test files to reflect the new behavior. These were reviewed and are correct:

| File | Change |
|------|--------|
| `tests/GUI-005/test_gui005_project_creation.py` | Expected folder names updated to `TS-SAE-*` |
| `tests/GUI-007/test_gui007_validation.py` | Duplicate-check folder creation uses `TS-SAE-*` prefix |
| `tests/GUI-007/test_gui007_tester_additions.py` | Stripped-name duplicate test uses `TS-SAE-*` prefix |
| `tests/INS-001/test_ins001_structure.py` | Traversal tests updated to 3-level escape threshold |
| `tests/INS-004/test_ins004_template_bundling.py` | `assert result.name` expects `TS-SAE-test-project` |

All 2988 tests in the updated suite pass (**excluding** the pre-existing BUG-045 INS-005 failure which predates this WP).

---

## Pre-Existing Failure

`tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — tracked as **BUG-045** (Open). Not caused by GUI-015.

---

## Verdict

**PASS** — All acceptance criteria met. All 28 GUI-015 tests green (15 developer + 13 tester). No regressions. Security guard verified effective.
