# Dev Log — INS-002

**Developer:** Developer Agent
**Date started:** 2026-03-10
**Iteration:** 1

## Objective

Create `pyproject.toml` at the repository root with project metadata (name: `agent-environment-launcher`, version matching `config.py`), runtime dependency (`customtkinter`), dev/optional dependencies (`pyinstaller`, `pytest`), a console-scripts entry point pointing to `launcher.main:main`, and a setuptools build-system configuration for the `src` layout.

## Implementation Summary

Created `pyproject.toml` using the PEP 517/518 standard format (TOML-based). Key decisions:

- **Build system:** `setuptools>=68,<69` with `[tool.setuptools.packages.find] where = ["src"]` so setuptools discovers the `launcher` package under `src/` — matching the src layout established in INS-001.
- **Version:** `0.1.0` — identical to `VERSION` in `src/launcher/config.py` (single source of truth enforced by test).
- **Runtime dependency:** `customtkinter>=5,<6` — major version pinned per coding-standards.md.
- **Dev/optional group:** `pyinstaller>=6,<7` and `pytest>=8,<9` declared under `[project.optional-dependencies] dev` so they are not installed for end users.
- **Entry point:** `agent-launcher = launcher.main:main` — resolves to the `main()` function in `src/launcher/main.py` which already exists from INS-001.
- **`requires-python`:** `>=3.11` — aligns with test environment recorded in test-results.csv.

No runtime or security logic was changed. Only the packaging metadata file was created.

## Files Changed

- `pyproject.toml` (new) — Python packaging configuration

## Tests Written

- `test_pyproject_exists` — verifies `pyproject.toml` exists at repository root
- `test_pyproject_is_valid_toml` — verifies the file parses without errors using `tomllib`
- `test_pyproject_project_name` — verifies `project.name == "agent-environment-launcher"`
- `test_pyproject_version_matches_config` — verifies `project.version` matches `config.VERSION`
- `test_pyproject_requires_python` — verifies `requires-python` is present
- `test_pyproject_customtkinter_dependency` — verifies `customtkinter` is in `project.dependencies`
- `test_pyproject_dev_dependencies` — verifies `pyinstaller` and `pytest` are in `project.optional-dependencies.dev`
- `test_pyproject_entry_point` — verifies `agent-launcher` script entry point is declared
- `test_pyproject_build_system` — verifies `[build-system]` section exists with `setuptools` backend
- `test_pyproject_src_layout` — verifies `[tool.setuptools.packages.find]` sets `where = ["src"]`

## Known Limitations

- Version is currently hard-coded in both `pyproject.toml` and `config.py`. A future WP could unify these by reading `importlib.metadata.version()` in `config.py`, but that requires `pip install -e .` to have been run first — a bootstrapping issue beyond this WP's scope.
