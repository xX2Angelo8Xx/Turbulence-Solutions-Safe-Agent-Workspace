# Dev Log — DOC-014

**Developer:** Developer Agent  
**Date started:** 2026-03-25  
**Iteration:** 1

## Objective

Research whether and how the security gate should log all decisions (allow/deny)
to a file for post-session review. Produce a design document covering:

1. Lightweight logging format: timestamp, session ID, tool name, decision, reason
2. I/O overhead evaluation (deny-only: max 20 writes per session)
3. Log file location, rotation policy, and retention
4. Privacy: only denied activities are logged (allowed operations excluded)
5. Integration point in `security_gate.py`
6. Design document with recommended approach in `research-report.md`

---

## Implementation Summary

This is a **research-only workpackage**. No changes were made to `src/`, `templates/`,
or any existing source files. The deliverables are:

- `docs/workpackages/DOC-014/research-report.md` — full audit logging design document
- `tests/DOC-014/test_doc014_report.py` — structural validation tests confirming
  the report exists and contains all required sections

---

## Research Summary

### Key Findings

1. **Deny-only logging is the correct scope**: Logging all allowed operations
   (potentially hundreds per session) would add measurable I/O overhead to every
   tool call, reveal normal work patterns (privacy), and produce a noisy log with
   poor signal-to-noise ratio. Denied actions (max 20 per session) are the only
   ones worth auditing.

2. **JSONL (JSON Lines) is the optimal format**: Append-only, no read-before-write,
   machine-readable and grep-friendly. Each entry is ~200–300 bytes.

3. **Log location**: `.github/hooks/scripts/audit.log.jsonl` — co-located with
   `.hook_state.json` and `copilot-otel.jsonl`, consistent with existing conventions.

4. **Rotation at 1 MiB / retention 30 days / 10 files max**: A 1 MiB threshold
   covers ~1,700 sessions. 30-day retention provides sufficient incident investigation
   window. Cap of 10 rotated files prevents unbounded disk use.

5. **Tool arguments are excluded**: Even for denied calls, the `input` object is
   not logged to prevent the audit file from becoming a secondary exfiltration vector.
   An opt-in `log_denied_inputs: false` config flag allows operators to enable it.

6. **Integration point**: `main()` deny branch in `security_gate.py`, after
   `_increment_deny_counter` and `_save_state`, calling a new
   `_append_audit_log(...)` helper. A second integration point covers the
   pre-lockout check path. A `_maybe_rotate_audit_log` call belongs at the
   top of `main()`.

7. **Config extension**: `counter_config.json` gains two optional fields:
   `audit_log_enabled` (default `true`) and `log_denied_inputs` (default `false`).

### Files Inspected

- `templates/coding/.github/hooks/scripts/security_gate.py` — `main()`,
  `_increment_deny_counter`, `_load_counter_config`, `_get_session_id`
- `docs/workpackages/SAF-035/dev-log.md` — denial counter architecture
- `docs/workpackages/SAF-036/dev-log.md` — counter configuration design
- `docs/workpackages/DOC-013/research-report.md` — multi-agent context
- `docs/user-stories/user-stories.csv` — US-034 acceptance criteria

---

## Files Changed

| File | Change Type |
|------|-------------|
| `docs/workpackages/DOC-014/research-report.md` | Created (design document) |
| `docs/workpackages/DOC-014/dev-log.md` | Created (this file) |
| `tests/DOC-014/test_doc014_report.py` | Created (structural validation tests) |
| `docs/workpackages/workpackages.csv` | Updated (status → In Progress → Review) |

---

## Tests Written

| Test | Category | Validates |
|------|----------|-----------|
| `test_report_file_exists` | Unit | Report exists at expected path |
| `test_report_is_not_empty` | Unit | Report has substantial content (> 200 chars) |
| `test_report_section_1_log_format` | Unit | Section 1 covers JSONL format and required fields |
| `test_report_section_2_io_overhead` | Unit | Section 2 addresses I/O overhead analysis |
| `test_report_section_3_file_location` | Unit | Section 3 specifies log file location |
| `test_report_section_4_privacy` | Unit | Section 4 covers privacy and deny-only decision |
| `test_report_section_5_integration_point` | Unit | Section 5 names the integration point in security_gate.py |
| `test_report_section_6_design_document` | Unit | Section 6 contains design document / summary |
| `test_report_mentions_jsonl` | Unit | JSONL format is mentioned |
| `test_report_mentions_rotation` | Unit | Rotation policy is present |
| `test_report_mentions_retention` | Unit | Retention period is specified |
| `test_report_deny_only_decision` | Unit | Report confirms deny-only logging decision |
| `test_report_mentions_counter_config_extension` | Unit | counter_config.json extension is documented |
| `test_report_mentions_gitignore` | Unit | .gitignore exclusion is recommended |
