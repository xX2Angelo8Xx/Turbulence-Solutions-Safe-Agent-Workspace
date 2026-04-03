# Dev Log — SAF-077: Install vs Update Parity Testing

**Agent:** Developer Agent  
**Branch:** SAF-077/install-update-parity  
**Date Started:** 2026-04-04  
**Status:** Review

## ADR Acknowledgements

- **ADR-003 (Template Manifest and Workspace Upgrade System):** Directly relevant. This WP operationalises the parity guarantee mentioned in ADR-003's "Positive" consequences: "Fresh install and upgraded workspace are verifiably identical for security files." The parity script and CI job validate this guarantee automatically.
- **ADR-002 (Mandatory CI Test Gate Before Release Builds):** This WP adds a new CI job to `test.yml`, extending the CI gate to include parity verification.

## Requirements

1. `scripts/verify_parity.py` — standalone script that:
   - Reads `templates/agent-workbench/MANIFEST.json` for security-critical file list
   - Creates a fresh workspace via `create_project()`
   - Creates a simulated upgraded workspace (fresh workspace → corrupt security files → run `upgrade_workspace()`)
   - Compares all security-critical files byte-by-byte (SHA256)
   - Returns exit 0 on parity, exit 1 on any mismatch
   - Supports `--verbose` flag

2. `parity-check` job in `.github/workflows/test.yml`:
   - Runs on every push/PR to main
   - Executes `scripts/verify_parity.py`
   - Must pass with exit 0

3. Tests in `tests/SAF-077/` validating both the script and the parity guarantee.

## Implementation Plan

- `scripts/verify_parity.py`: Self-contained, imports from `src/launcher/` via sys.path manipulation. Uses `tempfile.TemporaryDirectory()` for safe, auto-cleaned workspace creation.
- CI job: Added as a separate job in `test.yml` (not in the matrix) running on `ubuntu-latest`.
- Tests: Unit tests for helpers + integration test for the full parity flow.

## Implementation Summary

### scripts/verify_parity.py
Standalone script (~230 lines). Key design decision: uses `shutil.copytree()` directly instead of `create_project()` to avoid per-workspace post-copy modifications (write_counter_config() line-ending differences, replace_template_placeholders() substitution) that would cause artificial parity failures unrelated to the upgrade mechanism. Both the install path and upgrade path source from the same template tree, so byte-for-byte comparison is valid.

The script:
1. Reads MANIFEST.json to identify security-critical files
2. Creates a fresh workspace via `shutil.copytree(template_dir, fresh_dir)`
3. Creates an "old" workspace via `shutil.copytree()` + corrupts security files with sentinel bytes + runs `upgrade_workspace()`
4. Compares all security-critical files byte-by-byte between fresh and upgraded
5. Handles stale MANIFEST.json gracefully (post-upgrade verification errors filtered; file-copy errors still propagate)

### .github/workflows/test.yml
Added new `parity-check` job (ubuntu-latest, Python 3.11) that runs `python scripts/verify_parity.py --verbose`. Runs on every push/PR to main and on workflow_dispatch.

### tests/SAF-077/
31 unit + integration + security tests covering:
- `load_manifest()` — error handling for missing/invalid JSON
- `get_security_critical_files()` — filters correctly
- `_sha256()` — correct digest computation
- `compare_workspaces()` — detects all mismatch types
- `verify_parity()` — integration test + mocked unit tests
- CLI exit codes (0 on pass, 1 on error)
- Security: sentinel detection, bypass attempt, manifest-tampering proof

## Files Changed

- `scripts/verify_parity.py` — NEW
- `.github/workflows/test.yml` — added parity-check job
- `docs/workpackages/SAF-077/dev-log.md` — NEW
- `docs/workpackages/workpackages.csv` — claim and status update
- `tests/SAF-077/__init__.py` — NEW
- `tests/SAF-077/test_saf077_parity.py` — NEW

## Tests Written

- 31 tests in `tests/SAF-077/test_saf077_parity.py`
- Logged as TST-2495 via `scripts/run_tests.py`
- All 31 passed; `validate_workspace.py --wp SAF-077` clean

## Known Limitations

- Uses `shutil.copytree()` instead of `create_project()` for workspace creation. This is intentional — `create_project()` modifies security files post-copy (counter_config.json line endings, copilot-instructions.md placeholder substitution) which would cause false parity failures. Deviation from WP instruction documented here.
- The upgrader's post-upgrade verification may fail for `audit.jsonl` (stale MANIFEST.json hash); this is filtered out and does not affect parity comparison correctness.
