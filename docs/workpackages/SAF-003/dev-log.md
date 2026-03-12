# Dev Log — SAF-003

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Close the grep_search and semantic_search bypass vectors identified in audit
findings 2 and 3. Specifically:

- Validate `includePattern` and `includeIgnoredFiles` parameters on `grep_search`
  calls to prevent the tool from searching inside `.github/`, `.vscode/`, or
  `NoAgentZone/`.
- Handle `semantic_search` explicitly: since it has no path restriction parameter
  it always requires human approval ("ask") to prevent automated exposure of
  protected file content.
- Block `../` traversal attempts hidden inside any search parameter.

## Implementation Summary

All changes are confined to
`Default-Project/.github/hooks/scripts/security_gate.py`.

### New helpers

| Function | Purpose |
|----------|---------|
| `_is_truthy_flag(value)` | Returns True for bool True, string "true" (any case), or int 1. Used to check `includeIgnoredFiles`. |
| `_validate_include_pattern(pattern, ws_root)` | Normalizes a glob pattern, checks for remaining `..` traversal sequences, and delegates zone membership to `zone_classifier.classify()`. Returns "deny" or "allow". |
| `validate_grep_search(data, ws_root)` | Full validation for `grep_search`: denies if `includeIgnoredFiles` is truthy or if `includePattern` targets a deny zone or contains traversal. Falls through to the standard path zone check for any explicit `filePath` field. |
| `validate_semantic_search(data, ws_root)` | Always returns "ask". `semantic_search` indexes the entire workspace with no path restriction; every call requires human review to prevent automated leakage. |

### Changes to `decide()`

Two new checks added **before** the `_EXEMPT_TOOLS` block:

```python
if tool_name == "semantic_search":
    return validate_semantic_search(data, ws_root)
if tool_name == "grep_search":
    return validate_grep_search(data, ws_root)
```

`grep_search` and `semantic_search` remain in `_EXEMPT_TOOLS` for documentation
purposes, but those entries are now dead code — the explicit SAF-003 handlers
always fire first.

### Parameter extraction

Both `validate_grep_search` and the internal `_param()` helper support the two
call formats seen in tests and in live VS Code hooks:

- **Flat format**: parameters at the top level of the JSON object.
- **Nested format**: parameters inside `tool_input` dict (VS Code hook format).

The `tool_input` value always takes precedence, with a fallback to the top-level
key.

### Path traversal detection

`_validate_include_pattern` calls `zone_classifier.normalize_path()` before
checking for `..`. This resolves resolvable traversal sequences (e.g.
`project/../.github/**` → `.github/**`, caught by zone check) and leaves
unresolvable ones (e.g. `../../etc/**`) still containing `..` for the explicit
traversal guard.

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — added SAF-003
  search tool validation helpers and wiring in `decide()`.

## Tests Written

All 42 tests live in `tests/SAF-003/test_saf003_tool_parameter_validation.py`.

| Group | Test IDs | Count |
|-------|----------|-------|
| `_is_truthy_flag` unit tests | TST-269 – TST-277 | 9 |
| `_validate_include_pattern` unit tests | TST-278 – TST-284 | 7 |
| `validate_grep_search` unit tests | TST-285 – TST-294 | 10 |
| `validate_semantic_search` unit tests | TST-295 – TST-297 | 3 |
| Security protection tests | TST-298 – TST-300 | 3 |
| Security bypass-attempt tests | TST-301 – TST-307 | 7 |
| Integration (`decide()`) tests | TST-308 – TST-312 | 5 |
| Cross-platform tests | TST-313 – TST-314 | 2 |

## Known Limitations

- `semantic_search` is effectively restricted to user-supervised calls
  ("ask"). This may require user approval for every semantic search. If the
  team decides that certain semantic searches are safe, a future WP (e.g.
  SAF-003b) could add a more nuanced policy.
- The `includePattern` check uses `zone_classifier.classify()` which normalizes
  the glob string as if it were a plain path. Exotic glob features (e.g.
  `{.github,.vscode}`) are not explicitly expanded; however the zone_classifier
  Method 2 regex scan (`/(\.github|\.vscode|noagentzone)(/|$)`) still catches
  the deny-zone names within the raw pattern string.
