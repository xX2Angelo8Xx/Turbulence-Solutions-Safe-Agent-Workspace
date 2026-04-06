# Dev Log — FIX-116: Allow file_search for .github/ subdirectories

**WP ID:** FIX-116  
**Branch:** FIX-116/file-search-github-allow  
**Assigned To:** Developer Agent  
**Started:** 2026-04-06

---

## ADR Review

No directly related ADRs exist for `file_search` or SAF-043/SAF-055. ADR-011 (Drop settings.json from Security Gate Integrity Hash) is related to the security gate but does not conflict with this fix. Acknowledged.

## Bug Fixed

**BUG-195** — `file_search` over-blocks `.github/` paths.  
`file_search` with a query targeting `.github/agents/README.md` is denied, but `read_file` for the same path is allowed. The AGENT-RULES only specifies `NoAgentZone` as blocked for `file_search`.

## Root Cause

In `validate_file_search()` (security_gate.py), the deny-zone name check blanket-denies any query containing `.github`:

```python
for zone_name in (".github", ".vscode", "noagentzone"):
    if zone_name in query_lower:
        return "deny"
```

This is over-restrictive: `read_file` and `list_dir` are allowed for `.github/agents/`, `.github/skills/`, `.github/prompts/`, and `.github/instructions/` via `_GITHUB_READ_ALLOWED_RE`, but `file_search` was not given the same exemption.

## Implementation

### File Changed:
`templates/agent-workbench/.github/hooks/scripts/security_gate.py`

### Change:
Split the `.github` check out of the blanket deny loop in `validate_file_search()`. If `.github` appears in the query, the function now checks whether `_GITHUB_READ_ALLOWED_RE` matches the normalized query. If it matches (one of the four whitelisted subdirectories), the deny is skipped. If it does not match (e.g., `.github/hooks/`, `.github/workflows/`), the query is denied as before.

`.vscode` and `noagentzone` remain unconditional denies.

The updated hash is re-embedded after the code change by running `scripts/update_hashes.py`.

### Security Rationale:
- `_GITHUB_READ_ALLOWED_RE` ensures only the four explicitly whitelisted subdirectories are matched — the pattern uses a trailing `(?:/|$)` that prevents prefix attacks (e.g., `.github/agents-extra/`).
- `.github/hooks/` (where the security gate itself lives) remains denied.
- The existing `_READ_ONLY_TOOLS` guard in `decide()` already ensures only `read_file` / `list_dir` can access whitelisted `.github/` paths at the zone check level. `file_search` has its own early-return path via `validate_file_search()` so this is consistent.

## Tests Written

- `tests/FIX-116/test_fix116_file_search_github.py`
  - Regression test: `.github/agents/README.md` query → allow
  - Regression test: all four whitelisted subdirectories → allow
  - Security test: `.github/hooks/` query → deny (gate code still blocked)
  - Security test: `.github/workflows/` query → deny (non-whitelisted)
  - Security test: `.vscode/` query → deny (unchanged)
  - Security test: `noagentzone/` query → deny (unchanged)
  - Edge case: wildcard glob `.github/agents/**` → allow
  - Edge case: absolute path to whitelisted dir → allow
  - Edge case: absolute path to `.github/hooks/` → deny

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `docs/workpackages/FIX-116/dev-log.md` (this file)
- `docs/workpackages/workpackages.jsonl`
- `docs/bugs/bugs.jsonl` (BUG-195 Fixed In WP → FIX-116)
- `tests/FIX-116/test_fix116_file_search_github.py`
