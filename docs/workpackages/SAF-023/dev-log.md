# Dev Log — SAF-023: Block get_errors for Restricted Zone Paths

## Status
In Progress → Review

## WP Summary
Add `get_errors` to the security gate's tool handling. When `get_errors` is called
with `filePaths` targeting restricted zone files, the gate returns "deny". When
called without `filePaths` or with project-folder paths only, returns "allow".

## Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py`
- `templates/coding/.github/hooks/scripts/security_gate.py` (sync)
- `docs/workpackages/workpackages.csv` (status update)
- `docs/test-results/test-results.csv` (test log)

## Implementation

### Changes to security_gate.py

1. **`_EXEMPT_TOOLS`** — Added `"get_errors"` to the set so it passes the unknown-tool
   deny guard in `decide()`.

2. **`validate_get_errors()`** — New function (SAF-023) that validates `get_errors`
   tool calls:
   - Extracts `filePaths` from `tool_input` (the VS Code hook nested format) or
     falls back to the top-level dict (test/flat format).
   - No `filePaths` key or empty array → **allow** (VS Code scopes automatically).
   - `filePaths` is not a list → **deny** (fail closed, unexpected type).
   - Each element must be a non-empty string; zone-checks each path via
     `zone_classifier.classify()`.
   - If ANY path is in a "deny" zone → **deny** the entire call.
   - All paths pass zone check → **allow**.

3. **`decide()`** — Added early dispatch for `get_errors` before the generic
   `_EXEMPT_TOOLS` fallback block (matching the pattern used by `grep_search`,
   `semantic_search`, and `multi_replace_string_in_file`).

### Hash Update
After both files are modified, `update_hashes.py` is run to regenerate
`_KNOWN_GOOD_GATE_HASH` so the integrity check passes.

## Tests Written
- `tests/SAF-023/test_saf023_get_errors.py` — unit, security, bypass, cross-platform tests

## Decisions
- `filePaths` absent or empty → allow: The tool without paths means VS Code audits
  what it considers relevant; there is nothing for the gate to restrict.
- `filePaths` non-list type → deny (fail closed): unexpected shape indicates a
  malformed or adversarial call.
- Zone "ask" paths → deny: Only explicit project folder paths (zone "allow") and
  the no-paths variant are confirmed safe per WP requirements.
- Early dispatch pattern: consistent with all other special-case tools in `decide()`.
