# SAF-055 — Dev Log: Whitelist .github/ agent-facing subdirectories read-only

## Status
Review

## Assigned To
Developer Agent

## WP Summary
Allow read-only access to `.github/agents/`, `.github/skills/`, `.github/prompts/`, and `.github/instructions/` in `security_gate.py`. Write operations to any `.github/` path remain denied. `.github/hooks/` (security gate code) remains fully denied for both read and write.

---

## Implementation Plan

1. Add `_GITHUB_READ_ALLOWED` constant (frozenset of allowed subdirectory prefixes) to `security_gate.py`.
2. Add `_READ_ONLY_TOOLS` constant (frozenset of read-only tool names) to `security_gate.py`.
3. Add compiled regex `_GITHUB_READ_ALLOWED_RE` for efficient path matching.
4. In `decide()`, after zone check returns "deny" in the exempt-tool path, add a conditional that returns "allow" when:
   - `tool_name in _READ_ONLY_TOOLS`
   - The normalized path matches `_GITHUB_READ_ALLOWED_RE` (i.e., targets agents/, skills/, prompts/, or instructions/)
5. Run `update_hashes.py` to update integrity hashes.
6. Write and run tests.

---

## Implementation Notes

### Design Decisions
- `_READ_ONLY_TOOLS` is intentionally narrow (`read_file`, `Read`, `list_dir`). Write tools are handled separately by `validate_write_tool()` which denies all `.github/` paths, so this is defense-in-depth.
- `_GITHUB_READ_ALLOWED_RE` pattern `(?:^|/)\.github/(?:agents|skills|prompts|instructions)(?:/|$)` handles both relative paths (`.github/agents/foo.md`) and absolute paths (`c:/workspace/.github/agents/foo.md`).
- Path traversal is defeated by `posixpath.normpath` in `normalize_path()`, which resolves `..` sequences before the regex check.
- `.github/hooks/` (and any unknown subdirectory) remains denied because `hooks` is not listed in the allowed alternation.

### Bugs Fixed
- BUG-138: `copilot-instructions.md` wasting Block 1 (now agents can read `.github/instructions/`)
- BUG-139: Skill files inaccessible (now agents can read `.github/skills/`)

---

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — Added `_GITHUB_READ_ALLOWED`, `_READ_ONLY_TOOLS`, `_GITHUB_READ_ALLOWED_RE`, updated `decide()`.

---

## Tests Written
- `tests/SAF-055/test_saf055_github_read_whitelist.py`
  - `test_read_file_agents_allowed` — read_file targeting .github/agents/ returns allow
  - `test_read_file_skills_allowed` — read_file targeting .github/skills/ returns allow
  - `test_read_file_prompts_allowed` — read_file targeting .github/prompts/ returns allow
  - `test_read_file_instructions_allowed` — read_file targeting .github/instructions/ returns allow
  - `test_list_dir_agents_allowed` — list_dir targeting .github/agents/ returns allow
  - `test_list_dir_instructions_allowed` — list_dir targeting .github/instructions/ returns allow
  - `test_read_file_deep_agents_allowed` — read_file targeting nested file in .github/agents/ returns allow
  - `test_write_to_agents_denied` — create_file targeting .github/agents/ returns deny
  - `test_replace_string_in_agents_denied` — replace_string_in_file targeting .github/agents/ returns deny
  - `test_read_hooks_denied` — read_file targeting .github/hooks/ returns deny
  - `test_list_dir_hooks_denied` — list_dir targeting .github/hooks/ returns deny
  - `test_read_github_root_denied` — read_file targeting .github/ root returns deny
  - `test_read_unknown_github_subdir_denied` — read_file targeting .github/other/ returns deny
  - `test_traversal_attempt_denied` — read_file with traversal .github/agents/../hooks/ returns deny
  - `test_absolute_path_agents_allowed` — read_file with absolute path to .github/agents/ allowed
  - `test_absolute_path_hooks_denied` — read_file with absolute path to .github/hooks/ denied

---

## Iteration History
(none yet)
