# SAF-042 — Verify and expand git command allowlist

**Developer:** Developer Agent  
**Branch:** `SAF-042/git-allowlist`  
**Started:** 2026-03-24  
**Status:** Review  

---

## Summary

Audited the git subcommand allowlist in `templates/coding/.github/hooks/scripts/security_gate.py`
(Category E — Version Control) against the 17 documented git operations required by US-036 ACs 5-6.

## Audit Findings

### Required 17 operations vs. existing allowlist

| Operation | Status before SAF-042 |
|-----------|----------------------|
| status    | ✓ present |
| log       | ✓ present |
| diff      | ✓ present |
| branch    | ✓ present |
| add       | ✓ present |
| commit    | ✓ present |
| fetch     | ✓ present |
| pull      | ✓ present |
| checkout  | ✓ present |
| **switch** | ✗ **MISSING** |
| stash     | ✓ present |
| merge     | ✓ present |
| rebase    | ✓ present |
| tag       | ✓ present |
| remote    | ✓ present |
| show      | ✓ present |
| **blame** | ✗ **MISSING** |

Two subcommands were missing: `switch` and `blame`.

### Destructive operations verification

All 5 destructive operations were and remain blocked:

| Destructive operation | Blocking mechanism |
|----------------------|-------------------|
| `push --force`       | `--force` in `denied_flags`; `("push", "--force")` in `_GIT_DENIED_COMBOS` |
| `push -f`            | `-f` in `denied_flags`; `("push", "-f")` in `_GIT_DENIED_COMBOS` |
| `reset --hard`       | `reset` not in `allowed_subcommands`; `("reset", "--hard")` in `_GIT_DENIED_COMBOS` |
| `filter-branch`      | `filter-branch` not in `allowed_subcommands`; `("filter-branch", "")` in `_GIT_DENIED_COMBOS` |
| `gc --force`         | `gc` not in `allowed_subcommands`; `("gc", "--force")` in `_GIT_DENIED_COMBOS` |
| `clean -f`           | `clean` not in `allowed_subcommands`; `-f` in `denied_flags`; `("clean", "-f")` in `_GIT_DENIED_COMBOS` |

## Changes Made

### `templates/coding/.github/hooks/scripts/security_gate.py`

- Added `"switch"` to the git `allowed_subcommands` frozenset (Category E)
- Added `"blame"` to the git `allowed_subcommands` frozenset (Category E)
- Updated the `notes` field to reflect full destructive operation list
- Ran `update_hashes.py` — `_KNOWN_GOOD_GATE_HASH` updated

## Tests Written

**`tests/SAF-042/test_saf042_git_allowlist.py`** — 45 tests:

- **Section 1 (17 tests):** Each of the 17 documented operations individually verified as allowed
  - Verifies `git switch` and `git blame` now work (newly added)
- **Section 2 (6 tests):** Each of the 5 destructive operations individually verified as blocked
  - `push --force`, `push -f`, `reset --hard`, `filter-branch`, `gc --force`, `clean -f`
- **Section 3 (22 tests):** Edge cases
  - `git push` without `--force` → allowed
  - `git reset` without `--hard` → denied (reset not in allowlist)
  - `git clean` without flags → denied (clean not in allowlist)
  - `git gc` without `--force` → denied (gc not in allowlist)
  - `git switch -c <branch>` → allowed (`-c` is not in `denied_flags`)
  - `git push --force-with-lease` → allowed (distinct flag, not `--force`)
  - `git blame -L 1,10 <file>` → allowed
  - Various common git commands with flags documented as working

## Test Results

- TST-2058: 45 passed, 0 failed — `tests/SAF-042/` (Windows 11 + Python 3.11)
- Full regression: 155 passed (SAF-042 + SAF-041 + SAF-040), 2 xfailed (expected)
- Pre-existing failures unrelated to this WP: SAF-022, SAF-010, INS-019 (yaml module missing for INS-013–INS-017 suite)

## Files Changed

- `templates/coding/.github/hooks/scripts/security_gate.py` — added `switch`, `blame` to git allowlist
- `docs/workpackages/workpackages.csv` — status updated
- `tests/SAF-042/test_saf042_git_allowlist.py` — new test file (45 tests)
- `tests/SAF-042/__init__.py` — new empty init file
- `docs/workpackages/SAF-042/dev-log.md` — this file
