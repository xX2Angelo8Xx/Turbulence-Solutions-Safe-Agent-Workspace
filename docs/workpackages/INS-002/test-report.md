# Test Report — INS-002

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 2

## Summary

Re-review after BUG-002 fix. `pyproject.toml` now contains the correct `build-backend = "setuptools.build_meta"`. All required fields are present and valid. The full test suite (96 tests) passes with zero failures. Three additional edge-case tests were added by the Tester and also pass.

## pyproject.toml Verification

| Field | Expected | Actual | Result |
|-------|----------|--------|--------|
| `build-backend` | `setuptools.build_meta` | `setuptools.build_meta` | PASS |
| `[build-system] requires` | setuptools with version bounds | `setuptools>=68,<69` | PASS |
| `project.name` | `agent-environment-launcher` | `agent-environment-launcher` | PASS |
| `project.version` | matches `config.VERSION` (`0.1.0`) | `0.1.0` | PASS |
| `project.description` | present | present | PASS |
| `requires-python` | `>=3.11` | `>=3.11` | PASS |
| `dependencies` | `customtkinter>=5,<6` | `customtkinter>=5,<6` | PASS |
| `optional-dependencies.dev` | pyinstaller + pytest with bounds | `pyinstaller>=6,<7`, `pytest>=8,<9` | PASS |
| `project.scripts` | `agent-launcher = launcher.main:main` | `agent-launcher = "launcher.main:main"` | PASS |
| `[tool.setuptools.packages.find] where` | `["src"]` | `["src"]` | PASS |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-023 `test_pyproject_exists` | Unit | Pass | |
| TST-024 `test_pyproject_is_valid_toml` | Unit | Pass | |
| TST-025 `test_pyproject_project_name` | Unit | Pass | |
| TST-026 `test_pyproject_version_matches_config` | Unit | Pass | |
| TST-027 `test_pyproject_requires_python` | Unit | Pass | |
| TST-028 `test_pyproject_customtkinter_dependency` | Unit | Pass | |
| TST-029 `test_pyproject_dev_dependencies` | Unit | Pass | |
| TST-030 `test_pyproject_entry_point` | Unit | Pass | |
| TST-031 `test_pyproject_build_system` | Unit | Pass | Asserts exact value `setuptools.build_meta` — BUG-002 confirmed fixed |
| TST-032 `test_pyproject_src_layout` | Unit | Pass | |
| TST-114 `test_pyproject_build_system_requires` | Unit | Pass | Tester-added: verifies setuptools bounds in `[build-system] requires` |
| TST-115 `test_pyproject_requires_python_exact` | Unit | Pass | Tester-added: guards against looser `>=3.9` style bound |
| TST-116 `test_pyproject_customtkinter_upper_bound` | Unit | Pass | Tester-added: major-version upper bound `<6` present |
| TST-117 Full suite (96 tests) | Regression | Pass | 96/96 — no regressions in INS-001 or SAF-001 suites |

## Bugs Found

None. BUG-002 (invalid `build-backend`) was the previously reported defect. It is confirmed fixed.

## TODOs for Developer

None.

## Verdict

PASS — mark INS-002 as Done.

`build-backend = "setuptools.build_meta"` is correct. All required packaging fields are present with appropriate version pins. The entry point resolves to an existing callable. The src layout is correctly configured. 96/96 tests pass across INS-001, INS-002, and SAF-001 suites. No regressions.
