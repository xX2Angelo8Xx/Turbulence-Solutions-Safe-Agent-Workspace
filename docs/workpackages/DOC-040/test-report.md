# DOC-040 Test Report — Add .github/version file to template

**Tester:** Tester Agent  
**Date:** 2026-03-31  
**Verdict:** PASS

---

## 1. Implementation Review

### Template file
`templates/agent-workbench/.github/version` exists and contains exactly `{{VERSION}}` (one line, no trailing newline issues). ✓

### `project_creator.py` changes
- `from launcher.config import VERSION` import is present. ✓
- `replace_template_placeholders()` signature correctly accepts optional `version: str = VERSION`. ✓
- `candidates` list is built as `list(project_dir.rglob("*.md")) + list(project_dir.rglob("version"))` — covers both `.md` files and bare `version` files. ✓
- Replacement logic: `{{PROJECT_NAME}}`, `{{WORKSPACE_NAME}}`, `{{VERSION}}` all replaced in a single pass per file. ✓
- Idempotency check: file only written if `updated != original`. ✓
- Binary-safe: `UnicodeDecodeError` and `OSError` are caught and skipped. ✓
- The `create_project()` function calls `replace_template_placeholders(target, folder_name)` which now carries the version replacement forward. ✓

### Security review
- No path traversal risk in the version file content (it is read from a controlled template, not user-supplied).
- The `rglob("version")` call is scoped to the project directory — no filesystem escape possible.
- No secrets, credentials, or external URLs introduced.

---

## 2. Developer Tests (TST-2366)

| Test | Result |
|---|---|
| `test_agentworkbench_version_file_exists` | PASS |
| `test_agentworkbench_version_file_contains_placeholder` | PASS |
| `test_replace_placeholders_version_replaced` | PASS |
| `test_replace_placeholders_version_not_placeholder` | PASS |
| `test_replace_placeholders_version_is_semver` | PASS |
| `test_replace_placeholders_md_version_replaced` | PASS |
| `test_replace_placeholders_custom_version` | PASS |
| `test_replace_placeholders_all_tokens` | PASS |

**8 passed, 0 failed.**

---

## 3. Tester Edge-Case Tests (TST-2367)

Added `tests/DOC-040/test_doc040_edge_cases.py` with 8 additional tests:

| Test | Scenario | Result |
|---|---|---|
| `test_multiple_version_placeholders_all_replaced` | `{{VERSION}}` appears 3× in one file — all replaced | PASS |
| `test_empty_version_file_no_placeholder` | Empty (0-byte) version file — no crash, file stays empty | PASS |
| `test_no_placeholder_file_not_rewritten` | File without placeholder — mtime unchanged (idempotency) | PASS |
| `test_version_file_in_deep_directory` | `version` file in deeply-nested subdirectory — found by rglob | PASS |
| `test_version_file_replacement_valid_string_not_empty` | Replaced VERSION must be non-empty and match config.VERSION | PASS |
| `test_end_to_end_create_project_version_file_written` | Full `create_project()` call — `.github/version` contains real VERSION | PASS |
| `test_version_file_content_is_semver_format` | `config.VERSION` itself matches `X.Y.Z` semver pattern | PASS |
| `test_project_name_placeholder_not_replaced_in_version_file` | `{{PROJECT_NAME}}-{{VERSION}}` in version file — both replaced | PASS |

**8 passed, 0 failed.** Total DOC-040 tests: **16 passed, 0 failed.**

---

## 4. Regression Suite (TST-2368)

- **Main branch baseline:** 470 failed, 7332 passed, 42 skipped, 4 xfailed, 81 errors.
- **DOC-040 branch:** 466 failed, 7343 passed, 42 skipped, 1 deselected, 4 xfailed, 81 errors.
- **Delta:** −4 failures, +11 passes vs. main. **DOC-040 introduces zero regressions.**
- All failures on the branch are pre-existing (`DOC-002`, `DOC-008`, `DOC-018`, `DOC-029`, etc.) and unrelated to the version file feature.

---

## 5. Workspace Validation

```
scripts/validate_workspace.py --wp DOC-040 → All checks passed (exit code 0)
```

---

## 6. Edge Cases Analyzed — Not Exploitable

| Scenario | Analysis |
|---|---|
| Path traversal via `rglob("version")` | Scoped to `project_dir` — no escape possible |
| `version` filename collides with other dirs | `rglob` returns files only; `if not file_path.is_file()` guard present |
| Empty VERSION constant | `test_version_file_replacement_valid_string_not_empty` catches this |
| Non-semver VERSION value | `test_version_file_content_is_semver_format` validates config.VERSION = "3.3.0" ✓ |
| Binary file named `version` | `UnicodeDecodeError` caught and skipped — no crash |

---

## 7. Verdict

**PASS** — All acceptance criteria met:
- Every newly created workspace contains `.github/version` with the launcher version string.
- Placeholder replacement is correct, idempotent, and safe.
- 16 tests pass, 0 fail.
- No regressions introduced.
