# DOC-001 — Dev Log: Add Placeholder System to Template Files

## Status
In Progress → (will update to Review after tests pass)

## Assigned To
Developer Agent

## Date
2026-03-17

---

## Implementation Plan

1. Add `replace_template_placeholders(project_dir, project_name)` to `src/launcher/core/project_creator.py`.
2. Call it from `create_project()` after copytree and internal folder rename.
3. Write tests covering placeholder replacement, non-.md files untouched, binary files skipped.

---

## Implementation Summary

### Function: `replace_template_placeholders`

- Walks all files under `project_dir` recursively.
- Processes only files with `.md` extension (text-based template files).
- Replaces `{{PROJECT_NAME}}` with `project_name` and `{{WORKSPACE_NAME}}` with `TS-SAE-{project_name}`.
- Skips any file where UTF-8 decoding fails (binary safety guard).
- Only writes back if content changed (idempotent — no unnecessary I/O).

### Integration

- `create_project()` calls `replace_template_placeholders(target, folder_name)` after copytree and the internal folder rename.

---

## Files Changed

- `src/launcher/core/project_creator.py` — added `replace_template_placeholders`, called from `create_project()`
- `tests/DOC-001/test_doc001_placeholder.py` — unit tests

---

## Tests Written

| Test | Description |
|------|-------------|
| `test_md_placeholder_replaced` | `.md` file with `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` is replaced correctly |
| `test_non_md_untouched` | `.txt` file with placeholder tokens is left unchanged |
| `test_binary_file_skipped` | Binary file containing placeholder bytes is not corrupted |
| `test_nested_md_replaced` | Placeholder in nested subdirectory `.md` file is replaced |
| `test_idempotent` | Running replacement twice produces the same result |
| `test_no_placeholder_untouched` | `.md` file without placeholders is written back only if changed (content same) |

---

## Known Limitations / Notes

- Only `.md` files are processed. If future WPs need `.py` or other extensions processed, a parameter can be added.
- Files must be UTF-8 (or ASCII-compatible) to be processed; non-UTF-8 files are silently skipped.
