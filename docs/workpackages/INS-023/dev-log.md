# Dev Log — INS-023: Skip README files during project creation

## WP Summary
Implement the `include_readmes` parameter in `create_project()` so that when `False`,
all files named exactly `README.md` in the newly created workspace are removed after
`copytree` completes. The GUI-022 wiring in `app.py` was already in place.

## Branch
`INS-023/skip-readmes`

## Status
In Progress → Review

---

## Implementation

### Files Changed
- `src/launcher/core/project_creator.py` — added README deletion loop after
  `replace_template_placeholders`. Uses `os.walk` + `os.unlink` with
  `try/except FileNotFoundError` to silently skip already-missing files.
  Added `import os` at top.

### Design Decisions
1. Walk with `os.walk` to visit all subdirectories; match basename exactly
   `"README.md"` (case-sensitive) — satisfies the critical constraint that
   `AGENT-RULES.md`, `copilot-instructions.md`, and other `.md` files are
   never touched.
2. `try/except FileNotFoundError` on each `os.unlink` call handles the edge
   case where a template was already shipped without a README.
3. `app.py` did not need changes — GUI-022 already wired `include_readmes_var`
   into `create_project()`.

---

## Tests Written
- `tests/INS-023/test_ins023_skip_readmes.py`
  - `test_include_readmes_true_preserves_readmes` — default behaviour
  - `test_include_readmes_false_removes_readmes` — core feature
  - `test_include_readmes_false_preserves_non_readmes` — AGENT-RULES.md and
    copilot-instructions.md survive
  - `test_include_readmes_false_missing_readme_no_error` — edge case
  - `test_default_parameter_is_true` — parameter default value
  - `test_include_readmes_true_explicit` — explicit True preserves files
  - `test_only_readme_md_files_deleted_not_others` — case-sensitive name check

## Test Results
All 7 tests pass. See test-results.csv for logged entry.

---

## Known Limitations
None.

---

## Iteration 2 — Fix read-only README.md crash (BUG-105)

### Problem
The Tester's edge-case test `TestReadonlyReadme::test_readonly_readme_does_not_crash_project_creation`
failed because `except FileNotFoundError` did not cover `PermissionError`, which Windows
raises when `os.unlink` is called on a read-only file.

### Fix Applied
`src/launcher/core/project_creator.py`:
1. Added `import stat` at module level.
2. Changed the exception handling in the README deletion loop:
   - First try `os.unlink(path)` as before.
   - On `PermissionError`: clear write-protection via `os.chmod(path, stat.S_IWRITE)`,
     then retry `os.unlink(path)`. Any remaining `OSError` is silently suppressed.
   - `FileNotFoundError` is still caught separately (no regression for race-condition edge case).

### Tests
All 22 tests in `tests/INS-023/` pass (20 passed, 2 skipped on Windows — symlinks and
case-sensitive FS are platform-limited, skip is intentional).
