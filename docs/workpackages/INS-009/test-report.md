# Test Report — INS-009

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

---

## Summary

The workpackage was submitted for review but the implementation is a **stub only**.
`src/launcher/core/updater.py` contains no real code: `check_for_update()` ignores
its argument and unconditionally returns `(False, current_version)`. No `_API_URL`
constant exists, no network call is made, no version comparison is performed, no
`dev-log.md` was written, and no developer tests were provided.

The 2-tuple interface and silent-failure contract technically hold by accident
(the stub returns early without touching the network), but all functional
requirements of US-015 criterion 1 are unmet.

**Verdict: FAIL — return to Developer.**

---

## Artefacts Reviewed

| Artefact | Exists? | Notes |
|----------|---------|-------|
| `docs/workpackages/INS-009/dev-log.md` | **NO** | Developer never created it |
| `src/launcher/core/updater.py` | YES — stub | 17-line file; `check_for_update` returns `(False, current_version)` always |
| `src/launcher/config.py` | YES — incomplete | Only `APP_NAME` and `VERSION`; no GitHub repo constants, no `_API_URL` |
| `tests/INS-009/test_ins009_version_check.py` | **NO** | Developer wrote no tests |

---

## Tests Executed

All 44 tests are Tester-authored (no developer tests existed).
Run: `python -m pytest tests/INS-009/ -v --tb=short`

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TestInterfaceContract::test_function_is_callable | Unit | PASS | Stub callable |
| TestInterfaceContract::test_returns_tuple | Unit | PASS | Stub returns tuple |
| TestInterfaceContract::test_returns_two_element_tuple | Unit | PASS | Tuple length 2 |
| TestInterfaceContract::test_first_element_is_bool | Unit | PASS | First elem is bool |
| TestInterfaceContract::test_second_element_is_str | Unit | PASS | Second elem is str |
| TestInterfaceContract::test_tuple_unpack_compatible | Unit | PASS | Unpack works |
| TestApiUrlSecurity::test_api_url_attribute_exists | Security | **FAIL** | `_API_URL` missing from module |
| TestApiUrlSecurity::test_api_url_starts_with_https | Security | **FAIL** | No `_API_URL`; falls back to `""` |
| TestApiUrlSecurity::test_api_url_not_plain_http | Security | PASS | Trivially (no URL exists) |
| TestApiUrlSecurity::test_api_url_targets_github_api | Security | **FAIL** | No `_API_URL` |
| TestApiUrlSecurity::test_api_url_references_releases_endpoint | Security | **FAIL** | No `_API_URL` |
| TestNoDependencies::test_source_does_not_import_requests | Unit | PASS | No third-party imports |
| TestNoDependencies::test_source_uses_urllib_for_http | Unit | **FAIL** | `urllib` not in source — stub makes no HTTP call |
| TestSilentErrorHandling::test_url_error_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_http_404_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_http_500_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_timeout_error_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_generic_exception_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_invalid_json_response_caught_silently | Unit | PASS | Stub never calls network |
| TestSilentErrorHandling::test_empty_current_version_string_no_raise | Unit | PASS | Stub ignores input |
| TestSilentErrorHandling::test_whitespace_padded_version_no_raise | Unit | PASS | Stub ignores input |
| TestVersionComparison::test_newer_major_version_sets_flag_true | Unit | **FAIL** | Stub always returns False |
| TestVersionComparison::test_newer_minor_version_sets_flag_true | Unit | **FAIL** | Stub always returns False |
| TestVersionComparison::test_newer_patch_version_sets_flag_true | Unit | **FAIL** | Stub always returns False |
| TestVersionComparison::test_same_version_flag_false | Unit | PASS | Stub coincidentally returns False |
| TestVersionComparison::test_older_api_version_flag_false | Unit | PASS | Stub coincidentally returns False |
| TestVersionComparison::test_v_prefix_stripped_before_comparison | Unit | **FAIL** | Stub always returns False |
| TestVersionComparison::test_latest_version_string_returned_non_empty | Unit | PASS | Stub echoes current_version |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1.0.0-alpha] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1.0.0-beta] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1.0.0-rc1] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1.0.0-rc.2] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1.2] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v1] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[v999.999.999] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[1.0.0] | Unit | PASS | Stub ignores API mock |
| TestVersionParsingEdgeCases::test_unusual_tag_does_not_raise[1.2.3.4] | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_missing_tag_name_field | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_empty_string_tag_name | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_null_tag_name | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_integer_tag_name | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_response_is_json_array_not_object | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_empty_json_object | Unit | PASS | Stub ignores API mock |
| TestResponseValidation::test_extra_fields_do_not_break_parsing | Unit | PASS | Stub ignores API mock |

**INS-009 suite result: 35 pass / 9 fail**

Full regression run (all WPs, excluding INS-004 collection error):
`python -m pytest tests/ --ignore=tests/INS-004 -q`
→ **28 failed, 549 passed, 1 skipped**
→ 9 failures = INS-009 implementation gap (new)
→ 19 failures = pre-existing Open WPs (INS-012 × 1, SAF-003 × 2, SAF-006 × 16)
→ **Zero regressions introduced by the INS-009 test file.**

---

## Bugs Found

None logged. The stub is incomplete by design (deferred to INS-009 implementation)
rather than a defect in an implemented feature.

---

## TODOs for Developer

- [ ] **Create `docs/workpackages/INS-009/dev-log.md`** — required before handoff.
      Must document objective, files changed, tests written, and decisions made.

- [ ] **Implement `check_for_update()` in `src/launcher/core/updater.py`:**
      - Add `_API_URL: str` module-level constant; value must start with `https://`,
        contain `api.github.com`, and reference the `releases/latest` endpoint.
      - Use only stdlib (`urllib.request`, `urllib.error`, `json`) — no `requests`.
      - Set a `User-Agent` request header (e.g. `APP_NAME/VERSION`).
      - Enforce a configurable timeout (default 5 seconds) on the `urlopen` call.
      - Wrap the entire body in a broad `except Exception` (or specific
        `URLError` + `HTTPError` + `ValueError` + `Exception`) so the function
        **never propagates an exception** under any circumstances.
      - Parse the JSON response as a `dict`; validate that `tag_name` is a
        non-empty `str` — if not, fall back to `(False, current_version)`.
      - Strip a leading `v` from the tag before comparison.
      - Compare versions using `packaging.version.Version` or a manual
        tuple-of-ints comparison to handle `1.2.3`, `1.2`, `1`, and
        `1.0.0-alpha` without raising.
      - Return `(True, latest_version_str)` when the API version is strictly
        greater than `current_version`; `(False, current_version)` otherwise.

- [ ] **Add `GITHUB_REPO` (or equivalent) to `src/launcher/config.py`** if the
      repo slug is not embedded directly in `_API_URL`. This avoids hardcoding the
      owner/repo pair inside the updater and makes it testable without changing
      source.

- [ ] **All 9 failing tests must pass** upon re-submission:
      - `test_api_url_attribute_exists`
      - `test_api_url_starts_with_https`
      - `test_api_url_targets_github_api`
      - `test_api_url_references_releases_endpoint`
      - `test_source_uses_urllib_for_http`
      - `test_newer_major_version_sets_flag_true`
      - `test_newer_minor_version_sets_flag_true`
      - `test_newer_patch_version_sets_flag_true`
      - `test_v_prefix_stripped_before_comparison`

- [ ] **Note on passing tests that pass for the wrong reason:** 8 silent-error
      tests (URLError, HTTPError, timeout, etc.) currently pass only because the
      stub never touches the network. Once the real implementation is in place,
      re-verify these tests pass because errors are genuinely caught, not because
      the code path never executes.

---

## Verdict

**FAIL — INS-009 remains `In Progress`.**

The implementation is an unfulfilled stub. No network call, no version comparison,
no `_API_URL`, and no developer documentation or tests were delivered.
The 9 failing tests above are the exact acceptance criteria that must pass
before this WP can be re-submitted for Tester review.
