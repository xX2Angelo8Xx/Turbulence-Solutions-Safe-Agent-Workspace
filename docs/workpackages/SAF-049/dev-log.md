# SAF-049 Dev Log

## Workpackage
**ID:** SAF-049  
**Title:** Update AGENT-RULES search tool documentation to match actual behavior  
**Branch:** SAF-049/search-doc-fix  
**Status:** In Progress → Review  
**Assigned To:** GitHub Copilot  

---

## Problem Statement

`AGENT-RULES.md` §3 (Tool Permission Matrix) labels `grep_search` and `file_search` as having "no zone restriction", which is inaccurate. The actual behavior enforced by the security gate is:

- `includePattern` targeting denied zones (e.g., `NoAgentZone/**`) is blocked
- `includeIgnoredFiles: true` is blocked  
- General pattern-based search (without targeting denied zones) remains allowed

This misleading wording was reported in BUG-114 (v3.2.1 feedback).

---

## Changes Made

### `templates/agent-workbench/Project/AGENT-RULES.md`

Updated §3 Tool Permission Matrix — Search Tools section:

- `grep_search`: Changed from "no zone restriction" to accurate description noting that `includePattern` targeting denied zones is blocked and `includeIgnoredFiles: true` is blocked.
- `file_search`: Same correction applied.
- `semantic_search`: Left unchanged (no zone restriction is correct for this tool).

---

## Tests Written

`tests/SAF-049/test_saf049_agent_rules_doc.py`

- `test_grep_search_no_longer_says_no_zone_restriction` — verifies old misleading text is absent
- `test_file_search_no_longer_says_no_zone_restriction` — verifies old misleading text is absent
- `test_grep_search_documents_include_pattern_restriction` — verifies `includePattern` restriction is documented
- `test_file_search_documents_include_pattern_restriction` — verifies `includePattern` restriction is documented
- `test_grep_search_documents_include_ignored_files_restriction` — verifies `includeIgnoredFiles` restriction is documented
- `test_file_search_documents_include_ignored_files_restriction` — verifies `includeIgnoredFiles` restriction is documented
- `test_grep_search_still_allowed_for_general_use` — verifies general use still documented as allowed
- `test_file_search_still_allowed_for_general_use` — verifies general use still documented as allowed
- `test_semantic_search_unchanged` — verifies `semantic_search` retains its original (no zone restriction) description

---

## Bugs Fixed

- BUG-114: Fixed In WP = SAF-049

---

## Known Limitations

None. This is a documentation-only change.
