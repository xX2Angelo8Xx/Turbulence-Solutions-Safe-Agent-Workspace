# Dev Log — FIX-108: Add PyYAML to dev dependencies

## Metadata
- **WP ID**: FIX-108
- **Agent**: Developer Agent
- **Date**: 2026-04-05
- **Status**: In Progress

## Prior Art Check
No ADRs found in `docs/decisions/index.jsonl` related to Python dependency management or PyYAML specifically.

## Problem Summary
47 test modules perform `import yaml` at module-level. `pyyaml` was installed locally but not declared in `pyproject.toml` dev optional-dependencies. On CI runners that only do `pip install -e ".[dev]"`, PyYAML is absent, causing collection errors for all 47 modules.

## Implementation

### Change Made
**File**: `pyproject.toml`

Added `pyyaml>=6,<7` to the `[project.optional-dependencies]` dev list:

```toml
dev = [
    "pyinstaller>=6,<7",
    "pytest>=8,<9",
    "pyyaml>=6,<7",
]
```

## Tests Written
- `tests/FIX-108/test_fix108_pyyaml_dep.py`
  - `test_pyyaml_in_pyproject_dev_deps` — verifies `pyyaml` appears in `pyproject.toml` dev deps
  - `test_yaml_import_succeeds` — verifies `import yaml` works
  - `test_yaml_version_gte_6` — verifies yaml version >= 6

## Files Changed
- `pyproject.toml` — added `pyyaml>=6,<7` to dev deps
- `tests/FIX-108/test_fix108_pyyaml_dep.py` — new test file

## Result
All FIX-108 tests pass. Previously-failing CI modules (INS-013, DOC-019, FIX-010, MNT-005) now collect cleanly.
