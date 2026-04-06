# Dev Log — FIX-114

**WP:** FIX-114 — Fix CI test.yml 3 regressions and manifest-check  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-04-06  

## ADR Check
No ADRs in `docs/decisions/index.jsonl` directly govern CRLF normalisation, git init user config, or grep PCRE usage. No supersession required.

## Problem Summary
Three CI regressions on the Windows runner:
1. `manifest-check` job: 4 template files had CRLF locally but `.gitattributes` mandates `eol=lf`. CI checked out LF copies so SHA256 hashes mismatched MANIFEST.json.
2. `INS-030` test: `_init_git_repository()` ran `git commit` without a local `user.name`/`user.email` config. On CI (no global git config), the commit silently failed.
3. `SAF-073` test: `require-approval.sh` used `grep -qP` (PCRE) for backtick detection. Git Bash on Windows CI may lack PCRE-enabled grep.

## Implementation

### Fix 1 — CRLF normalisation + MANIFEST regeneration
- Ran `git add --renormalize templates/agent-workbench/.github/hooks/` to convert 4 files from CRLF to LF in the index.
- Ran `python scripts/generate_manifest.py` to regenerate MANIFEST.json with LF hashes.
- Verified: `python scripts/generate_manifest.py --check` → "Manifest is up to date."

### Fix 2 — git user config in `_init_git_repository()`
**File:** `src/launcher/core/project_creator.py`  
Added two `subprocess.run` calls after `git init` and before `git add`:
```python
subprocess.run(["git", "config", "user.name", "Launcher"], **common)
subprocess.run(["git", "config", "user.email", "launcher@localhost"], **common)
```
These are repo-local (not global) and ensure `git commit` succeeds on CI.

### Fix 3 — POSIX grep for backtick detection
**File:** `templates/agent-workbench/.github/hooks/scripts/require-approval.sh`  
Replaced:
```sh
if echo "$INPUT_NORM" | grep -qP '`\w'; then
```
With:
```sh
if echo "$INPUT_NORM" | grep -qE '`[a-zA-Z_0-9]'; then
```
`\w` (PCRE word-char class) is equivalent to `[a-zA-Z_0-9]` in POSIX ERE. MANIFEST.json was regenerated after this change.

## Tests Written
- `tests/FIX-114/test_fix114_ci_regressions.py`
  - `test_manifest_check_passes` — runs `generate_manifest.py --check`
  - `test_git_init_sets_user_config` — asserts user.name/email config present in source
  - `test_require_approval_no_pcre_grep` — asserts no `grep -qP` and POSIX replacement is in place

## Target Tests Confirmed Passing
- `tests/INS-030/test_ins030_git_init.py::TestCreateProjectGitInit::test_created_workspace_has_initial_commit` ✓
- `tests/MNT-029/test_mnt029_manifest.py::test_manifest_check_exits_clean` ✓
- `tests/SAF-073/test_saf073.py::test_deny_command_substitution_backtick` ✓

## Files Changed
- `src/launcher/core/project_creator.py` — added git user config
- `templates/agent-workbench/.github/hooks/scripts/require-approval.sh` — POSIX grep
- `templates/agent-workbench/.github/hooks/require-approval.json` — CRLF→LF
- `templates/agent-workbench/.github/hooks/scripts/counter_config.json` — CRLF→LF
- `templates/agent-workbench/.github/hooks/scripts/reset_hook_counter.py` — CRLF→LF
- `templates/agent-workbench/.github/hooks/scripts/zone_classifier.py` — CRLF→LF
- `templates/agent-workbench/MANIFEST.json` — regenerated with LF hashes
- `docs/workpackages/workpackages.jsonl` — status updated
- `tests/FIX-114/test_fix114_ci_regressions.py` — new tests
- `docs/workpackages/FIX-114/dev-log.md` — this file
