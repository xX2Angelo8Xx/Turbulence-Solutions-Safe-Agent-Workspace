# Dev Log — INS-009

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective

On app launch, silently query the GitHub Releases API for the latest version; compare against the current version using semantic versioning; return an update-available flag. Version check runs silently on launch and correctly identifies when a newer release exists.

## Implementation Summary

Replaced the `check_for_update` stub in `src/launcher/core/updater.py` with a full implementation that:

- Defines `UpdateCheckResult`, a `collections.namedtuple` with `update_available` and `latest_version` fields. Maintains backward-compatible 2-tuple unpacking so existing INS-001 tests continue to pass.
- `_parse_version(version_str)` — strips leading `v`, splits on `.`, parses the numeric prefix of each component, and pads to 3 components. Handles `v2.0.0`, `1.2`, `3`, and pre-release suffixes like `1.2.3-beta`.
- `_is_newer(latest, current)` — delegates to `_parse_version` for both strings and uses Python tuple comparison for correct semver ordering.
- `_fetch_latest_version()` — queries `https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest` with a `TurbulenceSolutions-Launcher` User-Agent and a configurable `GITHUB_API_TIMEOUT`. Validates the response is a dict with a non-empty `tag_name` string. Returns the version string (stripped of `v`) or `None` on any error. All exceptions are caught silently.
- `check_for_update(current_version)` — calls `_fetch_latest_version()`, returns `UpdateCheckResult(False, current_version)` if None, otherwise compares and returns the appropriate result. Never raises.

Added three constants to `src/launcher/config.py`:
- `GITHUB_OWNER = "TurbulenceSolutions"`
- `GITHUB_REPO = "agent-environment-launcher"`
- `GITHUB_API_TIMEOUT = 5`

Only stdlib is used (`json`, `urllib.request`, `urllib.error`, `collections`).

## Files Changed

- `src/launcher/config.py` — added GITHUB_OWNER, GITHUB_REPO, GITHUB_API_TIMEOUT
- `src/launcher/core/updater.py` — replaced stub with full implementation

## Tests Written

- `tests/INS-009/__init__.py` — package marker
- `tests/INS-009/test_ins009_version_check.py` — 21 tests:
  - `test_update_check_result_is_namedtuple` — UpdateCheckResult is a tuple subclass
  - `test_update_check_result_has_update_available_field` — field accessible by name
  - `test_update_check_result_has_latest_version_field` — field accessible by name
  - `test_update_check_result_tuple_unpacking` — 2-tuple unpack works at UpdateCheckResult level
  - `test_parse_version_basic_semver` — "1.2.3" → (1, 2, 3)
  - `test_parse_version_v_prefix_stripped` — "v2.0.0" → (2, 0, 0)
  - `test_parse_version_two_components_padded` — "1.4" → (1, 4, 0)
  - `test_parse_version_one_component_padded` — "3" → (3, 0, 0)
  - `test_is_newer_major_bump` — 2.0.0 > 1.9.9
  - `test_is_newer_minor_bump` — 1.1.0 > 1.0.9
  - `test_is_newer_patch_bump` — 1.0.1 > 1.0.0
  - `test_is_newer_same_version_returns_false` — 1.0.0 not newer than 1.0.0
  - `test_fetch_latest_version_returns_version_string` — mocked response → "1.2.3"
  - `test_fetch_latest_version_uses_https` — _API_URL starts with "https://"
  - `test_fetch_latest_version_timeout_forwarded` — urlopen called with timeout=GITHUB_API_TIMEOUT
  - `test_fetch_latest_version_network_error_returns_none` — OSError → None
  - `test_fetch_latest_version_http_error_returns_none` — HTTPError 404 → None
  - `test_fetch_latest_version_missing_tag_name_returns_none` — dict without tag_name → None
  - `test_fetch_latest_version_empty_tag_name_returns_none` — tag_name="" → None
  - `test_check_for_update_returns_true_when_newer` — 2.0.0 > 1.0.0 → UpdateCheckResult(True, "2.0.0")
  - `test_check_for_update_network_failure_returns_no_update` — None fetch → (False, current)

## Test Results

- INS-009: 21/21 pass
- Full regression: 493/495 pass (2 pre-existing failures in INS-004 and INS-012, unrelated to this WP)

## Known Limitations

- The INS-001 test `test_updater_stub_returns_no_update` calls `check_for_update("0.1.0")` without a mock. It passes because the GitHub repo has no public releases (API returns 404 → None → no update). If a real "0.1.0" release is ever published, this test will need review.
- `_fetch_latest_version` checks only the `latest` release endpoint; pre-releases are ignored by design.

## Iteration 2 — 2026-03-12

### Context
A previous iteration created some files that were lost due to a file conflict. This iteration re-applies all changes from scratch.

### Tester Feedback Addressed
- N/A — Iteration 2 is a full re-implementation after file-conflict loss, not a Tester revision cycle.

### Additional Changes
- `src/launcher/config.py` — re-added GITHUB_OWNER, GITHUB_REPO, GITHUB_API_TIMEOUT (had been lost)
- `src/launcher/core/updater.py` — full implementation re-applied (stub had been restored)
- `tests/INS-009/__init__.py` — recreated (had been lost)
- `tests/INS-009/test_ins009_version_check.py` — recreated (had been lost)
- `docs/workpackages/INS-009/dev-log.md` — created (had been lost)

### Tests Added/Updated
- All 21 INS-009 tests — recreated identically; 21/21 pass
