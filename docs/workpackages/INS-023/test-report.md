# Test Report — INS-023: Skip README files during project creation

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Branch:** `INS-023/skip-readmes`  
**Iteration:** 2

---

## Summary

Iteration 2 review. BUG-105 (PermissionError on read-only README.md) was correctly fixed
by the Developer. The fix adds `import stat`, catches `PermissionError` separately from
`FileNotFoundError`, calls `os.chmod(path, stat.S_IWRITE)` to clear write-protection,
then retries `os.unlink`. Any remaining `OSError` is silently suppressed. The regression
in the Tester's edge-case test now passes.

All 22 INS-023 tests executed: **20 passed, 2 skipped** (platform-appropriate skips for
symlink test on Windows and case-insensitive-filesystem test on Windows — both skips are
correct and intentional).

---

## Code Review

File reviewed: `src/launcher/core/project_creator.py`

### Verified correct

- `import stat` added at module level.
- `os.walk(target)` visits every subdirectory recursively — all `README.md` files at
  any nesting depth are found and deleted.
- Exact `filename == "README.md"` match: `AGENT-RULES.md`, `copilot-instructions.md`,
  and all other `.md` files are untouched.
- Exception handling: `PermissionError` → `os.chmod + retry`; remaining `OSError`
  silently suppressed; `FileNotFoundError` caught separately (race-condition guard).
- `include_readmes=True` (default) path is unchanged — no README deletion occurs.
- `app.py` wiring (GUI-022 `include_readmes_var`) was confirmed already correct.
- `filename == "README.md"` is a case-sensitive exact match — `AGENT-RULES.md`,
  `copilot-instructions.md`, `README.rst`, `README.txt`, `README-DEV.md`, and all
  other variants are left untouched.
- `except FileNotFoundError: pass` correctly handles the race where the file was
  already absent in the template.
- The loop runs after `replace_template_placeholders` — no placeholders are left in
  the files that are about to be deleted.
- `app.py` was correctly left unchanged (GUI-022 wiring already in place).
- `include_readmes` parameter defaults to `True` — fully backwards-compatible.

---

## Tests Executed (Iteration 2)

### Developer suite (`test_ins023_skip_readmes.py`)

| Test | Result |
|------|--------|
| `test_include_readmes_true_preserves_readmes` | PASS |
| `test_default_parameter_is_true` | PASS |
| `test_include_readmes_true_explicit` | PASS |
| `test_include_readmes_false_removes_readmes` | PASS |
| `test_include_readmes_false_preserves_agent_rules` | PASS |
| `test_include_readmes_false_preserves_copilot_instructions` | PASS |
| `test_only_readme_md_deleted_case_sensitive` | PASS |
| `test_missing_readme_files_do_not_raise` | PASS |

**8 / 8 passed**

### Tester edge-case suite (`test_ins023_tester_edge_cases.py`)

| Test | Result |
|------|--------|
| `TestDeeplyNestedReadme::test_readme_three_levels_deep_is_removed` | PASS |
| `TestDeeplyNestedReadme::test_readme_four_levels_deep_is_removed` | PASS |
| `TestDeeplyNestedReadme::test_non_readme_files_in_deep_dirs_survive` | PASS |
| `TestReadmeInGithubDir::test_readme_in_github_root_removed` | PASS |
| `TestReadmeInGithubDir::test_copilot_instructions_survive_after_github_readme_removed` | PASS |
| `TestExactNameMatchOnly::test_readme_dev_md_survives` | PASS |
| `TestExactNameMatchOnly::test_readme_rst_survives` | PASS |
| `TestExactNameMatchOnly::test_readme_txt_survives` | PASS |
| `TestExactNameMatchOnly::test_myreadme_md_survives` | PASS |
| `TestReadonlyReadme::test_readonly_readme_does_not_crash_project_creation` | **PASS** ✓ |
| `TestSymlinkReadme::test_symlink_readme_removed` | SKIPPED (Windows — admin required) |
| `TestSymlinkReadme::test_symlink_readme_windows_skipped_gracefully` | PASS |
| `TestCaseSensitivity::test_readme_md_exact_case_deleted` | PASS |
| `TestCaseSensitivity::test_readme_lowercase_variant_survives_on_case_sensitive_fs` | SKIPPED (Windows case-insensitive FS) |

**12 passed, 2 skipped** (TST-2100)

---

## Acceptance Criteria Check

| AC | Description | Met? |
|----|-------------|------|
| AC-3 | `create_project` accepts `include_readmes`; when False all README.md files removed | ✓ PASS |
| AC-4 | All other template files remain intact | ✓ PASS |
| AC — BUG-105 | Read-only README.md does not crash project creation | ✓ PASS (Iteration 2 fix) |

---

## Bugs Found

None new. BUG-105 is now **Closed** (fixed in this iteration).

---

## Verdict

**PASS — mark WP as Done**
