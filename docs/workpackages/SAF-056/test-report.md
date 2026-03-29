# SAF-056 Test Report

## Summary

| Field | Value |
|-------|-------|
| WP ID | SAF-056 |
| Title | Update AGENT-RULES for `.venv` and copilot-instructions reality |
| Tester | Tester Agent |
| Date | 2026-03-30 |
| Verdict | **PASS** |

---

## Scope Verification

### WP Goal
Update `AGENT-RULES.md` §4 to document system Python as acceptable when no `.venv` exists.
Verify `copilot-instructions.md` is minimal and references `AGENT-RULES.md`.

### Files Reviewed
| File | Status |
|------|--------|
| `templates/agent-workbench/Project/AGENT-RULES.md` | ✅ Modified correctly |
| `templates/agent-workbench/.github/instructions/copilot-instructions.md` | ✅ Trimmed correctly |
| `tests/SAF-056/test_saf056_agent_rules.py` | ✅ 9 developer tests |
| `docs/bugs/bugs.csv` | ✅ BUG-145 marked Fixed In WP = SAF-056 |
| `docs/workpackages/workpackages.csv` | ✅ WP in Review status |

---

## Implementation Verification

### AGENT-RULES.md §4 — Terminal Rules

- ✅ Section 4 contains both `.venv\Scripts\python` (preferred) and bare `python` (acceptable fallback) examples.
- ✅ Comment on `.venv` lines: `# preferred when .venv is present`
- ✅ Comment on bare `python` lines: `# acceptable when no .venv exists`
- ✅ All placeholder tokens (`{{PROJECT_NAME}}`, `{{WORKSPACE_NAME}}`) preserved throughout the file.
- ✅ Critical security sections intact: Denied Zones (§2), Git Rules (§5), Denial Counter (§6).

### copilot-instructions.md

- ✅ References `AGENT-RULES.md` as the comprehensive rule source.
- ✅ Line count is within the 80-line limit (well under).
- ✅ Security — Denied Actions section retained.
- ✅ Does NOT duplicate full Terminal Rules or Git Rules blocks from AGENT-RULES.md.

---

## Test Results

### Developer Tests (`tests/SAF-056/test_saf056_agent_rules.py`)

| Test | Result |
|------|--------|
| `test_agent_rules_exists` | PASS |
| `test_agent_rules_system_python_acceptable` | PASS |
| `test_agent_rules_venv_preferred` | PASS |
| `test_agent_rules_section4_has_python_examples` | PASS |
| `test_copilot_instructions_exists` | PASS |
| `test_copilot_instructions_references_agent_rules` | PASS |
| `test_copilot_instructions_reasonably_short` | PASS |
| `test_copilot_instructions_comprehensive_reference_note` | PASS |
| `test_copilot_instructions_not_just_empty_pointer` | PASS |

**9 passed, 0 failed**

### Tester Edge-Case Tests (`tests/SAF-056/test_saf056_edge_cases.py`)

| Test | Result | Notes |
|------|--------|-------|
| `test_agent_rules_placeholder_project_name` | PASS | `{{PROJECT_NAME}}` present |
| `test_agent_rules_placeholder_workspace_name` | PASS | `{{WORKSPACE_NAME}}` present |
| `test_agent_rules_denied_zones_section` | PASS | `.github/`, `.vscode/`, `NoAgentZone/` listed |
| `test_agent_rules_git_rules_section` | PASS | `git push --force` blocked |
| `test_agent_rules_denial_counter_section` | PASS | Lockout section retained |
| `test_copilot_instructions_no_full_terminal_rules` | PASS | No duplicate block |
| `test_copilot_instructions_no_full_git_rules` | PASS | No duplicate block |
| `test_agent_rules_valid_utf8` | PASS | Clean encoding |
| `test_copilot_instructions_valid_utf8` | PASS | Clean encoding |
| `test_agent_rules_fallback_uses_word_acceptable` | PASS | Bare python lines correctly labelled |
| `test_agent_rules_venv_label_not_lost` | PASS | `.venv` lines still say 'preferred' |

**11 passed, 0 failed**

### Total SAF-056 Tests: 20 passed, 0 failed

### Full Regression Suite

| Metric | Value |
|--------|-------|
| Passed | 7007 |
| Failed | 74 (all pre-existing on main — confirmed by stash test) |
| Skipped | 32 |
| New regressions from SAF-056 | **0** |

Pre-existing failures are in FIX-039, FIX-042, FIX-049, INS-004, INS-014, INS-015, INS-017, INS-019, MNT-002, SAF-010, SAF-025 — none touch AGENT-RULES.md or copilot-instructions.md.

---

## Edge-Case Analysis

### Security Considerations
- The change only edits Markdown documentation files — no executable code modified.
- No secrets, credentials, or absolute paths introduced.
- Denied zones (§2) remain fully intact in AGENT-RULES.md.

### Boundary Conditions
- `copilot-instructions.md` line count checked (well under 80-line limit).
- Placeholder token integrity verified — no accidental substitution occurred.

### Potential Staleness Risk
- MITIGATED: `copilot-instructions.md` no longer duplicates rules that could diverge from AGENT-RULES.md over time.

### Test Note
During edge-case test development, an initial false-positive was detected in `test_agent_rules_fallback_uses_word_acceptable` — the substring `"python script.py"` matched the `.venv\Scripts\python script.py` line. Fixed by anchoring the check to bare `python` commands only (no `.venv` prefix).

---

## Bugs Found

None. No new bugs discovered during testing.

---

## Verdict

**PASS** — All 20 SAF-056 tests pass. Zero regressions. Implementation satisfies WP goal and US-060 acceptance criteria (AGENT-RULES.md accurately reflects Python env reality; copilot-instructions.md is a minimal pointer).
