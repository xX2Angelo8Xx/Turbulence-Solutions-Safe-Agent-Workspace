# Test Report — GUI-023

**Tester:** Tester Agent
**Date:** 2026-03-25
**Iteration:** 1

## Summary

The template rename from `templates/coding/` → `templates/agent-workbench/` and `templates/creative-marketing/` → `templates/certification-pipeline/` is correctly implemented. Both renames were performed via `git mv`, preserving all content including hidden directories (`.github/`, `.vscode/`, `NoAgentZone/`). All security-critical files are intact. The launcher source code requires no changes — `_format_template_name()`, `list_templates()`, `is_template_ready()`, `TEMPLATES_DIR`, and `launcher.spec` are all path-agnostic. No broken references to old names exist in `src/`.

Globally 11 GUI tests (in GUI-002 and GUI-014) and a number of DOC and INS tests fail due to referencing old template paths — all are documented as FIX-071 scope, pre-known, and explicitly excluded from this WP's verdict per the handoff instructions.

The 71 SAF collection errors (`ModuleNotFoundError: No module named 'security_gate'`) are pre-existing across the full test suite and pre-date this WP.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2116: GUI-023 targeted suite (16 tests) | Unit | PASS | Developer tests: directory existence, format fn, list_templates, is_template_ready, TEMPLATES_DIR |
| TST-2117: GUI-023 full regression suite | Regression | FAIL* | 71 pre-existing SAF collection errors unrelated to WP; 11 FIX-071 test failures expected |
| TST-2118: GUI-023 tester edge-case suite (26 tests) | Unit | PASS | Format boundaries, list_templates robustness, security files, no broken refs |

\* Full-suite failure is pre-existing and FIX-071 scope — not caused by GUI-023.

### Tester Edge-Case Coverage (26 tests added)

| Test | Validates |
|------|-----------|
| `test_format_empty_string` | `_format_template_name("")` returns `""` without crash |
| `test_format_single_word` | `"coding"` → `"Coding"` |
| `test_format_underscore_separated` | `"agent_workbench"` → `"Agent Workbench"` |
| `test_format_mixed_separators` | `"agent-work_bench"` → `"Agent Work Bench"` |
| `test_format_already_title_case` | `"Agent-Workbench"` → `"Agent Workbench"` |
| `test_format_triple_hyphen` | `"a-b-c"` → `"A B C"` |
| `test_list_templates_ignores_files` | Regular files in templates/ are excluded |
| `test_list_templates_empty_dir_returns_empty` | Empty templates dir → `[]` |
| `test_list_templates_nonexistent_path` | Non-existent path → `[]` |
| `test_list_templates_not_a_path_object` | str input → `[]` (type guard) |
| `test_list_templates_real_count` | Exactly 2 template directories exist |
| `test_is_template_ready_empty_dir` | Empty dir → not ready |
| `test_is_template_ready_readme_only` | README-only dir → not ready |
| `test_is_template_ready_one_non_readme_file` | Single non-README file → ready |
| `test_is_template_ready_readme_plus_one_file` | README + file → ready |
| `test_security_gate_py_exists` | `security_gate.py` preserved after rename |
| `test_zone_classifier_py_exists` | `zone_classifier.py` preserved after rename |
| `test_require_approval_json_exists` | `require-approval.json` preserved |
| `test_agent_workbench_vscode_settings_exist` | `.vscode/settings.json` preserved |
| `test_agent_workbench_gitignore_exists` | `.gitignore` preserved |
| `test_certification_pipeline_has_readme` | README.md exists in cert-pipeline |
| `test_certification_pipeline_readme_content` | README mentions "Certification Pipeline" |
| `test_certification_pipeline_only_has_readme` | Only README.md — not populated yet |
| `test_src_no_reference_to_templates_coding` | No `templates/coding` in `src/` |
| `test_src_no_reference_to_creative_marketing` | No `creative-marketing` in `src/` |
| `test_launcher_spec_bundles_templates_generically` | `launcher.spec` bundles `templates/` generically, no hard-coded old names |

## Pre-existing / Out-of-Scope Failures

All listed failures pre-date or are explicitly excluded from GUI-023 scope:

| Failing Tests | Count | Reason |
|---------------|-------|--------|
| SAF-001 through SAF-045 collection errors | 71 | `ModuleNotFoundError: No module named 'security_gate'` — pre-existing |
| GUI-002 (TestGetTemplateOptions, TestDropdownDynamicLoading, TestTemplateDirPresence) | 9 | References `templates/coding` / `creative-marketing` — FIX-071 scope |
| GUI-014 (TestRealTemplatesDirectory) | 2 | References `templates/coding` display name — FIX-071 scope |
| INS-004 (test_ins004_template_bundling) | ~9 | References `templates/coding` — FIX-071 scope |
| DOC-009 (test_doc009_placeholder_replacement) | ~9 | References `templates/coding/Project/AGENT-RULES.md` — FIX-071 scope |

## Bugs Found

None. All failures are pre-existing or FIX-071 scope.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done**

The rename is correct and complete. All 42 GUI-023 tests pass (16 developer + 26 tester). Security-critical files are preserved. No broken references in source code. The implementation is path-agnostic and robust. Expected test failures in other WPs are documented as FIX-071 scope.
