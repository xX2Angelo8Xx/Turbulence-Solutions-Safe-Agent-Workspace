# Dev Log — SAF-068

**WP ID:** SAF-068  
**Name:** Fix shlex backslash consumption in _tokenize_segment  
**Assigned To:** Developer Agent  
**Branch:** SAF-068/fix-shlex-backslash  
**Status:** Review  
**Date Started:** 2026-04-02  

---

## Problem

`_tokenize_segment()` in `security_gate.py` calls `shlex.shlex(segment, posix=True)`.
In POSIX mode, `shlex` treats `\` as an escape character, silently consuming backslashes
in unquoted Windows paths. `C:\Users\angel` becomes `C:Usersangel`, which has no `/`,
`\`, or `..`, so `_is_path_like()` returns `False` and zone checks never fire.
This allows unquoted Windows paths to bypass the security gate entirely.

**Bug:** BUG-173  
**User Story:** US-074  

---

## Fix

Added one line before the `shlex.shlex()` call in `_tokenize_segment()`:

```python
segment = re.sub(r"\\(?=\S)", "/", segment)
```

This normalizes interior backslashes: `C:\Users\angel` → `C:/Users/angel` before shlex sees it.  
The lookahead `(?=\S)` (non-whitespace after backslash) ensures trailing backslashes are NOT normalized — they  
still cause a `shlex.ValueError` → safe-fail deny, preserving the FIX-022/FIX-023 trailing-backslash behavior.

Forward slashes are preserved by shlex. The `/` characters make `_is_path_like()` return `True`,  
triggering zone checks which correctly deny the path.

**Initial approach:** `segment.replace("\\", "/")` was tried first but broke 2 existing tests  
(`test_ls_trailing_backslash_deny`, `test_venv_dot_venv_trailing_backslash_deny`) that relied  
on trailing-`\` causing a `ValueError`. The regex approach is the correct solution.

**File changed:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`  
**Lines changed:** ~1510 (one insertion inside `_tokenize_segment()`)

---

## Tests Written

**Test file:** `tests/SAF-068/test_saf068.py`

| Test | Description |
|------|-------------|
| `test_tokenize_segment_normalizes_backslashes` | `_tokenize_segment` preserves path with forward slashes |
| `test_unquoted_windows_path_denied` | `Get-Content C:\Users\angel\secret.txt` → deny |
| `test_unquoted_get_childitem_denied` | `Get-ChildItem C:\Users` → deny |
| `test_quoted_windows_path_still_denied` | Quoted path `"C:\Users\angel\secret.txt"` → deny |
| `test_project_folder_path_allowed` | Project-relative path → allow |
| `test_unc_path_denied` | UNC path `\\server\share` → deny |

---

## Implementation Notes

- Only `_tokenize_segment()` was modified. No other functions touched.
- `update_hashes.py` intentionally NOT run — that is SAF-071's scope.
- The fix is a single-line forward-slash normalization, minimal blast radius.

---

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
- `tests/SAF-068/test_saf068.py` (new)
- `tests/SAF-068/__init__.py` (new)
- `docs/workpackages/SAF-068/dev-log.md` (this file)
- `docs/workpackages/workpackages.csv` (status updated)
