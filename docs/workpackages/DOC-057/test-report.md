# Test Report — DOC-057

**Tester:** Tester Agent
**Date:** 2026-04-04
**Iteration:** 1

## Summary

DOC-057 correctly documents the certification pipeline exclusion in both `generate_manifest.py` (docstring + argparse) and `MANIFEST.json` (`_scope` field). Six of the seven new tests pass. One test — `test_generate_manifest_check_passes` — FAILS due to a flawed design: it calls `generate_manifest.py --check` expecting exit code 0, but `audit.jsonl` is a live security-gate log that accumulates entries continuously. Any test or hook action after the manifest was generated will change `audit.jsonl`'s hash, causing `--check` to report a discrepancy. This failure is **not** in the regression baseline and was introduced by this WP.

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| DOC-057: targeted suite (TST-2541) | Unit | **Fail** | 6 passed / 1 failed |
| Full regression suite (TST logged by prior run_tests --full-suite) | Regression | 636 failed / 8200 passed | All 636 failures are pre-existing baseline entries; no NEW regressions from DOC-057 source changes |

### DOC-057 Test Detail

| Test Function | Result | Notes |
|---|---|---|
| `test_module_docstring_mentions_agent_workbench` | PASS | |
| `test_module_docstring_mentions_certification_pipeline_exclusion` | PASS | |
| `test_argparse_description_mentions_scope` | PASS | |
| `test_generate_manifest_has_scope_field` | PASS | `generate_manifest()` returns `_scope` key with correct content |
| `test_manifest_json_has_scope_field` | PASS | MANIFEST.json on disk has `_scope` |
| `test_manifest_json_scope_not_in_files` | PASS | `_scope` is top-level metadata, not inside `files` |
| `test_generate_manifest_check_passes` | **FAIL** | See root-cause analysis below |

---

## Root-Cause Analysis — Failing Test

**Test:** `test_generate_manifest_check_passes`
**Error:** `generate_manifest.py --check` exits with code 1:
```
Manifest is OUT OF DATE:
  CHANGED:   .github/hooks/scripts/audit.jsonl
```

**Why it fails:**

`audit.jsonl` is a live security-gate audit log located at  
`templates/agent-workbench/.github/hooks/scripts/audit.jsonl`.  
The security gate appends a JSON line to this file for **every tool call** the hook intercepts (deny/allow decisions). This includes calls made during testing — other test suites in the repo deliberately write fixture entries to `audit.jsonl` to test the security gate itself.

The MANIFEST.json was regenerated at `2026-04-04T02:00:38Z`, capturing `audit.jsonl`'s hash at that instant. By the time any tests run, `audit.jsonl` has new entries, its hash has changed, and `--check` will always report a discrepancy.

**This is an inherently unstable test.** It will fail every time any agent or test touches `audit.jsonl` after manifest regeneration.

**Proof:** The baseline has 680 known failures; the current full suite has 636 failures — no new regressions from DOC-057's actual code changes. The only new failure is `test_generate_manifest_check_passes`, introduced by this WP.

---

## Bugs Found

None logged. The failing test is a test design flaw introduced in DOC-057 itself, not a bug in the application code.

---

## TODOs for Developer

- [ ] **Remove `test_generate_manifest_check_passes`** from `tests/DOC-057/test_doc057_manifest_scope.py`.  
  It does not test any DOC-057 acceptance criterion (which are: scope clarified in docstring/help text; no agent confusion about cert-pipeline) and is structurally unstable. The 6 remaining tests fully cover the acceptance criteria.  
  
  Alternatively, if coverage of the `--check` feature is desired, rewrite the test to  
  (1) call `generate_manifest()` programmatically to regenerate a temp manifest, then  
  (2) verify the function returns exit code 0 on a freshly-generated manifest — do NOT invoke `--check` against the live `MANIFEST.json` on disk, which is always subject to `audit.jsonl` drift.

- [ ] **After fixing the test, re-run `scripts/run_tests.py --wp DOC-057`** to confirm all tests pass and log the new result.

- [ ] **Re-run `scripts/validate_workspace.py --wp DOC-057`** to confirm clean exit (0).

- [ ] **Recommit** with message `DOC-057: Tester corrections` and re-push branch `DOC-057/document-certification-pipeline-scope`.

---

## Acceptance Criteria Check

| Criterion | Status |
|-----------|--------|
| MANIFEST.json header or generate_manifest.py help text clarifies scope | ✅ PASS — both the module docstring and argparse description name `agent-workbench` as in-scope and `certification-pipeline` as intentionally excluded; MANIFEST.json has a `_scope` field with the same message |
| No agent will expect cert-pipeline files in the manifest | ✅ PASS — the `_scope` field is visible in any raw manifest read, and the `--help` text is explicit |

The underlying implementation is correct. Only the test design needs fixing.

---

## Verdict

**FAIL — return to Developer**

The acceptance criteria are satisfied by the implementation. However, `test_generate_manifest_check_passes` is a new test (not in the regression baseline) that fails on every run due to the live nature of `audit.jsonl`. The WP cannot be marked Done with a failing test. Remove or replace that test, then resubmit for re-review.
