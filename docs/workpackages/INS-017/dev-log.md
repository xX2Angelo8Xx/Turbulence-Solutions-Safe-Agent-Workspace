# INS-017 Dev Log — CI Release Upload Job

## Status
In Progress → Review

## Assignment
- **WP ID:** INS-017
- **Agent:** Developer Agent
- **Branch:** `ins/INS-017-ci-release-upload`
- **Date:** 2026-03-14

## Objective
Add the `release` job to `.github/workflows/release.yml` that:
1. Depends on all 4 platform build jobs via `needs`
2. Has `permissions: contents: write` to create GitHub Releases
3. Downloads all artifacts with `actions/download-artifact@v4` (no `name` = all artifacts)
4. Creates a GitHub Release via `softprops/action-gh-release@v2` with all artifacts attached
5. Uses `generate_release_notes: true` to auto-generate notes from commits

## Files Changed
- `.github/workflows/release.yml` — release job expanded from checkout stub to full release steps
- `tests/INS-017/test_ins017_release_job.py` — test suite verifying the release job
- `docs/workpackages/INS-017/dev-log.md` — this file
- `docs/workpackages/workpackages.csv` — INS-017 status updated

## Implementation Summary

The `release` job stub previously only had `actions/checkout@v4`. The following was added:

1. **`permissions: contents: write`** — Required by `softprops/action-gh-release` to create and publish a GitHub Release. Without `write` permission the action cannot create releases.

2. **`actions/download-artifact@v4` (no `name` key)** — Downloads ALL artifacts from upstream jobs into `release-assets/`. Each artifact is placed in its own subdirectory (`release-assets/windows-installer/`, etc.).

3. **`softprops/action-gh-release@v2`** — Industry-standard action for creating GitHub Releases. The `files: release-assets/**/*` glob matches all files inside all artifact subdirectories. `generate_release_notes: true` auto-populates the release description with commits since the last tag.

## Design Decisions
- Used `@v2` for `softprops/action-gh-release` (latest major) for security/stability.
- Used `release-assets/**/*` glob to cover all artifact subdirectories uniformly.
- No `tag_name` override — action reads the triggering tag automatically (already enforced by `on.push.tags: v*.*.*`).
- No `GITHUB_TOKEN` explicit reference needed — `softprops/action-gh-release` uses the default `GITHUB_TOKEN` from the workflow context when `permissions: contents: write` is set.

## Tests Written
- `tests/INS-017/__init__.py`
- `tests/INS-017/test_ins017_release_job.py`

Test categories covered:
- release job exists in workflow
- needs exactly the 4 build jobs
- runs-on ubuntu-latest
- permissions.contents equals write
- download-artifact step present with correct action version
- download-artifact path is release-assets
- download-artifact has no `name` key (downloads all)
- softprops/action-gh-release step present
- softprops action uses @v2
- files glob is release-assets/**/*
- generate_release_notes is true
- release job has exactly 3 steps (checkout + download + release)

## Test Results
All tests pass — see `docs/test-results/test-results.csv`.
