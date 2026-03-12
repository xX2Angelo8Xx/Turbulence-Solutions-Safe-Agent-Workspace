# Dev Log — INS-009

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

Implement a silent GitHub Releases version check on app launch. Query the GitHub Releases API for the latest version, compare it against the current version using semantic versioning, and return an update-available flag. The UI notification is out of scope (handled by GUI-009/GUI-010).

## Implementation Summary

- Added three constants to `src/launcher/config.py`: `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, and `GITHUB_RELEASES_URL` (derived f-string). No existing constants were removed or modified.
- Replaced the stub in `src/launcher/core/updater.py` with a full implementation:
  - `parse_version(version_str)` — strips a leading "v"/"V", splits on ".", converts each segment to `int` (non-numeric segments become 0), returns a `tuple[int, ...]`.
  - `check_for_update(current_version)` — opens `GITHUB_RELEASES_URL` via `urllib.request.urlopen` with a 5-second timeout, reads and JSON-parses the response, extracts `tag_name`, compares tuples from `parse_version`, returns `(True, latest)` when remote is newer, otherwise `(False, latest_or_current)`. All exceptions are silently caught; the function never raises.
- Only stdlib modules used (`json`, `urllib.request`, `urllib.error`). No `requests` or `packaging` dependency added.
- Restored after parallel workgroup branch conflict that wiped the previous implementation.

## Files Changed

- `src/launcher/config.py` — added `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_RELEASES_URL` constants
- `src/launcher/core/updater.py` — replaced stub with full `parse_version` + `check_for_update` implementation

## Tests Written

Located in `tests/INS-009/test_ins009_version_check.py` (21 tests across 5 test classes):

**TestParseVersion (10 tests)**
- `test_basic_semver` — "1.2.3" → (1, 2, 3)
- `test_leading_v_stripped` — "v0.2.0" → (0, 2, 0)
- `test_leading_v_uppercase_stripped` — "V1.0.0" → (1, 0, 0)
- `test_zero_version` — "0.0.0" → (0, 0, 0)
- `test_single_component` — "3" → (3,)
- `test_two_components` — "1.5" → (1, 5)
- `test_large_numbers` — "10.20.300" → (10, 20, 300)
- `test_non_numeric_part_becomes_zero` — "1.2.alpha" → (1, 2, 0)
- `test_v_only_stripped_not_middle` — "v2.3.4" → (2, 3, 4)
- `test_current_version_constant` — VERSION from config is parseable

**TestCheckForUpdateAvailable (5 tests)**
- `test_newer_patch_version` — remote 0.2.0 vs local 0.1.0
- `test_newer_minor_version` — remote 1.0.0 vs local 0.9.9
- `test_newer_major_version` — remote 2.0.0 vs local 1.99.99
- `test_tag_without_v_prefix` — tag "0.5.0" (no v)
- `test_latest_version_string_returned` — returned string matches stripped tag

**TestCheckForUpdateNotAvailable (4 tests)**
- `test_same_version_no_update`
- `test_older_remote_no_update`
- `test_same_version_returns_latest_string`
- `test_local_newer_than_remote`

**TestCheckForUpdateErrorHandling (11 tests)**
- `test_network_error_returns_false` — OSError
- `test_url_error_returns_false` — urllib.error.URLError
- `test_http_error_returns_false` — urllib.error.HTTPError 404
- `test_malformed_json_returns_false` — non-JSON bytes
- `test_missing_tag_name_key_returns_false` — dict without tag_name
- `test_timeout_returns_false` — TimeoutError
- `test_empty_response_returns_false` — empty bytes
- `test_null_json_response_returns_false` — JSON null
- `test_no_exception_raised_on_error` — verifies silence
- `test_returns_current_version_on_error` — returns passed-in version

**TestConfigConstants (8 tests)**
- `test_github_repo_owner_exists`
- `test_github_repo_name_exists`
- `test_github_releases_url_exists`
- `test_github_releases_url_contains_owner`
- `test_github_releases_url_contains_repo_name`
- `test_github_releases_url_is_api_endpoint`
- `test_github_releases_url_correct_format`
- `test_existing_constants_unchanged`

## Known Limitations

- Version comparison uses simple integer-tuple ordering; pre-release suffixes (e.g. "1.0.0-beta.1") are not handled — non-numeric segment is treated as 0.
- The function makes a real HTTP call unless mocked; the 5-second timeout prevents UI hangs but callers should run it off the main thread.
