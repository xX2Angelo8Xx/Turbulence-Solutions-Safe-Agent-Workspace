# SAF-035: Implement Session-Scoped Denial Counter — Dev Log

**WP ID:** SAF-035  
**Branch:** SAF-035/session-denial-counter  
**Assigned To:** Developer Agent  
**Status:** Review  
**Started:** 2026-03-21  
**Completed:** 2026-03-21

---

## Summary

Implements a session-scoped denial counter in `templates/coding/.github/hooks/scripts/security_gate.py`.
The counter tracks deny decisions per session, shows progressive "Block N of M" messaging,
and locks the session at the configured threshold (default 20).

## Scope

- `templates/coding/.github/hooks/scripts/security_gate.py` — core counter logic
- `templates/coding/.vscode/settings.json` — add 3 OTel settings
- `templates/coding/.gitignore` — exclude `copilot-otel.jsonl` and `.hook_state.json`
- `tests/SAF-035/test_saf035_denial_counter.py` — tests

## Implementation Decisions

1. **Session ID via OTel JSONL**: Reads the last non-empty line from `copilot-otel.jsonl`
   in the scripts directory. Extracts `session.id` from resource attributes, falls back
   to `gen_ai.conversation.id` from span attributes.
2. **Fallback UUID**: When OTel JSONL is absent or contains no session ID, generates a
   UUID4 stored under `_fallback_session_id` in `.hook_state.json`. Reused across
   invocations until manually reset.
3. **State file**: `.hook_state.json` in `.github/hooks/scripts/`. Structure:
   ```json
   {
     "_fallback_session_id": "uuid4",
     "_fallback_created": "ISO timestamp",
     "session-uuid": {
       "deny_count": 5,
       "locked": false,
       "timestamp": "ISO timestamp of last deny"
     }
   }
   ```
4. **Atomic write**: State file is written to a temp file, then renamed. This prevents
   corruption from partial writes and provides a form of concurrent-access safety.
5. **Thread safety**: Python's os.replace() is atomic on POSIX. On Windows, it's
   effectively atomic for the rename, providing safe concurrent access.
6. **Threshold M = 20** (default, hard-coded in SAF-035; SAF-036 will make it configurable).
7. **Locked sessions**: Checked at entry in main() before decide(); all tool calls rejected.
8. **Counter integration point**: The `main()` function is modified to check lock status
   before deciding and to increment the counter after each deny decision.

## Files Changed

- `templates/coding/.github/hooks/scripts/security_gate.py`
- `templates/coding/.vscode/settings.json`
- `templates/coding/.gitignore`

## Tests Written

- `tests/SAF-035/test_saf035_denial_counter.py` — 11 test cases covering all ACs

## Known Limitations

- In fallback mode (no OTel), session boundaries cannot be detected. All denies in the
  current VS Code instance accumulate under the same UUID until manually reset.
- SAF-036 will add threshold configurability; SAF-037 will add a reset script.
