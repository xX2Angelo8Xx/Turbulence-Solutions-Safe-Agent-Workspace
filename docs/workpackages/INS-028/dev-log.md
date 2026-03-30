# Dev Log — INS-028: Add macOS source install to CI test matrix

## Status
In Progress

## Assigned To
Developer Agent

## Goal
Add a CI workflow job that validates the macOS source install path on every push to main,
pull request, and release tag. Ensures `scripts/install-macos.sh` (INS-026) does not regress.

## Implementation

### Decision: Separate workflow file
Created `.github/workflows/macos-source-test.yml` rather than modifying `release.yml`.
Rationale:
- The source-install test should run on every `push` to `main` and `pull_request`, not just
  on release tags. Embedding it in `release.yml` would limit coverage.
- Keeps release-build concerns separate from install-script testing.
- Easier to iterate and disable independently.

### Workflow triggers
- `push` to `main`
- `pull_request` targeting `main`
- `workflow_dispatch` (manual trigger)

### Job: `macos-source-install`
Runs on `macos-14` (Apple Silicon runner).

Steps:
1. `actions/checkout@v4` — full checkout
2. `actions/setup-python@v5` with `python-version: '3.11'`
3. Run `bash scripts/install-macos.sh` in non-interactive mode (stdin is not a tty in CI,
   so the script's `[ -t 0 ]` guard already skips the PATH prompt)
4. Verify `agent-launcher --version` exits 0 using the full install path
5. Verify `ts-python --version` exits 0 using the full install path
6. Run `python -m pytest tests/ -x --tb=short` using the venv Python

### Non-interactive handling
`install-macos.sh` already uses `[ -t 0 ]` to detect interactive sessions. In CI, stdin
is not connected to a tty, so the PATH-modification prompt is auto-skipped. No environment
variable injection needed.

## Files Changed
- `.github/workflows/macos-source-test.yml` — new CI workflow
- `docs/workpackages/workpackages.csv` — status update
- `docs/workpackages/INS-028/dev-log.md` — this file
- `tests/INS-028/test_ins028_workflow.py` — tests validating workflow file structure

## Tests Written
All tests in `tests/INS-028/test_ins028_workflow.py`:
- `test_workflow_file_exists` — YAML file is present
- `test_workflow_is_valid_yaml` — file parses as valid YAML
- `test_workflow_references_macos14_runner` — job uses `macos-14`
- `test_workflow_calls_install_script` — step runs `scripts/install-macos.sh`
- `test_workflow_runs_pytest` — step runs `pytest`
- `test_workflow_uses_setup_python` — uses `actions/setup-python`
- `test_workflow_python_version_311_or_newer` — Python 3.11+
- `test_workflow_has_correct_triggers` — push/pull_request triggers present
- `test_workflow_verifies_agent_launcher` — step checks `agent-launcher --version`
- `test_workflow_verifies_ts_python` — step checks `ts-python --version`

## Known Limitations
- The workflow cannot be locally executed (requires GitHub runner). Tests validate file
  structure and content only.
