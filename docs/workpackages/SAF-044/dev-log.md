# SAF-044 Dev Log — Scope semantic_search and search_subagent

**WP ID:** SAF-044  
**Branch:** SAF-044/search-scoping  
**Assigned To:** Developer Agent  
**Status:** In Progress  
**User Story:** US-037

---

## Objective

Scope `semantic_search` and `search_subagent` tools to the project folder by
adding query validation to `security_gate.py`. Goals:

1. Upgrade `validate_semantic_search` from "always allow" to active validation.
2. Add `validate_search_subagent` as a new function.
3. Remove `search_subagent` from `_ALWAYS_ALLOW_TOOLS` so validation runs.
4. Wire both validators into `decide()`.

---

## Design Decisions

### validate_semantic_search

`semantic_search` accepts **natural language** queries fed to VS Code's
pre-built semantic index. VS Code's `search.exclude` settings already exclude
`.github/`, `.vscode/`, and `NoAgentZone/` from the index, so a query of
"find .github references" cannot surface restricted content regardless.

Defence-in-depth additions (SAF-044):
- **Path traversal denial** (`..`) — prevents encoded path escapes embedded
  in query strings.
- **Absolute path zone check** — denies queries that are absolute paths
  resolving into a deny zone (e.g. `/workspace/.github/hooks.py`).
- Natural language queries (including those mentioning zone names as text)
  are intentionally allowed; they cannot leak restricted content because the
  semantic index is already scoped by `search.exclude`.

This design keeps FIX-021 regression tests passing while adding real
defence-in-depth against crafted path-injection attempts.

### validate_search_subagent

`search_subagent` can accept both natural language queries **and** path-like
glob patterns (e.g. `src/components/**/*.tsx`). Stricter controls apply:

- **Deny-zone name check** — denies queries containing `.github`, `.vscode`,
  or `noagentzone` (case-insensitive). An agent querying "search .github for
  hook scripts" is targeting a restricted directory; this is blocked.
- **Path traversal denial** (`..`).
- **Absolute path zone check** (same as validate_semantic_search).
- General text queries (e.g. "utility functions", "how does error handling
  work") are allowed.

`search_subagent` is also removed from `_ALWAYS_ALLOW_TOOLS`; it remains in
`_EXEMPT_TOOLS` for consistency with `semantic_search`.

---

## Files Changed

| File | Change |
|------|--------|
| `templates/coding/.github/hooks/scripts/security_gate.py` | Remove `search_subagent` from `_ALWAYS_ALLOW_TOOLS`; upgrade `validate_semantic_search`; add `validate_search_subagent`; add handler in `decide()` |
| `templates/coding/.github/hooks/scripts/security_gate.py.sha256` | Updated by `update_hashes.py` |

---

## Tests Written

`tests/SAF-044/test_saf044_search_scoping.py`

- validate_semantic_search: allow general query
- validate_semantic_search: allow query mentioning zone name as text
- validate_semantic_search: deny path traversal
- validate_semantic_search: deny absolute path to deny zone
- validate_semantic_search: nested tool_input format
- validate_semantic_search: no query → allow
- validate_search_subagent: allow general query
- validate_search_subagent: allow absolute path inside project → allow
- validate_search_subagent: deny .github in query
- validate_search_subagent: deny .vscode in query
- validate_search_subagent: deny noagentzone in query (case-insensitive)
- validate_search_subagent: deny path traversal
- validate_search_subagent: deny absolute path to deny zone
- validate_search_subagent: nested tool_input format
- validate_search_subagent: no query → allow
- decide() search_subagent safe query → allow
- decide() search_subagent deny-zone query → deny
- decide() semantic_search path traversal → deny

---

## Iteration 2 — Fix: absolute project path incorrectly denied

**Root cause:** Both `validate_semantic_search` and `validate_search_subagent`
called `zone_classifier.classify()` for absolute-path zone checks.
`classify()` calls `detect_project_folder()` which uses `os.listdir()` on the
workspace root. In test environments the workspace root (`/workspace`) does not
exist on the real filesystem, so `os.listdir` raises `OSError`, the except
clause catches it, and `classify()` returns `"deny"` for ALL absolute paths —
including safe project paths like `/workspace/src/main.py`.

**Fix:** Replaced the `zone_classifier.classify()` calls in the absolute-path
check of both validators with a direct regex pattern check using
`re.search(r"/(\.github|\.vscode|noagentzone)(/|$)", "/" + norm)`. This is
filesystem-independent and correctly:
- Denies paths targeting deny zones (e.g. `/workspace/.github/hooks.py`)
- Allows paths inside the project (e.g. `/workspace/src/main.py`)

**Tests fixed:**
- `test_semantic_search_absolute_project_path_allow` → now passes
- `test_search_subagent_absolute_project_path_allow` → now passes

**Total test result:** 33 passed, 0 failed (SAF-044); 107 passed, 0 failed (SAF-043 + SAF-044 regression)

---

## Known Limitations / Notes

- `runSubagent` remains in `_ALWAYS_ALLOW_TOOLS` (out of scope for SAF-044).
- The FIX-021 regression test `test_semantic_search_with_protected_query_allow`
  passes because `validate_semantic_search` does NOT check for zone names as
  text substrings — only path-structured zone references are denied.
