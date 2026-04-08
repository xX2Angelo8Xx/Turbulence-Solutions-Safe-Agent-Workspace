# Dev Log — SAF-079: Allow workspace-internal navigation

## Status
Review

## Assigned To
Developer Agent

## Date
2026-04-08

---

## ADR Check (Step 0)

Reviewed `docs/decisions/index.jsonl`. Relevant ADRs:

- **ADR-008** (Tests Must Track Current Codebase State): Test files created under `tests/SAF-079/` track the updated `_check_nav_path_arg` and `push-location` allowlist entry.
- **ADR-011** (Drop settings.json from Security Gate Integrity Hash): Hash update was performed via `update_hashes.py` after code changes. No conflict.
- No ADR directly governs navigation-scope rules; this WP establishes new behavior.

---

## Implementation Summary

### Problem
Navigation commands (`cd`, `set-location`, `sl`) used `_check_path_arg()` to validate path arguments. That function resolves relative paths against `ws_root`, meaning `cd ..` from the project folder resolved to the *parent* of `ws_root`, which is outside the workspace → always denied. `push-location` was absent from the allowlist entirely.

### Changes Made

#### 1. `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

**A. Added `push-location` to `_COMMAND_ALLOWLIST`** (Category H — Navigation):
```python
"push-location": CommandRule(
    path_args_restricted=True, allow_arbitrary_paths=False, ...
)
```

**B. Added `_check_nav_path_arg()` function** (after `_check_workspace_path_arg`):
- Denies `$`-containing tokens.
- Denies tokens matching deny-zone bare names (`.github`, `.vscode`, `noagentzone`) even when they are not path-like by `_is_path_like`'s definition.
- For path-like tokens: tries `_check_workspace_path_arg()` first (workspace-root resolution).
- If that fails for a relative path: project-folder fallback — resolves the token against `ws_root/<project_dir>/` and checks if the resolved destination is within workspace root and not a deny zone. This allows `cd ..` from the project folder to reach `ws_root`.

**C. Added `_NAV_VERBS` frozenset** (between `_PROJECT_FALLBACK_VERBS` and `_DELETE_PROJECT_FALLBACK_VERBS`):
```python
_NAV_VERBS: frozenset[str] = frozenset({"cd", "set-location", "sl", "push-location"})
```

**D. Modified `_validate_args()` step 5**:
For nav verbs, ALL non-flag args are zone-checked via `_check_nav_path_arg()` (bypassing the `_is_path_like` gate). This catches bare directory names like `noagentzone` which have no slashes or dot-prefix but are still valid navigation destinations.

#### 2. `templates/clean-workspace/.github/hooks/scripts/security_gate.py`
Copied byte-for-byte from agent-workbench after every code change + hash update.

#### 3. Hash update
`update_hashes.py` run after each iteration. Final hash: `4f2b0c9fe18694af4d0ad3f25259d4daaba8ec7ca018c58c653bc99aa15ff731` → re-synced → updated to current value after final sync.

#### 4. MANIFEST.json
`generate_manifest.py` run for both templates after final code state.

---

## Leo Bug Report Investigation

Reviewed `docs/bugs/User-Bug-Reports/Reports-v3.4.n/Leo-BUGREPORT-ACCESS-DENIAL-v3.4.0.md`.

**Assessment: The root cause is separate from SAF-079.**

The Leo report describes:
1. File write/edit operations being denied even in allowed project paths.
2. Fallback attempts (e.g. terminal-based edits) also being denied, incrementing the
   denial counter each time.
3. Session hard-lock at 20 denials blocking all tools including `edit_file`,
   diagnostics, and completion signalling.

SAF-079 fixes navigation false denials (`cd ..` from the project folder), which
indirectly reduces unnecessary counter increments during agent navigation. However,
the Leo report's primary failure mode — edit/write denials on allowed paths — is
**not addressed by this WP**. The root cause appears to be a write-tool zone-check
false positive that requires a separate investigation/fix (likely a FIX-xxx WP
targeting write-tool path resolution or denial counter policy adjustment).

SAF-079 is a partial mitigation: fewer nav denials → fewer counter increments →
less risk of premature lock. But the core write-denial issue and lock escalation
pattern require dedicated fixes.

---

## Tests Written

`tests/SAF-079/test_saf079_nav.py` — 26 tests:

- push-location allowlist: project subdir allowed, absolute inside workspace allowed,
  .github denied, .vscode denied, ../.. denied
- cd/sl/set-location `..`: all allowed (workspace root via project-folder fallback)
- cd `../..`: denied (above workspace root)
- Deny zones: cd .github, cd .vscode, cd noagentzone, cd NoAgentZone all denied
- Absolute paths: inside workspace allowed, workspace root allowed, outside denied
- `_check_nav_path_arg` unit tests: dollar token, non-path token, `..`, `../..`,
  workspace root, inside workspace, outside, .github, noagentzone

Test run: 26 passed via `run_tests.py --wp SAF-079 --type Unit` → logged as TST-2782.

---

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `templates/clean-workspace/.github/hooks/scripts/security_gate.py`
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json`
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json`
- `tests/SAF-079/__init__.py`
- `tests/SAF-079/test_saf079_nav.py`
- `docs/workpackages/workpackages.jsonl` (Status → Review)
- `docs/workpackages/SAF-079/dev-log.md` (this file)
- `docs/test-results/test-results.jsonl` (TST-2782 appended)

---

## Known Limitations

- Bare directory names other than the three protected zones are not zone-checked
  for nav verbs (e.g. `cd mydir` is allowed regardless of what `mydir` resolves
  to). This matches the WP scope; deeper zone-enforcement for arbitrary directory
  names is out of scope.
- `pop-location` (PowerShell) is not in the allowlist; it takes no path args
  and is a separate WP concern.
