# ADR-001: Use Draft GitHub Releases for Pre-Release Testing

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:** N/A (structural overhaul)  
**Supersedes:** None  
**Superseded by:** None

## Context

Previously, running `scripts/release.py` pushed a tag that immediately triggered a public GitHub Release. The auto-updater (`src/launcher/core/updater.py`) queries `/releases/latest` and would see the new version immediately. There was no way to test a built artifact before it reached end users.

For a security-critical application (Safe Agent Environment), releasing untested artifacts to production is unacceptable.

## Decision

All GitHub Releases are now created as **drafts** by default. The workflow is:

1. Developer runs `scripts/release.py <version>` (unchanged)
2. CI/CD builds artifacts and creates a **draft** release (not visible via `/releases/latest`)
3. Developer downloads draft artifacts and performs internal testing
4. Developer manually publishes the draft on GitHub (promotes to public)
5. Auto-updater now sees the new version

## Consequences

- **Positive:** Broken releases never reach users; internal testing is possible before publication
- **Positive:** No changes needed to `updater.py` — GitHub API already excludes drafts from `/releases/latest`
- **Negative:** One additional manual step (publishing the draft) is required per release
- **Negative:** If developer forgets to publish, users won't receive the update

## Notes

The auto-updater queries `GET /repos/{owner}/{repo}/releases/latest` which by GitHub API design only returns non-draft, non-prerelease releases. This behavior is leveraged rather than implementing custom channel logic.
