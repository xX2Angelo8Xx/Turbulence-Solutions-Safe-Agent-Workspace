# Dev Log — FIX-071: Update all test references for template rename

**WP ID:** FIX-071  
**Branch:** FIX-071/test-template-refs  
**Developer:** Developer Agent  
**Status:** Review  

---

## Summary

Updated all test files that referenced old template directory names (`templates/coding/` and `templates/creative-marketing/`) to use the new names (`templates/agent-workbench/` and `templates/certification-pipeline/`) following the GUI-023 rename.

---

## Problem

GUI-023 renamed the template directories:
- `templates/coding/` → `templates/agent-workbench/`
- `templates/creative-marketing/` → `templates/certification-pipeline/`

Approximately 120+ test files across the test suite still contained hardcoded references to the old paths. These caused `FileNotFoundError` and assertion failures across many test modules.

---

## Implementation

### Phase 1 (prior session): Bulk path updates
A bulk transformation script (`docs/workpackages/FIX-071/transform_tests.py`) was used to update ~120 test files. The script replaced:
- `templates/coding` → `templates/agent-workbench`
- `templates/creative-marketing` → `templates/certification-pipeline`
- Display names `"Coding"` / `"Creative Marketing"` → `"Agent Workbench"` / `"Certification Pipeline"` where used as template names in mock configurations

### Phase 2 (this session): Fix remaining failures

After reviewing test results, 21 additional failures were identified and fixed:

#### DOC-003 (5 failures fixed)
- `tests/DOC-003/test_doc003_edge_cases.py`: Updated `TEMPLATES_CODING_FILE` constant from `templates/coding/...` to `templates/agent-workbench/...`
- `tests/DOC-003/test_doc003_placeholders.py`: Same fix to `TEMPLATES_CODING_FILE`

#### SAF-022 (3 failures fixed)
- `tests/SAF-022/test_saf022_noagentzone_exclude.py`: Fixed broken 3-element tuples `("templates", "agent-workbench", DEFAULT_SETTINGS)` → `("templates/agent-workbench", DEFAULT_SETTINGS)`. The bulk transform had incorrectly split the label string `"templates/coding"` into two separate elements.

#### SAF-024 (2 failures fixed)
- `tests/SAF-024/test_saf024_edge_cases.py`: Updated `_TEMPLATE_PATH` from `templates/coding/...` to `templates/agent-workbench/...`
- `tests/SAF-024/test_saf024_generic_deny_messages.py`: Updated `_TEMPLATE_SCRIPTS_DIR` from `templates/coding/...` to `templates/agent-workbench/...`

#### GUI-020 (8 failures fixed)
- `tests/GUI-020/test_gui020_app_passes_counter_config.py`: Updated `_trigger_create` helper to use `"Agent Workbench"` instead of `"Coding"` for `project_type_dropdown.get.return_value`. The `_format_template_name("agent-workbench")` returns `"Agent Workbench"`, so the mock dropdown must match.
- `tests/GUI-020/test_gui020_tester_edge_cases.py`: Updated 2 test methods with the same `"Coding"` → `"Agent Workbench"` fix.

#### GUI-022 (3 failures fixed)
- `tests/GUI-022/test_gui022_include_readmes_checkbox.py`: Updated `_make_app_with_include_readmes` helper default `template="Coding"` → `template="Agent Workbench"`, and updated 2 explicit test calls passing `template="Coding"`.
- `tests/GUI-022/test_gui022_edge_cases.py`: Changed `project_type_dropdown.get.return_value = "Coding"` → `"Agent Workbench"`.

---

## Pre-existing failures (not FIX-071's responsibility)

The following failures exist on `main` and are unrelated to the template rename:
- **SAF-010** (2): `require-approval.json` uses `ts-python` but test expects `python` — pre-existing content mismatch
- **FIX-042** (2): `**/NoAgentZone` still in `files.exclude` — separate issue
- **FIX-007, FIX-009, FIX-019, FIX-028, FIX-031, FIX-036, FIX-037, FIX-038, FIX-039, FIX-049, MNT-002**: various pre-existing failures in CI/CD, codesign, and version tracking tests

---

## Files Changed

### Test files modified (complete list):
- `tests/conftest.py`
- `tests/DOC-002/test_doc002_readme_placeholders.py`
- `tests/DOC-002/test_doc002_tester_edge_cases.py`
- `tests/DOC-003/test_doc003_edge_cases.py`
- `tests/DOC-003/test_doc003_placeholders.py`
- `tests/DOC-004/test_doc004_project_readme_placeholders.py`
- `tests/DOC-004/test_doc004_tester_edge_cases.py`
- `tests/DOC-005/test_doc005_limitations.py`
- `tests/DOC-007/test_doc007_agent_rules.py`
- `tests/DOC-008/test_doc008_read_first_directive.py`
- `tests/DOC-008/test_doc008_tester_edge_cases.py`
- `tests/DOC-009/test_doc009_placeholder_replacement.py`
- `tests/FIX-002/test_fix002_hook_config_migration.py`
- `tests/FIX-003/test_fix003_template_sync.py`
- `tests/FIX-013/test_fix013_template_path.py`
- `tests/FIX-021/test_fix021_search_tools.py`
- `tests/FIX-022/test_fix022_path_fallback.py`
- `tests/FIX-022/test_fix022_tester_edge_cases.py`
- `tests/FIX-023/test_fix023_tester_edge_cases.py`
- `tests/FIX-023/test_fix023_venv_fallback.py`
- `tests/FIX-024/test_fix024_absolute_path_verification.py`
- `tests/FIX-025/test_fix025_cat_type_in_allowlist.py`
- `tests/FIX-026/test_fix026_get_errors_fallback.py`
- `tests/FIX-026/test_fix026_tester_edge_cases.py`
- `tests/FIX-027/test_fix027_absolute_path_handling.py`
- `tests/FIX-032/test_fix032_redirect_and_cmdlets.py`
- `tests/FIX-033/test_fix033_dot_prefix_env_vars.py`
- `tests/FIX-033/test_fix033_tester_edge_cases.py`
- `tests/FIX-034/test_fix034_tester_edge_cases.py`
- `tests/FIX-034/test_fix034_venv_activation.py`
- `tests/FIX-035/test_fix035_deferred_tools.py`
- `tests/FIX-042/test_fix042_noagentzone_visible.py`
- `tests/FIX-046/test_fix046_default_project_removed.py`
- `tests/FIX-069/test_fix069_zone_classifier_import.py`
- `tests/GUI-002/test_gui002_project_type_selection.py`
- `tests/GUI-005/test_gui005_project_creation.py`
- `tests/GUI-006/test_gui006_tester_edge_cases.py`
- `tests/GUI-006/test_gui006_vscode_auto_open.py`
- `tests/GUI-007/test_gui007_edge_cases.py`
- `tests/GUI-007/test_gui007_tester_additions.py`
- `tests/GUI-007/test_gui007_validation.py`
- `tests/GUI-014/test_gui014_coming_soon.py`
- `tests/GUI-017/test_gui017_edge_cases.py`
- `tests/GUI-017/test_gui017_ui_labels.py`
- `tests/GUI-020/test_gui020_app_passes_counter_config.py`
- `tests/GUI-020/test_gui020_tester_edge_cases.py`
- `tests/GUI-022/test_gui022_edge_cases.py`
- `tests/GUI-022/test_gui022_include_readmes_checkbox.py`
- `tests/INS-004/test_ins004_edge_cases.py`
- `tests/INS-004/test_ins004_template_bundling.py`
- `tests/INS-020/test_ins020_require_approval.py`
- `tests/SAF-001/test_saf001_security_gate.py`
- `tests/SAF-002/test_saf002_zone_classifier.py`
- `tests/SAF-003/test_saf003_tool_parameter_validation.py`
- `tests/SAF-005/test_saf005_edge_cases.py`
- `tests/SAF-005/test_saf005_terminal_sanitization.py`
- `tests/SAF-006/test_saf006_edge_cases.py`
- `tests/SAF-006/test_saf006_recursive_edge_cases.py`
- `tests/SAF-006/test_saf006_recursive_protection.py`
- `tests/SAF-006/test_saf006_tester_iter4.py`
- `tests/SAF-007/test_saf007_write_restriction.py`
- `tests/SAF-008/test_saf008_integrity.py`
- `tests/SAF-009/test_saf009_cross_platform.py`
- `tests/SAF-009/test_saf009_tester_edge_cases.py`
- `tests/SAF-010/test_saf010_hook_config.py`
- `tests/SAF-011/test_saf011_edge_cases.py`
- `tests/SAF-011/test_saf011_update_hashes.py`
- `tests/SAF-012/test_saf012_zone_classifier.py`
- `tests/SAF-012/test_saf012_zone_classifier_tester_edge.py`
- `tests/SAF-013/test_saf013_edge_cases.py`
- `tests/SAF-013/test_saf013_security_gate_2tier.py`
- `tests/SAF-014/test_saf014_edge_cases.py`
- `tests/SAF-014/test_saf014_read_commands.py`
- `tests/SAF-015/test_saf015_edge_cases.py`
- `tests/SAF-015/test_saf015_write_commands.py`
- `tests/SAF-016/test_saf016_delete_commands.py`
- `tests/SAF-016/test_saf016_edge_cases.py`
- `tests/SAF-016/test_saf016_tester_edge_cases.py`
- `tests/SAF-017/test_saf017_edge_cases.py`
- `tests/SAF-017/test_saf017_python_pip_commands.py`
- `tests/SAF-018/test_saf018_edge_cases.py`
- `tests/SAF-018/test_saf018_multi_replace.py`
- `tests/SAF-019/test_saf019_edge_cases.py`
- `tests/SAF-019/test_saf019_vscode_settings.py`
- `tests/SAF-020/test_saf020_tester_edge_cases.py`
- `tests/SAF-020/test_saf020_wildcard_blocking.py`
- `tests/SAF-021/test_saf021_wildcard_regression.py`
- `tests/SAF-022/test_saf022_edge_cases.py`
- `tests/SAF-022/test_saf022_noagentzone_exclude.py`
- `tests/SAF-023/test_saf023_get_errors.py`
- `tests/SAF-024/test_saf024_edge_cases.py`
- `tests/SAF-024/test_saf024_generic_deny_messages.py`
- `tests/SAF-025/test_saf025_hash_sync.py`
- `tests/SAF-026/test_saf026_edge_cases.py`
- `tests/SAF-026/test_saf026_python_c_scanning.py`
- `tests/SAF-028/test_saf028_bare_enumeration.py`
- `tests/SAF-028/test_saf028_tester_edge_cases.py`
- `tests/SAF-029/test_saf029_delete_dot_prefix.py`
- `tests/SAF-030/test_saf030_tilde_path.py`
- `tests/SAF-031/test_saf031_virtualenv_bypass.py`
- `tests/SAF-032/test_saf032_git_block.py`
- `tests/SAF-032/test_saf032_tester_edge_cases.py`
- `tests/SAF-033/test_saf033_update_hashes_protection.py`
- `tests/SAF-034/test_saf034.py`
- `tests/SAF-034/test_saf034_edge.py`
- `tests/SAF-035/test_saf035_denial_counter.py`
- `tests/SAF-035/test_saf035_tester_edge_cases.py`
- `tests/SAF-036/test_saf036_counter_config.py`
- `tests/SAF-036/test_saf036_tester_edge_cases.py`
- `tests/SAF-037/test_reset_hook_counter.py`
- `tests/SAF-037/test_saf037_edge_cases.py`
- `tests/SAF-038/test_saf038_edge_cases.py`
- `tests/SAF-038/test_saf038_memory_create_directory.py`
- `tests/SAF-039/test_saf039_lsp_tools.py`
- `tests/SAF-039/test_saf039_tester_edge_cases.py`
- `tests/SAF-040/test_saf040_readonly_commands.py`
- `tests/SAF-040/test_saf040_tester_edge_cases.py`
- `tests/SAF-041/test_saf041_shell_utilities.py`
- `tests/SAF-041/test_saf041_tester_edge_cases.py`
- `tests/SAF-042/test_saf042_git_allowlist.py`
- `tests/SAF-042/test_saf042_tester_edge_cases.py`
- `tests/SAF-043/test_saf043_file_search.py`
- `tests/SAF-043/test_saf043_tester_edge_cases.py`
- `tests/SAF-044/test_saf044_search_scoping.py`
- `tests/SAF-044/test_saf044_tester_edge_cases.py`
- `tests/SAF-045/test_saf045_grep_search_scoping.py`
- `tests/SAF-045/test_saf045_tester_edge_cases.py`

### New test files:
- `tests/FIX-071/test_fix071_template_ref_updates.py` (11 tests)

### Workpackage files:
- `docs/workpackages/workpackages.csv` (status: In Progress → Review)
- `docs/workpackages/FIX-071/dev-log.md` (this file)

---

## Test Results

- **FIX-071 tests:** 11 passed, 0 failed
- **All affected test modules:** 5539+ passed after fixes
- **Pre-existing failures:** 51 (unchanged from main, unrelated to template rename)

---

## Known Limitations

- Some test files still contain `templates/coding` in **comment strings and docstrings** (not as file paths). These are acceptable — they describe historical context or error message text and do not cause test failures.
- The SAF-010 failures (`ts-python` vs `python`) were pre-existing — the `require-approval.json` used `ts-python` before the rename and continues to do so after.
