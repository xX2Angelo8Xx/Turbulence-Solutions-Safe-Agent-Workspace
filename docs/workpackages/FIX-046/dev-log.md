# FIX-046 Dev Log — Remove Default-Project and update references

**WP ID:** FIX-046  
**Branch:** FIX-046  
**Developer:** Developer Agent  
**Date Started:** 2026-03-19  
**Status:** In Progress  

---

## Summary

Delete the entire `Default-Project/` directory from the repository (it is byte-identical to `templates/coding/` and was the original development copy). Update ALL references across test files, docs, and source code to point to `templates/coding/` instead.

---

## Implementation Plan

1. Create branch FIX-046 ✓
2. Claim WP in workpackages.csv ✓
3. Update security_gate.py comment (line 66) in templates/coding
4. Run update_hashes.py to re-embed hashes after comment change
5. Update ALL test files referencing Default-Project paths
6. Update docs/architecture.md
7. Update docs/project-scope.md
8. git rm -r Default-Project/
9. Write tests in tests/FIX-046/
10. Run full test suite
11. Commit and push

---

## Files Changed

| File | Change |
|------|--------|
| `templates/coding/.github/hooks/scripts/security_gate.py` | Updated comment on line 66 to reference templates/coding path |
| `docs/architecture.md` | Removed Default-Project/ entry, updated templates/coding description |
| `docs/project-scope.md` | Updated table row referencing Default-Project |
| `docs/workpackages/workpackages.csv` | Set FIX-046 to In Progress |
| `tests/SAF-001/test_saf001_security_gate.py` | Path updated to templates/coding |
| `tests/SAF-002/test_saf002_zone_classifier.py` | Path updated to templates/coding |
| `tests/SAF-005/test_saf005_terminal_sanitization.py` | Path updated to templates/coding |
| `tests/SAF-005/test_saf005_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-007/test_saf007_write_restriction.py` | Path updated to templates/coding |
| `tests/SAF-008/test_saf008_integrity.py` | Path updated to templates/coding |
| `tests/SAF-009/test_saf009_cross_platform.py` | Path updated to templates/coding |
| `tests/SAF-009/test_saf009_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-010/test_saf010_hook_config.py` | Path updated to templates/coding |
| `tests/SAF-011/test_saf011_update_hashes.py` | Path updated to templates/coding |
| `tests/SAF-011/test_saf011_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-012/test_saf012_zone_classifier.py` | Path updated to templates/coding |
| `tests/SAF-012/test_saf012_zone_classifier_tester_edge.py` | Path updated to templates/coding |
| `tests/SAF-013/test_saf013_security_gate_2tier.py` | Restructured, DP references removed |
| `tests/SAF-013/test_saf013_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-014/test_saf014_read_commands.py` | Path updated to templates/coding |
| `tests/SAF-014/test_saf014_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-015/test_saf015_write_commands.py` | Path updated to templates/coding |
| `tests/SAF-015/test_saf015_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-022/test_saf022_noagentzone_exclude.py` | Restructured, DP references removed |
| `tests/SAF-022/test_saf022_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-023/test_saf023_get_errors.py` | Path updated to templates/coding |
| `tests/SAF-024/test_saf024_generic_deny_messages.py` | Restructured, DP references removed |
| `tests/SAF-024/test_saf024_edge_cases.py` | Restructured, DP references removed |
| `tests/SAF-025/test_saf025_hash_sync.py` | Restructured: DP vars → TC only |
| `tests/SAF-026/test_saf026_python_c_scanning.py` | Path updated to templates/coding |
| `tests/SAF-026/test_saf026_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-028/test_saf028_bare_enumeration.py` | Path updated to templates/coding |
| `tests/SAF-028/test_saf028_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/SAF-029/test_saf029_delete_dot_prefix.py` | Path updated to templates/coding |
| `tests/SAF-030/test_saf030_tilde_path.py` | Path updated to templates/coding |
| `tests/SAF-031/test_saf031_virtualenv_bypass.py` | Path updated to templates/coding |
| `tests/SAF-033/test_saf033_update_hashes_protection.py` | Restructured, DP refs removed |
| `tests/DOC-002/test_doc002_readme_placeholders.py` | Path updated to templates/coding |
| `tests/DOC-002/test_doc002_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/DOC-003/test_doc003_placeholders.py` | Path updated to templates/coding |
| `tests/DOC-003/test_doc003_edge_cases.py` | Path updated to templates/coding |
| `tests/DOC-004/test_doc004_project_readme_placeholders.py` | Path updated to templates/coding |
| `tests/DOC-004/test_doc004_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/DOC-005/test_doc005_limitations.py` | Path updated to templates/coding |
| `tests/FIX-021/test_fix021_search_tools.py` | Path updated to templates/coding |
| `tests/FIX-022/test_fix022_path_fallback.py` | Path updated to templates/coding |
| `tests/FIX-022/test_fix022_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/FIX-023/test_fix023_venv_fallback.py` | Path updated to templates/coding |
| `tests/FIX-023/test_fix023_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/FIX-026/test_fix026_get_errors_fallback.py` | Path updated to templates/coding |
| `tests/FIX-026/test_fix026_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/FIX-032/test_fix032_redirect_and_cmdlets.py` | Path updated to templates/coding |
| `tests/FIX-033/test_fix033_dot_prefix_env_vars.py` | Path updated to templates/coding |
| `tests/FIX-033/test_fix033_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/FIX-034/test_fix034_venv_activation.py` | Path updated to templates/coding |
| `tests/FIX-034/test_fix034_tester_edge_cases.py` | Path updated to templates/coding |
| `tests/FIX-035/test_fix035_deferred_tools.py` | Path updated to templates/coding |
| `tests/FIX-042/test_fix042_noagentzone_visible.py` | Restructured, DP refs removed |
| `tests/INS-004/test_ins004_template_bundling.py` | Already has skip guard — no functional path changes needed |
| `tests/INS-004/test_ins004_edge_cases.py` | Restructured, DP comparison tests removed |
| `Default-Project/` | Removed via git rm -r |
| `tests/FIX-046/test_fix046_default_project_removed.py` | New test file |

---

## Tests Written

| Test Function | Category | Description |
|--------------|----------|-------------|
| `test_default_project_directory_does_not_exist` | Regression | Default-Project/ no longer in repo |
| `test_templates_coding_still_exists` | Unit | templates/coding/ present after removal |
| `test_templates_coding_has_security_gate` | Unit | security_gate.py exists in templates/coding |
| `test_security_gate_comment_references_templates_coding` | Unit | Comment on line 66 references correct path |
| `test_no_references_to_default_project_in_test_files` | Integration | No broken Default-Project path in any test |

---

## Decisions

- Historical references in `docs/workpackages/*/dev-log.md`, `docs/maintenance/*.md`, `docs/test-results/test-results.csv`, and `docs/bugs/bugs.csv` narrative fields are NOT updated — they are historical records of past work.
- `docs/work-rules/agent-workflow.md` references to `Default-Project/` in the context of "Forbidden locations" are updated to remove `Default-Project/` since it no longer exists.
- `copilot-instructions.md` references to `Default-Project/` are updated.
- Comments/labels in test files that mention "Default-Project" in error messages are updated for clarity; the critical changes are path-functional ones.
- INS-004 tests that compare Default-Project vs templates/coding already have skip guards and will auto-skip; their "both exist" tests remain but become single-directory existence tests.
- SAF-025 tests TST-1632 through TST-1638 (DP vs TC parity checks) are restructured as single-file integrity checks on templates/coding only.
