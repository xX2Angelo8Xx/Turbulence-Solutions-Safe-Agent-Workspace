# SAF-030 Dev Log — Recognize bare tilde as path-like token

## Status
In Progress

## Assigned To
Developer Agent

## Objective
Extend `_is_path_like()` in `security_gate.py` to return `True` for bare tilde (`~`) and
tilde-prefixed paths (`~/path`, `~\path`). Currently `~` has no `/`, `\`, `..`, or leading
dot, so `_is_path_like` returns `False` and commands like `rm ~` pass without any zone
check. After the fix, `_validate_args` will zone-check `~`, and since `~` resolves to HOME
(outside the project folder), the zone classifier returns "deny".

## Root Cause
`_is_path_like` relied on `_PATH_LIKE_RE = re.compile(r"[/\\]|\.\.")` plus a
`token.startswith(".")` check. A bare `~` satisfies none of these, so it was never treated
as a path argument.

## Fix
Added a tilde check to `_is_path_like`:
```python
if token == "~" or token.startswith("~/") or token.startswith("~\\"):
    return True
```
This is the minimal, targeted change. No other logic was modified.

## Files Changed
- `Default-Project/.github/hooks/scripts/security_gate.py` — `_is_path_like()` fix
- `Default-Project/.github/hooks/scripts/update_hashes.py` — re-run to refresh integrity hash
- `templates/coding/` security_gate.py — synced from Default-Project

## Tests Written
`tests/SAF-030/test_saf030_tilde_path.py`

Test cases:
- `rm ~` → deny
- `rm ~/Documents` → deny
- `remove-item ~` → deny
- `remove-item ~/Desktop` → deny
- `del ~` → deny
- `cat ~/secret.txt` → deny
- `ls ~` → deny
- Regression: normal project paths still allow

## Implementation Date
2026-03-18
