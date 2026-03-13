# Dev Log — INS-010

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
When the user initiates an update, download the appropriate platform installer artifact
from the GitHub Releases assets to a temp directory. Verify integrity before proceeding.
(US-016 AC 2–3: correct platform installer downloaded to temp dir; SHA256 integrity verified.)

## Implementation Summary

Created `src/launcher/core/downloader.py` — a self-contained, stdlib-only module that:

1. Constructs the GitHub Releases API URL for a specific version tag
   using `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` from `config.py`.
2. Detects the current platform via `sys.platform` and normalises CPU architecture
   from `platform.machine()` (x86_64 / arm64).
3. Matches the correct release asset by file extension (.exe / .dmg / .AppImage)
   with an architecture-preference pass before falling back to extension-only.
4. Validates the download URL against an explicit allow-list of GitHub-owned hostnames
   and enforces HTTPS — preventing SSRF attacks.
5. Sanitises the asset filename (removes path separators and non-safe characters)
   before writing to disk.
6. Downloads the asset to a `tempfile.mkdtemp()` directory using a 30-second timeout
   and `Accept: application/octet-stream` header.
7. Attempts to fetch a companion `.sha256` file from the same release assets;
   if found, compares the computed SHA256 digest and raises `RuntimeError` on mismatch.
   If no companion file is present, logs a warning and proceeds.
8. Returns the `Path` to the downloaded installer on success; raises a descriptive
   `RuntimeError` or `ValueError` on every failure path.

### Key Design Decisions
- **stdlib only** (`urllib.request`, `hashlib`, `tempfile`, `platform`, `sys`, `json`, `re`)
  — consistent with `updater.py`; no third-party HTTP dependencies.
- **Fail-closed**: every error path raises rather than returning silently.
- **URL validation** uses `urllib.parse.urlparse` to inspect scheme and hostname —
  not string prefix matching — to be robust against obfuscation.
- **Filename sanitisation** uses a compiled regex keeping only `\w`, `.`, `-`;
  `Path(name).name` strips directory components first.
- **Architecture fuzzy matching** uses a keyword list so Windows `x64` / `win64`
  installer names also match the `x86_64` architecture.
- Version tag normalisation: a leading `v` is added when absent so both `1.2.3`
  and `v1.2.3` reach the correct API endpoint.

## Files Changed
- `src/launcher/core/downloader.py` — new file (INS-010 implementation)

## Tests Written
- `tests/INS-010/__init__.py` — package marker
- `tests/INS-010/test_ins010_downloader.py`:
  - `TestPlatformDetection` — verify correct extension for win32, darwin, linux,
    and that unsupported platforms raise RuntimeError
  - `TestArchitectureDetection` — amd64/x86_64, arm64/aarch64 normalisation,
    unknown passthrough
  - `TestAssetSelection` — exact arch match, fallback to extension-only,
    architecture preference order, missing asset raises RuntimeError
  - `TestURLValidation` — HTTP rejected, non-GitHub host rejected, all allowed
    hosts accepted, SSRF-by-path rejected
  - `TestFilenameSanitization` — path traversal stripped, special chars removed,
    empty result raises ValueError, normal names preserved
  - `TestSHA256Computation` — known hash verified, empty file hash, multi-chunk read
  - `TestFetchSHA256Companion` — companion found and downloaded, not found returns None,
    network error returns None (non-fatal)
  - `TestDownloadUpdate` — happy path (Windows), macOS happy path, Linux happy path,
    HTTP error on metadata fetch, network error on metadata, bad JSON response,
    no assets in release, missing asset for platform, hash mismatch raises and
    cleans up temp file, no companion hash logs warning and proceeds,
    URL validation applied to download URL, timeout constant equals 30

## Known Limitations
- SHA256 companion file format assumed to be `<hash>  <filename>` or `<hash>` on
  the first line — no other checksum formats (MD5, etc.) are supported.
- The download is single-threaded with no progress reporting; a future WP may
  add a progress callback for the UI.
- ARM detection on Windows (arm64 Windows) is not explicitly tested since no
  Windows ARM release asset naming convention has been established yet.
