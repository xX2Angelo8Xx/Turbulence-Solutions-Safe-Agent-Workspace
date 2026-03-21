# Dev Log — SAF-036

**Developer:** Developer Agent
**Date started:** 2026-03-21
**Iteration:** 1

## Objective
Add configuration support for the denial counter in security_gate.py so the lockout threshold and enabled/disabled flag can be configured per workspace via a dedicated config file (`counter_config.json`).

## Implementation Summary
- Renamed `_DENY_THRESHOLD` to `_DENY_THRESHOLD_DEFAULT` and added `_COUNTER_ENABLED_DEFAULT` constant.
- Added `_COUNTER_CONFIG_NAME` constant pointing to `counter_config.json`.
- Implemented `_load_counter_config(scripts_dir)` function that reads the config file with full error handling: missing file, corrupt JSON, invalid types, negative threshold — all fall back to defaults (enabled=True, threshold=20).
- Modified `main()` to load config once at start, then conditionally:
  - When counter is enabled: use configured threshold for lock check and deny messaging.
  - When counter is disabled: skip all counter logic (no state loading, no incrementing, no "Block N of M" messages).
- Created default `counter_config.json` in the template directory.
- Updated integrity hashes via `update_hashes.py`.
- Updated SAF-035 tests to reference renamed `_DENY_THRESHOLD_DEFAULT` constant.
- Updated global `tests/conftest.py` to mock `_load_counter_config` for test isolation.

## Files Changed
- `templates/coding/.github/hooks/scripts/security_gate.py` — Added config loader, modified main() for configurable counter
- `templates/coding/.github/hooks/scripts/counter_config.json` — New default config file
- `tests/conftest.py` — Added `_load_counter_config` mock to global fixture
- `tests/SAF-035/test_saf035_denial_counter.py` — Updated `_DENY_THRESHOLD` → `_DENY_THRESHOLD_DEFAULT`
- `tests/SAF-035/test_saf035_tester_edge_cases.py` — Updated `_DENY_THRESHOLD` → `_DENY_THRESHOLD_DEFAULT`
- `tests/SAF-036/__init__.py` — New test package init
- `tests/SAF-036/conftest.py` — No-op override of global fixture for SAF-036 tests
- `tests/SAF-036/test_saf036_counter_config.py` — 16 tests covering all requirements
- `docs/workpackages/workpackages.csv` — Status update to In Progress

## Tests Written
- `TestDefaultConfigNoFile::test_defaults_when_no_config_file` — Validates defaults when no config file exists
- `TestCustomThreshold::test_custom_threshold_locks_at_5` — Validates custom threshold=5 locks at 5 denials
- `TestDisabledCounter::test_disabled_counter_no_block_messages` — Validates config returns disabled
- `TestDisabledCounter::test_disabled_counter_main_skips_counter` — Validates main() produces no Block N of M when disabled
- `TestDisabledCounter::test_disabled_counter_no_state_file_written` — Validates no state file access when disabled
- `TestCorruptConfigFallback::test_corrupt_json_falls_back` — Corrupt JSON falls back to defaults
- `TestCorruptConfigFallback::test_array_config_falls_back` — JSON array falls back
- `TestCorruptConfigFallback::test_empty_file_falls_back` — Empty file falls back
- `TestCorruptConfigFallback::test_invalid_types_fall_back` — Non-bool/non-int types fall back
- `TestCorruptConfigFallback::test_negative_threshold_falls_back` — Threshold < 1 falls back
- `TestCorruptConfigFallback::test_float_threshold_falls_back` — Float threshold falls back
- `TestMissingConfigFallback::test_nonexistent_directory` — Nonexistent dir returns defaults
- `TestMissingConfigFallback::test_empty_directory` — Empty dir returns defaults
- `TestExtraKeysIgnored::test_extra_keys_are_ignored` — Extra JSON keys silently ignored
- `TestConfigFileExistsInTemplate::test_template_counter_config_exists` — Config file exists in template
- `TestConfigFileExistsInTemplate::test_template_counter_config_valid` — Template config has correct structure and values

## Known Limitations
- The config file is read from the scripts directory (same directory as security_gate.py), not from a user-configurable location. GUI-019/GUI-020 will write values during project creation.
