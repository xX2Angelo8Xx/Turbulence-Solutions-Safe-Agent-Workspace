# FIX-104 Dev Log — Fix version-hardcoded test assertions

## Summary
Update all tests that hardcode obsolete launcher versions instead of using dynamic version sourcing from `tests/shared/version_utils.py`. Current launcher version is 3.3.11.

## ADRs Reviewed
No ADRs directly related to test version assertions. ADR-002 (Mandatory CI Test Gate Before Release Builds) is indirectly related — this WP unblocks CI by fixing stale tests.

## User Story
US-077 — Fix Stale Test Suite to Unblock CI/CD Releases

## Files Changed

### Test files updated to use `CURRENT_VERSION` from `version_utils`:
- `tests/FIX-077/test_fix077_version_322.py` — EXPECTED_VERSION changed to CURRENT_VERSION
- `tests/FIX-078/test_fix078_version_323.py` — EXPECTED_VERSION changed to CURRENT_VERSION
- `tests/FIX-078/test_fix078_edge_cases.py` — EXPECTED_VERSION changed to CURRENT_VERSION; tuple assertions made dynamic
- `tests/FIX-088/test_fix088_version_bump.py` — EXPECTED_VERSION changed to CURRENT_VERSION
- `tests/FIX-088/test_fix088_edge_cases.py` — EXPECTED_VERSION changed to CURRENT_VERSION; tuple assertions and length assertions made dynamic
- `tests/FIX-090/test_fix090_version_bump.py` — Version assertions updated to use CURRENT_VERSION
- `tests/FIX-090/test_fix090_edge_cases.py` — EXPECTED_VERSION changed to CURRENT_VERSION; future-version regex updated
- `tests/INS-029/test_ins029_version_bump.py` — EXPECTED_VERSION changed to CURRENT_VERSION
- `tests/FIX-070/test_fix070_version_bump.py` — test_current_version_is_3_2_3 updated to 3.3.11
- `tests/FIX-047/test_fix047_version.py` — Changed to standard `from tests.shared.version_utils import` pattern

### Other fixes:
- `tests/FIX-019/test_fix019_edge_cases.py` — Removed invalid minor==0 assertion (no longer valid at v3.3.11)
- `tests/FIX-036/test_fix036_version_consistency.py` — Updated architecture.md assertion to check FIX-036 reference only (2.1.0 is no longer in architecture.md)

## Strategy Notes
- Tests that test VERSION PARSING LOGIC (e.g., semver comparison tests in FIX-049) were NOT touched; those use arbitrary test data, not the launcher version.
- Tests checking stale versions (STALE_VERSION constants) were kept as-is — those correctly assert old versions are gone.
- For `test_no_future_version_in_files` in FIX-090, the regex `3\.3\.[2-9]` was blocking 3.3.11 (matched "3.3.1" prefix+1). Updated to accept 3.3.11+ as valid.
- For tests checking exact string equality against "3.2.4", "3.2.6", "3.3.1" in the canonical version files: these are the core failing assertions — replaced with CURRENT_VERSION.

## Tests Written
- No new test files required; this WP only updates existing tests.
- `tests/FIX-104/test_fix104_version_assertions.py` — validates that no test file in the affected set hardcodes old version strings.

## Test Results
- All 39 previously-failing version tests now pass.
- Ran `scripts/run_tests.py --wp FIX-104 --type Unit --env "Windows 11 + Python 3.13"`.
