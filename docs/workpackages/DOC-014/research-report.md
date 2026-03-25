# Research Report — DOC-014: Audit Logging for Hook Decisions

**Author:** Developer Agent  
**Date:** 2026-03-25  
**Workpackage:** DOC-014  
**User Story:** US-034  
**Status:** Final  

---

## Executive Summary

This report examines whether and how the security gate should log its allow/deny
decisions to a file for post-session review. The analysis covers log format design,
I/O overhead, file location, rotation, retention, privacy considerations, and the
proposed integration point in `security_gate.py`.

**Recommendation:** Implement **deny-only audit logging** using a lightweight
append-only JSONL file stored alongside the existing state files in
`.github/hooks/scripts/`. Allowed operations are intentionally excluded from the
audit log to avoid excessive I/O and to respect user privacy (allowed tool calls
reveal normal work patterns). With a maximum of 20 denials per session, the
performance impact is negligible. Log files should be rotated when they reach
1 MiB and retained for 30 days. The integration point is the `deny` branch of
`main()` in `security_gate.py`, immediately after `_increment_deny_counter` is
called.

---

## 1. Logging Format Design

### 1.1 Requirements

A log entry for a denied action must capture:

| Field | Purpose |
|-------|---------|
| `timestamp` | Absolute UTC time — correlates log to real-world events |
| `session_id` | Links all decisions in one Copilot session |
| `tool_name` | Which tool was denied |
| `decision` | Always `"deny"` in the deny-only scheme |
| `reason` | Human-readable denial reason (rule triggered, lockout, …) |
| `deny_count` | Counter value at time of denial (e.g. `"3/20"`) |

### 1.2 Recommended Format: JSONL (JSON Lines)

Each log entry is a single JSON object on one line, terminated by `\n`. This
format is:

- **Machine-readable** — trivially parsed by any JSON library
- **Append-friendly** — new entries are appended without reading or rewriting
  existing content
- **Human-readable** — a simple `cat` / `type` shows clean records
- **Grep-friendly** — `grep session_id` returns exact matching lines

**Example log entry:**

```json
{"timestamp": "2026-03-25T14:07:33Z", "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "tool_name": "run_in_terminal", "decision": "deny", "deny_count": "3/20", "reason": "Block 3 of 20. Access denied. This action has been blocked by the workspace security policy."}
```

### 1.3 Fields Deliberately Omitted

- **`input` / tool arguments** — omitting these protects any secrets or sensitive
  data that an agent might pass as arguments (file contents, tokens, etc.).
- **`ws_root`** — the workspace path reveals machine-specific filesystem layout;
  not needed for audit purposes.
- **Allowed operations** — See Section 4 (privacy rationale).

### 1.4 Lockout Entry Format

When a session is locked out, a final entry is appended with `"decision": "lockout"`:

```json
{"timestamp": "2026-03-25T14:08:01Z", "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "tool_name": "create_file", "decision": "lockout", "deny_count": "20/20", "reason": "Session locked — 20 denied actions reached. Start a new chat session to continue working."}
```

This provides a clear audit trail of which tool triggered the lockout.

---

## 2. I/O Overhead Evaluation

### 2.1 Deny-Only Volume

The security gate permits a maximum of `_DENY_THRESHOLD_DEFAULT = 20` denials
before locking a session. In practice, a developer session will incur far fewer
violations. A conservative upper bound is 20 log writes per session.

### 2.2 Write Cost

Each JSONL entry is approximately 200–300 bytes. With 20 entries per session:

- **Total data written per session:** ≤ 6 KB
- **Write syscalls:** 20 (one `open` + `write` + `close` sequence per denial)
- **Wall-clock cost per write:** < 1 ms on any modern SSD or HDD

The hook is invoked synchronously for every tool call. A 1 ms overhead added
to a denial (which is already a blocking error response) is imperceptible.
For the 99%+ of tool calls that are **allowed**, there is **zero** overhead
because allowed operations are not logged.

### 2.3 Conclusion

Deny-only logging introduces negligible I/O overhead. The append-only write
pattern is the lowest-cost durable write strategy available (no read-before-write,
no locking required for single-process append). The implementation requires no
buffering or batching.

---

## 3. Log File Location, Rotation, and Retention

### 3.1 Proposed Location

```
.github/hooks/scripts/audit.log.jsonl
```

**Rationale:**

- Co-located with `security_gate.py`, `.hook_state.json`, and `copilot-otel.jsonl`
  — all security-relevant runtime files live together.
- The `.github/hooks/scripts/` directory is already excluded from normal `src/`
  restrictions and is the gate's own working directory.
- Consistent with the existing convention: `.hook_state.json` (session state) and
  `copilot-otel.jsonl` (telemetry) share the same directory.
- Agents do not have write access to files outside the scripts directory through
  normal hook operation; centralising audit files here requires no new permission
  grants.

### 3.2 Rotation Policy

| Trigger | Action |
|---------|--------|
| File size ≥ 1 MiB | Rename `audit.log.jsonl` → `audit.log.jsonl.<ISO-date>` and open a fresh file |

**Rotation implementation note:** Rotation should occur at the start of a `main()`
call, before any write, to keep the active file small and readable. A simple size
check with `os.path.getsize` is sufficient; no external log-rotation daemon is
required. The rotation is performed in `_maybe_rotate_audit_log(scripts_dir)`.

**Why 1 MiB?** At ≤ 300 bytes per entry and ≤ 20 entries per session, a 1 MiB
threshold accommodates approximately 1,700 sessions before rotation. For a
daily-use developer machine this is several months of audit history per file —
more than sufficient to investigate any incident without unbounded disk growth.

### 3.3 Retention Policy

| Policy | Value |
|--------|-------|
| Rotated file retention | 30 days |
| Maximum rotated files kept | 10 |
| Deletion mechanism | Prune files older than 30 days at rotation time |

**Rationale:** 30 days provides sufficient window to retrospectively investigate
a security incident (e.g., an agent was compromised weeks ago). More than 10
rotated files implies either unusual denial volume or a system clock issue —
capping at 10 prevents unbounded accumulation.

### 3.4 .gitignore Recommendation

The audit log file should be added to `.gitignore` to prevent accidental
inclusion in commits:

```
.github/hooks/scripts/audit.log.jsonl
.github/hooks/scripts/audit.log.jsonl.*
```

This is consistent with `.hook_state.json` which is already excluded from
version control by convention.

---

## 4. Privacy Considerations

### 4.1 Should Allowed Operations Be Logged?

**Decision (from project plan, Q7): Log denied activities only.**

The rationale is:

1. **Volume:** Allowed tool calls are the norm. A developer session may involve
   hundreds of `read_file`, `grep_search`, and `semantic_search` calls — logging
   all of them produces megabytes of data per session with no security benefit,
   as these calls were explicitly permitted.

2. **Privacy:** A full allow-log would record every file path read, every search
   query issued, and every terminal command executed within allowed scope. This
   reveals the developer's complete work pattern and potentially the content of
   files they accessed. The security gate's purpose is to *block* unsafe actions,
   not to surveil safe ones.

3. **Performance:** Logging every allowed call (potentially 500–1 000 per session)
   would add measurable I/O overhead to every single tool invocation — the opposite
   of the negligible overhead achieved by deny-only logging.

4. **Signal-to-noise:** An audit log containing only denials is easy to review
   post-session. A mixed log requires filtering before analysis.

### 4.2 What the Deny Log Reveals

A deny-only log still reveals:
- Which tool names were attempted but blocked
- How many times per session (via `deny_count`)
- The session ID (a UUID — not linked to user identity by default)
- The timestamp of each violation

This is the minimum information needed for security audit purposes while respecting
user privacy.

### 4.3 Tool Arguments Are Not Logged

Even for denied calls, the tool `input` object (file paths, command strings, etc.)
is not written to the audit log. If an agent attempted to run a malicious command,
the command string itself is excluded. This protects against the audit log becoming
a secondary exfiltration vector for sensitive data that was present in the tool call.

**Trade-off acknowledged:** Excluding the `input` means a post-session reviewer
cannot see the exact malicious command. If detailed forensics are required, the
operator can temporarily enable full-argument logging via a config flag (proposed
in Section 5 as `log_denied_inputs: false` default).

---

## 5. Integration Point in security_gate.py

### 5.1 Recommended Integration Point

The audit log write should occur in the `else` (deny) branch of `main()`,
immediately after `_increment_deny_counter` and `_save_state`, before
`print(build_response("deny", ...))`:

```python
# Proposed insertion in main() — deny branch
if counter_enabled:
    deny_count, now_locked = _increment_deny_counter(
        state, session_id, threshold
    )
    _save_state(state_path, state)
    # DOC-014: Write deny audit entry
    _append_audit_log(
        scripts_dir=scripts_dir,
        session_id=session_id,
        tool_name=data.get("tool_name", "unknown"),
        decision="lockout" if now_locked else "deny",
        deny_count=deny_count,
        threshold=threshold,
        reason=deny_reason,
    )
    ...
```

The existing `deny` path at lines ~2828–2840 is the natural home for this call.
The `_append_audit_log` function is a pure side-effect (append-only file write)
that cannot affect the gate's decision logic.

### 5.2 Additional Integration: Lockout-During-Check Path

There is a second deny path in `main()`: when the session is already locked at
the start of the hook call (the "pre-check" lockout). This path should also
append an audit entry so the log records every blocked call, not just those that
triggered the initial lockout:

```python
# Existing locked-session check (lines ~2813–2820)
if isinstance(session_data, dict) and session_data.get("locked", False):
    _lockout_msg = "Session locked — ..."
    # DOC-014: Audit the continued block of an already-locked session
    _append_audit_log(
        scripts_dir=scripts_dir,
        session_id=session_id,
        tool_name=data.get("tool_name", "unknown"),
        decision="blocked_locked",
        deny_count=session_data.get("deny_count", threshold),
        threshold=threshold,
        reason=_lockout_msg,
    )
    print(build_response("deny", _lockout_msg), flush=True)
    sys.exit(0)
```

### 5.3 Proposed New Functions

Two new helper functions are required:

#### `_append_audit_log(scripts_dir, session_id, tool_name, decision, deny_count, threshold, reason)`

Appends one JSONL record to `audit.log.jsonl`. Called only on deny/lockout.
Uses `open(..., "a", encoding="utf-8")` for atomic line-append semantics.
Wrapped in a broad `except Exception: pass` to ensure audit-log failures
**never** affect the gate decision (fail-safe: log failure is silent).

#### `_maybe_rotate_audit_log(scripts_dir)`

Called once at the start of `main()` (before any write). Checks the current
file size; if ≥ 1 MiB, renames it to `audit.log.jsonl.<YYYY-MM-DD>` and
deletes rotated files older than 30 days (or beyond the 10-file cap).

### 5.4 Counter Config Extension

The existing `counter_config.json` (introduced by SAF-036) should be extended
with two optional fields:

```json
{
  "counter_enabled": true,
  "lockout_threshold": 20,
  "audit_log_enabled": true,
  "log_denied_inputs": false
}
```

- `audit_log_enabled` (default `true`) — allows operators to opt out of audit
  logging entirely (e.g., in highly privacy-sensitive environments).
- `log_denied_inputs` (default `false`) — allows operators to opt into logging
  tool arguments for detailed forensics. Off by default to protect privacy.

The `_load_counter_config` function in `security_gate.py` already reads
`counter_config.json` and applies defaults; extending it with these fields
requires only adding two `data.get(...)` calls.

---

## 6. Design Document — Recommended Approach

### 6.1 Summary of Decisions

| Concern | Decision |
|---------|---------|
| What to log | Denied operations only |
| Log format | JSONL, one record per line |
| Fields per entry | timestamp, session_id, tool_name, decision, deny_count, reason |
| Tool input logged | No (privacy protection, configurable) |
| Log file location | `.github/hooks/scripts/audit.log.jsonl` |
| Rotation trigger | File size ≥ 1 MiB |
| Retention | 30 days / 10 rotated files max |
| Integration point | `main()` deny branch, after `_increment_deny_counter` |
| Config extension | `audit_log_enabled` + `log_denied_inputs` in `counter_config.json` |
| Failure mode | Silent (audit failure never blocks a tool call) |
| .gitignore | `audit.log.jsonl*` excluded from commits |

### 6.2 Implementation Scope (Future WP)

This report is a design document. Implementation is deferred to a future SAF-xxx
workpackage. The implementer should:

1. Add `_maybe_rotate_audit_log(scripts_dir)` to `security_gate.py`.
2. Add `_append_audit_log(...)` to `security_gate.py`.
3. Extend `_load_counter_config` for the two new config fields.
4. Call `_maybe_rotate_audit_log` at the top of `main()`.
5. Call `_append_audit_log` in both deny branches of `main()`.
6. Update `counter_config.json` template with new optional fields.
7. Add `audit.log.jsonl*` to the `.gitignore` in the hooks scripts directory.
8. Run `update_hashes.py` after any change to `security_gate.py`.

### 6.3 Security Properties

- **Fail-safe:** Audit log write errors are silently swallowed — a disk-full or
  permission error never causes the gate to deny a legitimate operation.
- **Append-only:** The log file is opened in append mode, never overwritten.
  An agent cannot retroactively remove denial evidence without filesystem-level
  access (which is already outside the security gate's threat model).
- **No PII in log:** Session IDs are UUIDs; tool arguments are excluded by default.
- **Tamper detection:** The audit log is not integrity-protected by default (no
  HMAC). If tamper-evident logs are required, a future WP can add per-line HMAC
  using a key stored in the workspace admin config.

---

## 7. References

- `templates/coding/.github/hooks/scripts/security_gate.py` — gate implementation,
  `main()` deny branch, `_increment_deny_counter`, `_load_counter_config`
- `templates/coding/.github/hooks/scripts/counter_config.json` — SAF-036 config file
- `docs/workpackages/SAF-035/dev-log.md` — session denial counter design
- `docs/workpackages/SAF-036/dev-log.md` — counter configuration design
- `docs/workpackages/DOC-013/research-report.md` — multi-agent counter coordination
- US-034 acceptance criterion 6: "The design is backed by documented handling for
  session identification, multi-agent coordination, and audit logging decisions."
