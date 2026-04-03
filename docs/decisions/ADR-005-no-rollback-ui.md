# ADR-005: No Rollback UI — Use GitHub Releases

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:**  
**Supersedes:** None  
**Superseded by:** None

## Context

The overhaul plan (Phase 5) considered adding an "Install Previous Version" option to the launcher GUI to let users downgrade if a release was broken. This required building a version browser, download logic for arbitrary past versions, and installer rollback.

## Decision

We will **not** implement a rollback/downgrade UI in the launcher. All released versions are available on the GitHub Releases page. Users who need a previous version can download it directly from GitHub.

This is justified because:
- Draft releases (ADR-001) and CI test gates (ADR-002) reduce the probability of broken releases reaching users.
- Each new version should be an improvement — rollback is a recovery path, not a workflow.
- The engineering effort is better spent on preventing bad releases than recovering from them.

## Consequences

- **Positive:** Avoids UI complexity and maintenance burden of a version browser.
- **Positive:** GitHub Releases already provides this capability with changelogs and checksums.
- **Negative:** Users must manually download from GitHub if they need an older version (no in-app path).

## Notes

Revisit if user feedback indicates frequent need for rollback. At that point, the root cause (release quality) should be addressed first.
