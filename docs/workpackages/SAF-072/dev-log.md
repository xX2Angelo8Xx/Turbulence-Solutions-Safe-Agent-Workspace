# Dev Log — SAF-072: Add deny-event audit logging to security gate

**WP ID:** SAF-072  
**Category:** SAF  
**User Story:** US-075  
**Bug:** BUG-175 — File-tool denials invisible, no audit trail  
**Branch:** SAF-072/deny-event-audit-logging  
**Assigned To:** Developer Agent  

---

## Objective

On every deny decision in `decide()` and `sanitize_terminal_command()`, append a JSON line to `.github/hooks/scripts/audit.jsonl`. Format each entry with: ts, sid, tool, decision, reason (generic category), target (sanitized path or command verb). Append-only, no sensitive data, graceful failure.

---

## Implementation Summary

### Changes to `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

1. **Added `_audit_deny(tool_name, reason, target)` helper function** — placed after `_load_counter_config`, before `_save_state`. The function:
   - Reads OTel session ID (or fallback UUID from state file) read-only for `sid`
   - Builds a JSON dict with ts, sid, tool, decision, reason, target
   - Writes to `Path(__file__).parent / "audit.jsonl"` in append mode
   - Wraps all logic in `try/except Exception: pass` — never raises, never crashes gate

2. **Instrumented `sanitize_terminal_command()`** — added `_audit_deny("run_in_terminal", category, target)` before all 17 `return ("deny", ...)` statements, using these reason categories:
   - `"restricted_command"` — empty/no segments, not on allowlist, destructive pattern, parse error, exception handler
   - `"zone_violation"` — venv activation/executable/script outside allowed zone, arg validation failure
   - `"obfuscation_detected"` — obfuscation pre-scan matches
   - `"env_exfiltration"` — `$env:` assignment outside zone
   - For target: command verb where available, first word of normalized command as fallback

3. **Instrumented `decide()`** — added `_audit_deny` at each deny return point:
   - Empty terminal command: `"restricted_command"`
   - Delegated validators (semantic_search, grep_search, etc.): captured result, audited with `"zone_violation"` on deny
   - Non-exempt tool: `"restricted_tool"`
   - No path: `"zone_violation"`  
   - .git internals deny: `"zone_violation"`
   - Final zone deny: `"zone_violation"`

### No sensitive data
- Targets are limited to: command verb (first token), or path basename
- `$env:` values are never logged
- File contents are never logged

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — added `_audit_deny` + audit instrumentation

---

## Tests Written

`tests/SAF-072/test_saf072.py`:
1. Deny event writes a JSON line to audit.jsonl
2. JSON line has all required keys: ts, sid, tool, decision, reason, target
3. audit.jsonl is created if it doesn't exist
4. Multiple denials append (not overwrite)
5. Audit failure (read-only file) doesn't crash the gate
6. No sensitive data in audit lines ($env: values not logged)

---

## Notes

- `update_hashes.py` was NOT run — that is SAF-071's responsibility.
- `_audit_deny` is placed before `_save_state` so helper ordering does not affect functionality.
- The function is fail-safe by design: any I/O or logic error is silently swallowed.
