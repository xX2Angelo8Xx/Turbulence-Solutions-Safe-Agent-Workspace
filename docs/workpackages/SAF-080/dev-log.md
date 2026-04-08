# SAF-080 Dev Log — Fix batch Remove-Item comma tokenization

## WP Metadata
- **ID**: SAF-080
- **User Story**: US-082
- **Branch**: `SAF-080/batch-remove-comma`
- **Status**: Review

---

## ADR Check (Step 0)

Checked `docs/decisions/index.jsonl`. ADR-011 covers dropping `settings.json`
from the security gate integrity hash — not related to this WP's tokenization
fix. No relevant or blocking ADRs found.

---

## Implementation Summary (Step 4)

### Root Cause

PowerShell treats `,` as an array operator, so `Remove-Item file1.py, file2.py`
is sent as a single command string to the security gate. `shlex.shlex` with
`whitespace_split=True` and `whitespace=" \t"` tokenises by whitespace only,
producing `['remove-item', 'file1.py,', 'file2.py']`. The trailing comma on
`file1.py,` causes two failure modes:

1. **`_is_path_like()` miss (bare names):** `_is_path_like('file1.py,')` returns
   False (no `/`, `\\`, `..`, or leading `.`). The step-5 loop skips zone checks
   entirely for that token, so paths bypass validation.

2. **`_try_project_fallback()` deny-zone guard miss (dot-prefixed names):**
   For a bare deny-zone name like `.github,`, `_check_path_arg` returns False
   correctly, but then the `_DELETE_PROJECT_FALLBACK_VERBS` fallback calls
   `_try_project_fallback('.github,', ws_root)`. The internal deny-zone guard
   tests `'.github,' in {'.github', '.vscode', 'noagentzone'}` — the trailing
   comma makes this string-equality check fail. The fallback then resolves
   `c:/workspace/project/.github,` whose first component is `project` →
   `zone_classifier` classifies it as `'allow'`. **This was a real security
   bypass: `Remove-Item .github,` would succeed.**

### Fix

In `templates/agent-workbench/.github/hooks/scripts/security_gate.py`,
`_validate_args()` step 5, immediately after `stripped = tok.strip("\"'")`:

```python
# SAF-080: Strip trailing commas from PowerShell array operator syntax.
# "Remove-Item file1.py, file2.py" → shlex produces "file1.py," which
# bypasses _is_path_like() (no slash/dot prefix) and skips zone checks.
stripped = stripped.rstrip(",")
```

This single line ensures that by the time `_is_path_like()` and
`_check_path_arg()` are called, the token is the clean path without any
comma suffix.

### Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Added `stripped = stripped.rstrip(",")` in `_validate_args()` step 5 |
| `templates/clean-workspace/.github/hooks/scripts/security_gate.py` | Byte-identical copy of agent-workbench version |
| Both `security_gate.py` files | Hashes regenerated via `update_hashes.py` |

---

## Tests Written (Step 5)

**Location:** `tests/SAF-080/test_saf080_comma_tokenization.py`  
**Count:** 16 tests, all passing  
**Logged:** TST-2788 (via `scripts/run_tests.py`)

| Test | Purpose |
|------|---------|
| `test_remove_item_batch_both_project_files_allowed` | Primary batch-allow case |
| `test_remove_item_batch_three_project_files_allowed` | Three comma-separated project files |
| `test_remove_item_batch_second_arg_deny_zone_denied` | `.github` sub-path as second arg |
| `test_remove_item_batch_first_arg_deny_zone_denied` | `.github` sub-path as first arg |
| `test_remove_item_batch_vscode_deny_zone_denied` | `.vscode` sub-path |
| `test_remove_item_bare_github_with_trailing_comma_denied` | **Critical security test** — `.github,` bypass |
| `test_remove_item_bare_vscode_with_trailing_comma_denied` | `.vscode,` bypass |
| `test_remove_item_bare_noagentzone_with_trailing_comma_denied` | `noagentzone/file.txt,` multi-segment |
| `test_rm_alias_batch_allowed` | `rm` alias batch delete |
| `test_del_alias_batch_allowed` | `del` alias batch delete |
| `test_echo_with_comma_unaffected` | Non-path commands unaffected by fix |
| `test_remove_item_without_commas_still_allowed` | Regression — no comma case |
| `test_remove_item_single_file_no_comma_allowed` | Regression — single file |
| `test_remove_item_deny_zone_without_comma_still_denied` | Regression — deny zone without comma |
| `test_remove_item_path_with_middle_comma_allowed` | Middle-comma filename, allowed |
| `test_remove_item_path_with_middle_comma_deny_zone_denied` | Middle-comma deny zone, denied |

### Known Limitation (out of scope)
`Remove-Item NoAgentZone` and `Remove-Item NoAgentZone,` are both allowed because
`_is_path_like('NoAgentZone')` returns False (no slash, no leading `.`). This
is a pre-existing behaviour for bare names without path separators, not
introduced by SAF-080 and not within scope.

---

## Validation

- `scripts/validate_workspace.py --wp SAF-080` → `All checks passed.`
- `scripts/run_tests.py --wp SAF-080 --type Unit --env "Windows 11 + Python 3.11"` → 16 passed
- Both `security_gate.py` files are byte-identical (SHA-256 verified)
- `update_hashes.py` run on both templates; hashes updated to `55ad5395...`
