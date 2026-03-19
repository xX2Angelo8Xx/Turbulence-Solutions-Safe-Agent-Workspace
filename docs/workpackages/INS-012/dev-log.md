# Dev Log — INS-012

**Developer:** Developer Agent
**Date started:** 2026-03-11
**Iteration:** 1

## Objective

Create `.gitignore` at the repository root to prevent Python bytecache (`__pycache__/`, `*.pyc`, `*.pyo`), build artifacts (`.eggs/`, `*.egg-info/`, `dist/`, `build/`), test cache (`.pytest_cache/`), virtual environments (`.venv/`, `env/`, `venv/`), generated PyInstaller spec files (`*.spec`), and OS artifacts (`.DS_Store`, `Thumbs.db`) from being tracked by git.

## Implementation Summary

A `.gitignore` file was already present at the repository root, having been created manually on 2026-03-10. A full audit was performed to verify that all required exclusion patterns per the WP spec are present. All 14 required patterns were confirmed present and correctly formatted. No content changes were necessary.

Decisions:
- The existing file also includes `.vscode/` (VS Code developer-local settings). This is a sensible additional exclusion that does not conflict with the WP requirements and was retained.
- All section comments (`# Python bytecache`, `# Eggs / packaging artifacts`, etc.) were retained for readability.

## Files Changed

- `.gitignore` — verified all required exclusions present; no content change required (file was correctly created manually)

## Tests Written

- `tests/INS-012/test_ins012_gitignore.py`
  - `test_gitignore_exists` — verifies `.gitignore` file exists at repository root
  - `test_pycache_excluded` — verifies `__pycache__/` pattern is present
  - `test_pyc_excluded` — verifies `*.pyc` pattern is present
  - `test_pyo_excluded` — verifies `*.pyo` pattern is present
  - `test_eggs_dir_excluded` — verifies `.eggs/` pattern is present
  - `test_egg_info_excluded` — verifies `*.egg-info/` pattern is present
  - `test_dist_excluded` — verifies `dist/` pattern is present
  - `test_build_excluded` — verifies `build/` pattern is present
  - `test_pytest_cache_excluded` — verifies `.pytest_cache/` pattern is present
  - `test_venv_excluded` — verifies `.venv/` pattern is present
  - `test_env_excluded` — verifies `env/` pattern is present
  - `test_venv_plain_excluded` — verifies `venv/` pattern is present
  - `test_spec_excluded` — verifies `*.spec` pattern is present
  - `test_ds_store_excluded` — verifies `.DS_Store` pattern is present
  - `test_thumbs_db_excluded` — verifies `Thumbs.db` pattern is present
  - `test_no_duplicate_patterns` — verifies no pattern appears more than once
  - `test_gitignore_git_recognises_file` — verifies `git check-ignore` identifies a `.pyc` file as ignored
  - `test_pycache_tracked_files_absent` — verifies no `__pycache__/` paths are currently tracked in the git index

## Test Results

- **INS-012 suite:** 22/22 pass (TST-125 – TST-146)
- **Full regression suite:** 117/118 — 1 pre-existing SAF-001 failure (`test_decide_project_sibling_prefix_bypass`) confirmed present before this branch was created; not caused by INS-012 changes. Logged as TST-147.
- Environment: Windows 11 + Python 3.11.9, pytest 8.4.2

## Known Limitations

- Tests validate pattern presence and git recognition but cannot simulate a full commit cycle to check that future commits would never include excluded files. This is an inherent limitation of static `.gitignore` testing.
- Pre-existing SAF-001 regression (`test_decide_project_sibling_prefix_bypass`) is outside the scope of this WP and will require a separate fix in the SAF workstream.
