# Test Report — GUI-035

**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Iteration:** 1

## Summary

GUI-035 creates `templates/clean-workspace/` — a lightweight template with full security gate
infrastructure but without agents/prompts/skills/AgentDocs directories. All 64 tests pass.
No regressions were introduced. The implementation is correct and complete.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| GUI-035: targeted suite (TST-2703) | Unit | PASS | 64 passed — Developer (43) + Tester edge cases (21) |
| GUI-035: full regression suite (TST-2702) | Regression | PASS* | 9065 passed, 262 failures pre-existing on main (0 new) |

\* The full regression suite logged as Fail due to pre-existing baseline failures. After cross-referencing
with the main branch, **0 new failures** were introduced by GUI-035.

## Test Coverage

**Developer Tests (43)** — `tests/GUI-035/test_gui035_clean_workspace_template.py`

| Class | Tests | Covers |
|-------|-------|--------|
| `TestTemplateDirectoryExists` | 1 | Template root directory present |
| `TestRequiredFiles` | 16 | All 16 required files present (parametrised) |
| `TestForbiddenDirectories` | 4 | No agents/, prompts/, skills/, AgentDocs/ |
| `TestSecurityFilesIdentical` | 6 | Byte-identity for 6 security files vs agent-workbench |
| `TestVscodeSettings` | 2 | .github and .vscode hidden in files.exclude |
| `TestCopilotInstructions` | 4 | No agent/skills/AgentDocs refs; {{PROJECT_NAME}} present |
| `TestAgentRules` | 2 | No AgentDocs refs; {{PROJECT_NAME}} present |
| `TestManifestJson` | 5 | Valid JSON, template field, file_count, security_gate tracked |
| `TestTemplateDiscovery` | 3 | list_templates(), is_template_ready(), generate_manifest() |

**Tester Edge-Case Tests (21)** — `tests/GUI-035/test_gui035_edge_cases.py`

| Class | Tests | Covers |
|-------|-------|--------|
| `TestManifestHashIntegrity` | 3 | All MANIFEST.json hashes match actual files; file_count integrity; all hook scripts marked security_critical |
| `TestAdditionalByteIdenticalFiles` | 4 | counter_config.json, reset_hook_counter.py, .gitignore, NoAgentZone/README.md byte-identical to agent-workbench |
| `TestTemplatePlaceholders` | 6 | {{WORKSPACE_NAME}} and {{PROJECT_NAME}} in README, copilot-instructions, AGENT-RULES; {{VERSION}} in .github/version |
| `TestVscodeSettingsCompleteness` | 3 | NoAgentZone hidden in search.exclude; autoApprove=false; workspace trust enabled |
| `TestNoTemplatePollution` | 3 | No __pycache__, .pyc, or .pytest_cache artifacts |
| `TestCopilotInstructionsSafety` | 2 | No .github/prompts or Project/AgentDocs references in copilot-instructions |

## Regression Analysis

- **Baseline failures (before GUI-035 on main):** 262
- **Failures on GUI-035 branch:** 262
- **New regressions introduced:** **0**

The 90 "new" failures flagged by the automated cross-check (comparing to the regression baseline JSONL) are
pre-existing on the main branch. This was confirmed by running the full test suite on the main branch
and comparing FAILED/ERROR lines directly: both branches produce identical failure sets.

## Security Review

- All security gate files (security_gate.py, update_hashes.py, zone_classifier.py,
  require-approval.ps1, require-approval.sh, require-approval.json, reset_hook_counter.py,
  counter_config.json) are byte-identical to agent-workbench. SHA256 hashes verified.
- MANIFEST.json hashes verified against actual file contents — all 16 entries match.
- All security files marked `security_critical: true` in MANIFEST.json.
- copilot-instructions.md contains no references to directories that don't exist in the template.
- settings.json: `chat.tools.global.autoApprove=false`, workspace trust enabled, NoAgentZone hidden.
- No forbidden directories: `.github/agents/`, `.github/prompts/`, `.github/skills/`, `Project/AgentDocs/` — all absent.

## ADR Verification

- **ADR-003** (Template Manifest and Workspace Upgrade System) — Acknowledged in dev-log. MANIFEST.json
  follows the same schema as agent-workbench. No conflict.
- **ADR-011** (Drop settings.json from Security Gate Integrity Hash) — Acknowledged. settings.json is
  tracked in MANIFEST.json but not marked security_critical, consistent with the decision.
- No superseded ADRs related to this WP.

## Edge Cases Considered

1. **Tampered security files** — MANIFEST.json hash integrity test ensures any tampering would be detected.
2. **Missing placeholders** — All template substitution variables verified in both template and nested files.
3. **Template pollution** — No __pycache__, .pyc, or .pytest_cache artifacts left in template.
4. **Stale instructions** — copilot-instructions.md verified to not reference directories that don't exist.
5. **Side effects on other tests** — Full regression comparison confirms 0 new failures.
6. **Counter config consistency** — counter_config.json and reset_hook_counter.py byte-identical to agent-workbench.

## Bugs Found

None.

## Verdict

**PASS** — Mark WP as Done.
