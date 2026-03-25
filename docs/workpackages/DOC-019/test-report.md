# Test Report — DOC-019

**Tester:** Tester Agent
**Date:** 2026-03-25
**Iteration:** 1

## Summary

The `programmer.agent.md` file is correctly implemented: valid YAML frontmatter, all required tools present, meaningful persona body, AGENT-RULES.md reference. All 11 developer tests and all 12 tester edge-case tests pass (23 total for DOC-019).

**Verdict: FAIL** — The DOC-019 commit broke an existing test in `tests/DOC-018/`. The DOC-019 Developer did not update that test as part of their work. The failing test introduced a regression that blocks approval.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_file_exists` | Unit | PASS | File at correct path |
| `test_file_is_not_empty` | Unit | PASS | File has content |
| `test_file_starts_with_frontmatter_delimiter` | Unit | PASS | Opens with `---` |
| `test_frontmatter_is_parseable` | Unit | PASS | Valid YAML |
| `test_frontmatter_name_present_and_non_empty` | Unit | PASS | name: Programmer |
| `test_frontmatter_description_present_and_non_empty` | Unit | PASS | Description present |
| `test_frontmatter_tools_is_list` | Unit | PASS | 8 tools in list |
| `test_frontmatter_required_tools_present` | Unit | PASS | All required tools found |
| `test_frontmatter_model_present_and_non_empty` | Unit | PASS | model: claude-sonnet-4-5 |
| `test_body_is_non_empty` | Unit | PASS | Body has persona text |
| `test_body_references_agent_rules` | Unit | PASS | AGENT-RULES.md referenced |
| `test_frontmatter_has_closing_delimiter` | Unit | PASS | `---` closes frontmatter |
| `test_frontmatter_tools_contains_file_search` | Unit | PASS | file_search present |
| `test_frontmatter_tools_contains_multi_replace` | Unit | PASS | multi_replace_string_in_file present |
| `test_frontmatter_model_is_not_placeholder` | Unit | PASS | No `{{...}}` in model |
| `test_frontmatter_name_has_no_placeholder` | Unit | PASS | No `{{...}}` in name |
| `test_body_mentions_implementation` | Unit | PASS | "implement" in body |
| `test_body_mentions_refactoring` | Unit | PASS | "refactor" in body |
| `test_body_describes_zone_restrictions` | Unit | PASS | Denied zones listed (.github, .vscode, NoAgentZone) |
| `test_body_does_not_contain_interactive_constructs` | Unit | PASS | No user-prompt instructions |
| `test_file_is_valid_utf8` | Unit | PASS | Valid UTF-8 encoding |
| `test_file_has_no_trailing_crlf_issues` | Unit | PASS | No bare CR characters |
| `test_frontmatter_does_not_duplicate_opening_delimiter` | Unit | PASS | Exactly 2 `---` delimiters |
| Full regression suite (all tests/) | Regression | **FAIL** | 71 failed, 5889 passed — includes DOC-018 regression introduced by this WP |

### Regression Detail

`tests/DOC-018/test_doc018_tester_edge_cases.py::test_agents_dir_contains_only_readme` **FAILS** after DOC-019's commit.

The test was a phase-gate assertion:
```
"""agents/ directory must only contain README.md (no .agent.md files yet — those are DOC-019..028)."""
```
- Before DOC-019 commit: agents/ contained only `README.md` → test **passed**.
- After DOC-019 commit: agents/ contains `programmer.agent.md` and `README.md` → test **FAILS**.

This failure was caused by DOC-019's change and was not addressed by the Developer. Per protocol: **"DO NOT approve work that fails any existing test."**

The 70 other failures are pre-existing (INS-014, INS-015, INS-017, INS-019, MNT-002, SAF-010) and unrelated to DOC-019.

---

## Bugs Found

- **BUG-106**: `DOC-018 test_agents_dir_contains_only_readme stale after DOC-019 adds programmer.agent.md` (logged in docs/bugs/bugs.csv)

---

## Security Review

No security concerns found:
- No credentials or secrets in the agent file
- No hardcoded absolute paths — only project-relative references (`.github/`, `AGENT-RULES.md`)
- No `{{PROJECT_NAME}}` placeholder issues beyond what is intentional (e.g. `{{PROJECT_NAME}}/` used correctly in zone restriction description)
- Denied zones are correctly enumerated in the persona body
- Agent file is static content (no executable code)

---

## TODOs for Developer

- [ ] **Fix the failing DOC-018 test.** Update `tests/DOC-018/test_doc018_tester_edge_cases.py::test_agents_dir_contains_only_readme` to no longer assert that ONLY `README.md` is present. The test was a phase-gate for the pre-DOC-019 state and is now permanently stale.

  **Suggested fix** (update the test assertion):
  ```python
  def test_agents_dir_contains_only_readme():
      """agents/ directory must contain README.md. programmer.agent.md is added by DOC-019."""
      entries = os.listdir(AGENTS_DIR)
      visible = [e for e in entries if not e.startswith(".") and e != "__pycache__"]
      assert "README.md" in visible, "README.md must always be present in agents/"
  ```
  Or simply remove the snapshot assertion entirely and replace it with a check that `README.md` is present (not that it's the only file).

  After fixing, run the full suite to confirm the failure is resolved and no new failures were introduced. The fix must be scoped to `tests/DOC-018/` only — do not change source files.

---

## Verdict

**FAIL — Return to Developer (Iteration 1)**

DOC-019's implementation is correct but the Developer did not update the stale DOC-018 phase-gate test that their commit invalidated. Fix the single failing test in `tests/DOC-018/` and resubmit for Tester review.
