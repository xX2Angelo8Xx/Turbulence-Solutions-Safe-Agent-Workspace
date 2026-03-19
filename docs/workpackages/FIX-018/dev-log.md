# Dev Log — FIX-018

**Developer:** Orchestrator + Developer Agent
**Date started:** 2026-03-16
**Iteration:** 1

## Objective
Add GitHub authentication to all API calls in updater.py and downloader.py so that auto-update detection and download work for private repositories.

## Root Cause
The repository is private. Both updater.py and downloader.py made unauthenticated requests to the GitHub Releases API. For private repos, unauthenticated calls return HTTP 404. The check_for_update() function silently catches this and reports "no update available."

## Implementation Summary
- Created `src/launcher/core/github_auth.py` with `get_github_token()` helper
  - Checks GITHUB_TOKEN env var first, then GH_TOKEN, then `gh auth token` CLI
  - Returns None if no auth is available (graceful fallback)
  - Uses subprocess.run with list args, 3-second timeout
- Updated `src/launcher/core/updater.py` to add Authorization header when token available
- Updated `src/launcher/core/downloader.py` to add Authorization header to all 3 request types (metadata, SHA256 companion, asset download)
- Fixed `tests/INS-001/test_ins001_structure.py::test_updater_stub_returns_no_update` which broke because it called the real check_for_update without mocking the network — now mocks urlopen to test the silent-failure path properly

## Files Changed
- `src/launcher/core/github_auth.py` — new file: get_github_token()
- `src/launcher/core/updater.py` — import github_auth, add Authorization header
- `src/launcher/core/downloader.py` — import github_auth, add Authorization header to all requests
- `tests/INS-001/test_ins001_structure.py` — fixed flaky test that relied on unauthenticated API failure

## Tests Written
- `tests/FIX-018/test_fix018_github_auth.py` — 19 tests: env var priority, whitespace stripping, CLI subprocess, fallback to None
- `tests/FIX-018/test_fix018_updater_auth.py` — 7 tests: auth header added/omitted, 404 regression, single call verification
- `tests/FIX-018/test_fix018_downloader_auth.py` — 8 tests: auth header on metadata/download/sha256 requests

## Known Limitations
- If the user doesn't have GitHub CLI installed and no GITHUB_TOKEN env var set, auto-update will still fail silently for private repos (same as before — this is expected behavior)
