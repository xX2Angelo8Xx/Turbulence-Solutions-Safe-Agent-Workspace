# Dev Log — SAF-043

**Developer:** Developer Agent
**Date started:** 2026-03-24
**Iteration:** 1

## Objective

Update `security_gate.py` to ensure `file_search` results are scoped to the
project folder only.

1. Extract the `query` parameter from the `file_search` tool payload.
2. Deny if the query references deny-zone directories (`.github`, `.vscode`,
   `NoAgentZone`) or contains path traversal sequences (`..`).
3. Deny if the query contains a wildcard that could expand to a deny zone
   (reuses `_wildcard_prefix_matches_deny_zone`).
4. Deny if the query is (or starts with) an absolute path that resolves
   outside the project folder.
5. Allow otherwise — VS Code `search.exclude` settings prevent deny-zone
   entries from appearing in file_search results.
6. Verify `search.exclude` in the VS Code settings template already covers
   `.github`, `.vscode`, `NoAgentZone` (confirmed: it does).

Satisfies AC 1 of US-037.

## Implementation Summary

### Files Changed

- `templates/coding/.github/hooks/scripts/security_gate.py`
  - Added `validate_file_search(data, ws_root)` function (SAF-043 section).
  - Updated `decide()`: replaced inline `file_search` block (FIX-021 comment)
    with a call to `validate_file_search()`.
  - Existing `_KNOWN_GOOD_GATE_HASH` updated via `update_hashes.py`.

### VS Code Settings Verification

`templates/coding/.vscode/settings.json` already contains correct
`search.exclude` entries (added by SAF-022):

```json
"search.exclude": {
  ".github": true,
  ".vscode": true,
  "**/NoAgentZone": true
}
```

No changes required.

### Design Decisions

- **Fail closed:** Any query that cannot be safely classified is allowed only
  if VS Code's `search.exclude` will handle it. Absolute paths that zone-check
  to "deny" are blocked by the gate.
- **`_wildcard_prefix_matches_deny_zone` reuse:** The existing wildcard bypass
  check from SAF-020 already handles patterns like `.g*/**` — no new logic
  needed for that case.
- **Relative globs allowed:** Patterns like `**/*.py` or `src/**` do not
  target an absolute path outside the project; VS Code scopes these to the
  workspace folder and `search.exclude` filters denied zones.

## Tests Written

- `tests/SAF-043/test_saf043_file_search.py`
  - `test_allow_simple_filename` — plain filename query allowed
  - `test_allow_glob_pattern` — standard glob allowed
  - `test_allow_no_query` — missing query field allowed
  - `test_deny_github_in_query` — `.github` in query denied
  - `test_deny_vscode_in_query` — `.vscode` in query denied
  - `test_deny_noagentzone_in_query` — `noagentzone` in query denied
  - `test_deny_traversal_in_query` — `..` traversal denied
  - `test_deny_absolute_path_outside_project` — absolute path outside project denied
  - `test_allow_absolute_path_inside_project` — absolute path inside project allowed
  - `test_deny_wildcard_matching_deny_zone` — `.g*/**` wildcard denied
  - `test_deny_case_insensitive_zone_name` — `.GITHUB` denied (case-insensitive)
  - `test_allow_nested_glob` — `src/**/*.py` allowed
  - `test_decide_file_search_routes_to_validator` — integration: decide() calls validate_file_search
  - `test_decide_file_search_deny_via_decide` — integration: denied query denied by decide()
  - `test_deny_github_in_nested_tool_input` — VS Code nested format handled
  - `test_allow_nested_tool_input_no_path_issue` — clean nested format allowed

## Known Limitations

None.
