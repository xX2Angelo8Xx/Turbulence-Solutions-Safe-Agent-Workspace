# SAF-033 Dev Log — Protect update_hashes.py from agent execution

**WP ID:** SAF-033  
**Branch:** SAF-033  
**Developer:** Developer Agent  
**Date Started:** 2026-03-19  
**User Story:** US-013

---

## Summary

Strengthened the existing `update_hashes.py` execution block in the terminal sanitizer.
SAF-026 had already added `re.compile(r"\bupdate_hashes\b")` to `_EXPLICIT_DENY_PATTERNS`.
SAF-033 strengthens this by removing the `\b` word-boundary anchors, converting the pattern
to a simple substring match (`update_hashes`). This ensures ANY command whose lowercased
text contains the substring `update_hashes` — regardless of surrounding characters — is
denied.

---

## Findings — Existing SAF-026 Protection

Before implementation, the existing pattern was:
```python
re.compile(r"\bupdate_hashes\b"),  # SAF-026: block direct execution of update_hashes
```

Applied to `lowered_segment` (the segment lowercased at line 1646), so:
- Case-insensitive: YES (via lowering before matching)
- Substring match: NO (word-boundary anchors require non-word chars around the token)
- Gap: `\bupdate_hashes\b` would NOT match if `update_hashes` is surrounded by word
  characters on either side (e.g. `my_update_hashes_v2` would not be blocked).

A second protection exists in `_scan_python_inline_code` (Category E):
```python
for infra in ("update_hashes", ...):
    if infra in low:
        return False
```
This already uses substring matching (no word boundaries) for the `-c` code path.

---

## Changes Made

### Both files changed identically:
- `Default-Project/.github/hooks/scripts/security_gate.py`
- `templates/coding/.github/hooks/scripts/security_gate.py`

**Change:** Replaced `re.compile(r"\bupdate_hashes\b")` with `re.compile(r"update_hashes")`
and updated the comment from `SAF-026` to `SAF-033`.

The pattern is applied to `lowered_segment` (already lowercase), so case-insensitive
behaviour is preserved. The removal of `\b` anchors makes this a pure substring check,
matching the WP requirement: "if any token in the terminal command contains 'update_hashes'
(case-insensitive), deny the command."

### Post-change hash update:
After modifying both `security_gate.py` files, `update_hashes.py` was run for each to
re-embed SHA256 hashes.

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | Strengthened update_hashes deny pattern |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Strengthened update_hashes deny pattern (identical change) |

---

## Tests Written

**Location:** `tests/SAF-033/test_saf033_update_hashes_protection.py`

Tests cover:
1. Direct execution variants: `python update_hashes.py`, `python3 update_hashes.py`,
   `py update_hashes.py`, `./update_hashes.py`
2. Variants with path prefixes: `python ./update_hashes.py`, `python scripts/update_hashes.py`
3. Mixed-case variants: `python UPDATE_HASHES.PY`, `python Update_Hashes.py`
4. Substring variants: `python my_update_hashes.py` (now denied — substring match)
5. Bypass-attempt tests: obfuscated names (ensure they are caught)
6. The file remains readable: `read_file`, `grep_search` on the path are NOT affected
7. Regression: normal commands still allowed after adding the pattern
8. templates/coding copy matches Default-Project copy (identical pattern)

---

## Iteration 1

Initial implementation. All tests pass.
