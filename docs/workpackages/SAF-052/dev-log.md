# SAF-052 Dev Log — Add get_changed_files to security gate tool sets

**WP ID:** SAF-052  
**Branch:** SAF-052/get-changed-files  
**Assigned To:** Developer Agent  
**Status:** In Progress  
**Started:** 2026-03-26  

## Objective

Add `get_changed_files` to `_ALWAYS_ALLOW_TOOLS` in
`templates/agent-workbench/.github/hooks/scripts/security_gate.py`.

`get_changed_files` is a read-only VS Code deferred tool that lists git-modified
files in the current workspace. It carries no file-system path arguments and does
not execute arbitrary commands. Without this change it falls through to the
unknown-tool deny path and is always blocked.

## Bugs Fixed

- **BUG-132** — `get_changed_files` not in security gate tool sets — always denied.

## References

- User Story: US-052
- Bug: BUG-132
- v3.2.2 feedback Section 3.3

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Added `"get_changed_files"` to `_ALWAYS_ALLOW_TOOLS` frozenset (SAF-052) |
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Updated `_KNOWN_GOOD_GATE_HASH` via `update_hashes.py` |

### Implementation Details

Added `"get_changed_files"` to the `_ALWAYS_ALLOW_TOOLS` frozenset. This set is
checked first in `decide()` — tools in it bypass all zone checks and immediately
return `"allow"`. This is correct because:

1. `get_changed_files` is a read-only query tool (lists changed files from git).
2. It takes no file-system path arguments that could be zone-check attack vectors.
3. It does not execute arbitrary commands.

After modifying `security_gate.py`, ran `update_hashes.py` to recompute and
re-embed the `_KNOWN_GOOD_GATE_HASH` constant.

## Tests Written

**Location:** `tests/SAF-052/`

| Test | Description |
|------|-------------|
| `test_get_changed_files_in_always_allow` | Verifies `get_changed_files` is in `_ALWAYS_ALLOW_TOOLS` |
| `test_get_changed_files_decide_returns_allow` | Verifies `decide({"tool_name": "get_changed_files"}, ws_root)` returns `"allow"` |
| `test_get_changed_files_not_in_exempt_tools` | Confirms placement in correct set |
| `test_hash_verification_passes` | Verifies `_KNOWN_GOOD_GATE_HASH` matches actual gate hash |
| `test_decide_unknown_tool_still_denied` | Regression: unknown tools still denied |

## Decisions

- Added to `_ALWAYS_ALLOW_TOOLS` (not `_EXEMPT_TOOLS`) because the tool has no
  path argument that needs zone-checking — always-allow is the correct tier.
- No changes needed to the `decide()` body — the existing early-exit at line
  `if tool_name in _ALWAYS_ALLOW_TOOLS: return "allow"` handles it.

## Iteration History

### Iteration 1 (2026-03-26)

Initial implementation. All tests pass.
