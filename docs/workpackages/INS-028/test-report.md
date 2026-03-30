# Test Report — INS-028: Add macOS source install to CI test matrix

## Verdict: PASS

## Summary

All INS-028 tests pass. The CI workflow YAML is well-formed, secure, and correctly
structured to validate the macOS source install path on every push and pull request
to `main`. One pre-existing regression failure was found in `DOC-008` (unrelated to
this WP) and has been logged as BUG-154.

---

## Scope

| Item | Detail |
|------|--------|
| WP ID | INS-028 |
| Branch | `INS-028/macos-ci-test` |
| Reviewer | Tester Agent |
| Date | 2026-03-30 |
| User Story | US-065 |

---

## Files Reviewed

| File | Status |
|------|--------|
| `.github/workflows/macos-source-test.yml` | PASS — valid, secure, well-structured |
| `tests/INS-028/test_ins028_workflow.py` | PASS — 10 developer tests all pass |
| `docs/workpackages/INS-028/dev-log.md` | PASS — complete, accurate |

---

## Test Results

| Test Run | Type | Tests | Result |
|----------|------|-------|--------|
| TST-2274 — Developer workflow tests | Unit | 10 | 10 passed, 0 failed |
| TST-2275 — Tester edge-case tests | Unit | 19 | 19 passed, 0 failed |
| TST-2276 — Full regression suite | Unit | 178 | 177 passed, 1 pre-existing failure (DOC-008) |

**INS-028 total: 29 passed, 0 failed**

---

## Workflow YAML Review

### Correctness

- **Valid YAML**: Parses cleanly with `yaml.safe_load`. ✓
- **Triggers**: `push` (main), `pull_request` (main), `workflow_dispatch` — correct and complete. ✓
- **Runner**: `macos-14` (Apple Silicon). ✓
- **Checkout**: `actions/checkout@v4` (official, non-deprecated). ✓
- **Python setup**: `actions/setup-python@v5` with `python-version: '3.11'`. ✓
- **Install script**: `bash scripts/install-macos.sh` — explicit bash invocation. ✓
- **Version verification**: Both `agent-launcher --version` and `ts-python --version` verified via full install paths. ✓
- **Test execution**: `pytest tests/ -x --tb=short` using venv Python. ✓
- **Step ordering**: checkout → setup-python → install → verify → test. Correct. ✓
- **All steps named**: Every step has a descriptive `name:` field. ✓

### Security

- **No hardcoded tokens or credentials** found. ✓
- **No `shell: bash`** explicitly set (redundant/inconsistent on macOS). ✓
- **No `continue-on-error: true`** at step or job level — failures propagate correctly. ✓
- **No secrets or API keys** found in workflow file. ✓
- **No unsafe `${{ github.event.* }}` injection vectors** in `run:` blocks. ✓

### Quality

- Workflow name is descriptive: `macOS Source Install Test`. ✓
- Step names are descriptive (≥5 chars, meaningful labels). ✓
- `workflow_dispatch` included for manual debugging. ✓
- Branch triggers are scoped to `main` — not running on every branch. ✓
- `actions/checkout@v4` and `actions/setup-python@v5` are current versions. ✓

---

## Edge-Case Tests Written (19)

| Test | What It Checks |
|------|----------------|
| `test_workflow_uses_actions_checkout` | Uses official `actions/checkout`, not a third-party action |
| `test_workflow_checkout_not_deprecated_v1_v2` | Not using deprecated @v1 or @v2 |
| `test_workflow_setup_python_not_deprecated_v1_v2_v3_v4` | setup-python is v5+ |
| `test_workflow_has_non_empty_name` | Top-level name is non-empty and ≥5 chars |
| `test_all_steps_have_names` | Every step has a `name:` field |
| `test_step_names_are_descriptive` | All step names are ≥5 chars |
| `test_no_explicit_shell_bash_on_steps` | No redundant `shell: bash` declarations |
| `test_no_hardcoded_tokens_in_workflow` | No GitHub/GitLab token patterns found |
| `test_workflow_uses_github_secrets_for_sensitive_data` | No raw 40-char hex strings |
| `test_no_continue_on_error_in_steps` | No step masks failures |
| `test_no_continue_on_error_at_job_level` | No job masks failures |
| `test_workflow_has_workflow_dispatch_trigger` | Manual trigger present |
| `test_push_trigger_targets_main_branch` | Push scoped to `main` |
| `test_pull_request_trigger_targets_main_branch` | PR scoped to `main` |
| `test_checkout_is_first_step` | checkout is step 1 |
| `test_setup_python_before_install_script` | Python set up before install runs |
| `test_pytest_uses_fail_fast_flag` | pytest uses `-x` |
| `test_pytest_uses_short_traceback` | pytest uses `--tb=short` |
| `test_install_script_called_with_bash` | Script invoked with explicit `bash` |

---

## Pre-Existing Failures

| Bug | Location | Description |
|-----|----------|-------------|
| BUG-154 | `tests/DOC-008/test_doc008_read_first_directive.py` | `test_existing_content_preserved` fails because `copilot-instructions.md` is missing `Coding Standards` and `Communication` sections. Pre-existing on `main` — **not introduced by INS-028**. |

---

## Analysis

### Attack Vectors / Security

No security concerns with this workflow. It does not use `${{ github.event.head_commit.message }}`
or other injection-prone event data in `run:` blocks. No secrets required or referenced.
The install path (`~/.local/share/TurbulenceSolutions/...`) is user-local and non-privileged.

### Boundary Conditions

The `[ -t 0 ]` guard in `install-macos.sh` correctly handles non-interactive CI environments
(stdin is not a tty). The workflow correcty relies on this behaviour rather than injecting
environment variables.

### Platform Specifics

The workflow targets `macos-14` (Apple Silicon). The install script and binary paths use
the same `~/.local/share/TurbulenceSolutions/` prefix as documented in US-065. No
Windows/Linux-specific tests are needed here — this is intentionally macOS-only CI.

### Resource Concerns

No resource leaks or background processes started by the workflow definition itself.

---

## Verdict

**PASS** — INS-028 is complete and correct. Setting status to `Done`.
