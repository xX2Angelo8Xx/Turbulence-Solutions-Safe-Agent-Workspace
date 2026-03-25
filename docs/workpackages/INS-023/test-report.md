# Test Report — INS-023: Skip README files during project creation

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Branch:** `INS-023/skip-readmes`  
**Verdict:** **FAIL — return to Developer**

---

## Summary

The core implementation is correct and well-structured. The `os.walk` + `os.unlink` loop
satisfies the primary requirement (all `README.md` files removed after `copytree`) and
the exact-name match protects `AGENT-RULES.md`, `copilot-instructions.md`, and other
`.md` files.

One edge case was missed: **read-only `README.md` files cause an unhandled
`PermissionError` that crashes the entire `create_project()` call on Windows.**

---

## Code Review

File reviewed: `src/launcher/core/project_creator.py`

### What is correct

- `import os` added at the top — appropriate.
- `os.walk(target)` visits every subdirectory recursively — all `README.md` files at
  any nesting depth are found and deleted (verified by Tester tests).
- `filename == "README.md"` is a case-sensitive exact match — `AGENT-RULES.md`,
  `copilot-instructions.md`, `README.rst`, `README.txt`, `README-DEV.md`, and all
  other variants are left untouched.
- `except FileNotFoundError: pass` correctly handles the race where the file was
  already absent in the template.
- The loop runs after `replace_template_placeholders` — no placeholders are left in
  the files that are about to be deleted.
- `app.py` was correctly left unchanged (GUI-022 wiring already in place).
- `include_readmes` parameter defaults to `True` — fully backwards-compatible.

### Defect found

```python
# src/launcher/core/project_creator.py  lines 88-93
if not include_readmes:
    for dirpath, _dirnames, filenames in os.walk(target):
        for filename in filenames:
            if filename == "README.md":
                try:
                    os.unlink(os.path.join(dirpath, filename))
                except FileNotFoundError:    # <-- BUG: too narrow
                    pass
```

`os.unlink()` raises `PermissionError` (Windows: `[WinError 5] Access is denied`)
when the target file carries the read-only attribute. `shutil.copytree()` preserves
file permission bits from the template — so any read-only `README.md` in the template
produces a read-only `README.md` in the destination that cannot be deleted. The
`except FileNotFoundError` clause does **not** catch `PermissionError`, so the error
propagates and aborts `create_project()` entirely.

**Bug reference:** BUG-105

---

## Tests Run

### Developer suite

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

**8 / 8 passed** (TST-2097)

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
| `TestReadonlyReadme::test_readonly_readme_does_not_crash_project_creation` | **FAIL** |
| `TestSymlinkReadme::test_symlink_readme_removed` | SKIPPED (Windows — admin required) |
| `TestSymlinkReadme::test_symlink_readme_windows_skipped_gracefully` | PASS |
| `TestCaseSensitivity::test_readme_md_exact_case_deleted` | PASS |
| `TestCaseSensitivity::test_readme_lowercase_variant_survives_on_case_sensitive_fs` | SKIPPED (Windows case-insensitive FS) |

**11 passed, 1 failed, 2 skipped** (TST-2098)

---

## Failure Detail

```
FAILED tests/INS-023/test_ins023_tester_edge_cases.py::TestReadonlyReadme::test_readonly_readme_does_not_crash_project_creation

PermissionError: [WinError 5] Access is denied:
  '...\dest\TS-SAE-EdgeTest\README.md'

  src\launcher\core\project_creator.py:89: in create_project
      os.unlink(os.path.join(dirpath, filename))
```

**Root cause:** `except FileNotFoundError` is too narrow. `PermissionError` (a sibling
of `FileNotFoundError` under `OSError`) is not caught.

---

## Required Fix

In `src/launcher/core/project_creator.py`, change the `except` clause from:

```python
except FileNotFoundError:
    pass
```

to:

```python
except OSError:
    pass
```

`OSError` is the base class of both `FileNotFoundError` (file absent) and
`PermissionError` (file read-only / access denied). Widening the catch to `OSError`
makes the deletion robust against both failure modes without masking unrelated errors
from the `os.walk` call itself.

**Alternative (stronger):** Make the file writable before unlinking:

```python
try:
    os.chmod(os.path.join(dirpath, filename), stat.S_IWRITE)
    os.unlink(os.path.join(dirpath, filename))
except OSError:
    pass
```

This guarantees deletion even if the read-only flag was intentionally set. Recommend
the `OSError` catch-only variant (simpler) unless the project has a policy of always
forcing deletion.

---

## Acceptance Criteria Check (US-039)

| AC | Description | Met? |
|----|-------------|------|
| AC-2 | Checkbox state persisted in user settings | Not in scope for this WP (GUI-022 / separate WP) |
| AC-3 | `create_project` accepts `include_readmes`; when False all README.md files removed | **Partial** — core logic correct but crashes on read-only README.md (BUG-105) |
| AC-4 | All other template files remain intact | PASS (AGENT-RULES.md, copilot-instructions.md, README.txt etc. all survive) |

---

## TODOs for Developer (Iteration 2)

1. **Fix BUG-105** — In `project_creator.py`, change `except FileNotFoundError: pass`
   to `except OSError: pass` on the `os.unlink` call inside the README deletion loop.

2. **Add a unit test** (or update the existing missing-README test) that creates a
   read-only `README.md` in the template, runs `create_project(include_readmes=False)`,
   and asserts:  
   - No exception is raised.  
   - The `README.md` file no longer exists in the destination directory.

3. Re-run the full test suite (`tests/INS-023/` + regression) and confirm all tests
   pass, including the new Tester edge-case file at
   `tests/INS-023/test_ins023_tester_edge_cases.py`.

---

## Bugs Logged

| Bug ID | Title | Severity | Status |
|--------|-------|----------|--------|
| BUG-105 | INS-023: PermissionError when deleting read-only README.md | Medium | Open |
