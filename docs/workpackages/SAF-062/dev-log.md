# SAF-062 — Dev Log

## Workpackage
**ID:** SAF-062  
**Title:** Fix Test-Path for dot-prefixed workspace root paths  
**Status:** In Progress  
**Branch:** SAF-062/test-path-fallback  
**Assigned To:** Developer Agent

## Description
`test-path` was missing from `_PROJECT_FALLBACK_VERBS` in `security_gate.py`,
causing `Test-Path .venv` (and similar dot-prefixed workspace root paths) to be
incorrectly denied.  The fix adds `"test-path"` to the frozenset, giving it the
same project-folder fallback as `get-childitem`, `ls`, etc.

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — added `"test-path"` to `_PROJECT_FALLBACK_VERBS`
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — SHA256 hashes updated by `update_hashes.py`
- `tests/SAF-062/__init__.py` — test package marker
- `tests/SAF-062/conftest.py` — local conftest (no-op override for hook state write prevention)
- `tests/SAF-062/test_saf062_test_path_fallback.py` — unit + regression tests

## Implementation Notes
The `_PROJECT_FALLBACK_VERBS` frozenset (line ~1565) lists read/execute verbs
that receive a second-chance resolution against the project folder when the
initial zone check returns deny.  `test-path` is a read-only PowerShell cmdlet
(equivalent to `Test-Path` — checks file existence) so it belongs in the
same read group as `get-childitem`, `gci`, `ls`, `dir`.  Added after the
`get-childitem` group comment on a new line, consistent with SAF-041 style.

`update_hashes.py` was run immediately after the edit to refresh the embedded
SHA256 hashes inside `security_gate.py`.

## Tests Written
1. `test_test_path_in_fallback_verbs` — `"test-path"` present in `_PROJECT_FALLBACK_VERBS`
2. `test_test_path_dot_venv_allowed` — `Test-Path .venv` is allowed (project fallback)
3. `test_test_path_dot_env_allowed` — `Test-Path .env` is allowed (project fallback)
4. `test_test_path_github_denied` — `Test-Path .github/hooks/scripts/security_gate.py` is denied
5. `test_test_path_project_file_allowed` — `Test-Path Project/some-file.txt` is allowed

## Test Results
All 5 tests pass.  See `docs/test-results/test-results.csv` for logged entry.

## Iteration 1
Initial implementation — no prior iterations.
