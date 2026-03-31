# DOC-042 Test Report — Update agent default model and tools settings

**WP:** DOC-042  
**Branch:** DOC-042/agent-settings  
**Tester:** Tester Agent  
**Date:** 2026-03-31  
**Verdict: FAIL**

---

## Summary

The implementation correctly updates 6 of 7 agent files. However, `coordinator.agent.md` has a malformed YAML frontmatter: the `argument-hint` field contains an **unclosed double-quoted string**, causing `yaml.safe_load()` to raise a `ScannerError`. This defect was not caught by the Developer's tests because those tests use plain regex/string matching rather than YAML parsing.

---

## Test Runs

| Run | Test File | Tests | Passed | Failed | Status |
|-----|-----------|-------|--------|--------|--------|
| TST-2379 | `test_doc042_agent_settings.py` | 20 | 20 | 0 | Pass |
| TST-2380 | `test_doc042_edge_cases.py` | 21 | 15 | 6 | **FAIL** |

---

## Failures

All 6 failures cascade from the same root cause: **`coordinator.agent.md` has an unclosed double-quoted string** in the `argument-hint` YAML field.

### Root Cause

**File:** `templates/agent-workbench/.github/agents/coordinator.agent.md`, line 7

**Current (broken):**
```yaml
argument-hint: "Describe the goal or plan you want to autonomously be worked on. 
```
The closing `"` is missing. Python's `yaml.safe_load()` raises:
```
yaml.scanner.ScannerError: while scanning a quoted scalar
  found unexpected end of stream
```

**Expected (correct):**
```yaml
argument-hint: "Describe the goal or plan you want to autonomously be worked on."
```

### Failed Tests

| Test | Failure Reason |
|------|----------------|
| `test_coordinator_frontmatter_is_valid_yaml` | YAML parse error (root cause) |
| `test_all_agents_have_required_yaml_keys` | Parse failure on coordinator prevents key check |
| `test_no_agent_has_empty_tools` | Parse failure on coordinator propagates |
| `test_no_agent_has_empty_model` | Parse failure on coordinator propagates |
| `test_no_agent_has_empty_name` | Parse failure on coordinator propagates |
| `test_planner_is_only_opus_agent` | Parse failure on coordinator propagates |

---

## Bug Filed

**BUG-166** — `coordinator.agent.md`: unclosed double-quoted string in argument-hint YAML field (Severity: High)

---

## Passing Tests

All 20 Developer tests and 15 of 21 Tester edge-case tests pass:
- All 7 agent files exist ✓
- 6 agents use `Claude Sonnet 4.6 (copilot)` ✓
- Planner uses `Claude Opus 4.6 (copilot)` ✓
- No Sonnet agent uses Opus ✓
- All agents' expected tools are present in frontmatter text ✓
- Coordinator has `agents:` field listing all 6 specialists ✓
- Tidyup has `argument-hint` field ✓
- All 7 files start with `---` delimiter ✓
- All 7 files have closing `---` delimiter ✓
- All 7 body texts contain `{{PROJECT_NAME}}` placeholder ✓
- 6 of 7 agents have valid parseable YAML frontmatter (coordinator fails) ✗

---

## Other Observations

1. **Coordinator missing common tools** — The WP description says "expand tool lists to include vscode/memory, vscode/vscodeAPI, vscode/askQuestions where appropriate." The dev-log notes coordinator was left with `[vscode, execute, read, agent, edit, search, web/githubRepo, todo]` as "already correct." This is defensible since coordinator uses the generic `vscode` tool. No bug filed for this — it is a documented deliberate decision.

2. **Coordinator tools** include `vscode` (generic) instead of the three specific subtools. This interpretation is ambiguous but accepted since the WP says "where appropriate."

---

## TODOs for Developer (must fix before re-review)

1. **Fix** `templates/agent-workbench/.github/agents/coordinator.agent.md`:
   - Line 7: add the missing closing `"` to the `argument-hint` value.
   - Correct value: `argument-hint: "Describe the goal or plan you want to autonomously be worked on."`

2. **Verify** fix with: `python -c "import yaml, pathlib, re; c=pathlib.Path('templates/agent-workbench/.github/agents/coordinator.agent.md').read_text(); m=re.match(r'^---\n(.*?)\n---', c, re.DOTALL); yaml.safe_load(m.group(1)); print('OK')"`

3. **Ensure** all 41 tests in `tests/DOC-042/` pass before re-submitting for review.

---

## Verdict

**FAIL — Returning to In Progress.**

The implementation is nearly complete but has a YAML syntax defect in `coordinator.agent.md`. The Developer must fix the unclosed string and re-submit.
