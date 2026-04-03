# ADR-006: Defer Code Signing

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:**  
**Supersedes:** None  
**Superseded by:** None

## Context

The overhaul plan (Phase 5) identified that release artifacts are not code-signed (Windows) or notarized (macOS), creating a supply-chain attack vector. Code signing requires purchasing certificates (Windows Authenticode, Apple Developer ID) and integrating signing steps into the CI/CD pipeline.

## Decision

We will **defer code signing** until the project reaches a more stable state. The current priority is CI/CD automation, regression prevention, and workspace upgrade infrastructure. Code signing will be implemented when:

1. The CI/CD pipeline (ADR-002) and staging workflow (ADR-001) are battle-tested.
2. The project has a stable release cadence.
3. Certificate procurement and renewal costs are justified by user base size.

## Consequences

- **Positive:** No upfront certificate cost or CI pipeline complexity.
- **Positive:** Development effort focused on higher-impact safety improvements.
- **Negative:** Windows SmartScreen and macOS Gatekeeper will warn users on first launch.
- **Negative:** No cryptographic proof of artifact authenticity until signing is added.

## Notes

When implementing, consider:
- Windows: Authenticode certificate (EV preferred for SmartScreen reputation).
- macOS: Apple Developer ID + notarization via `xcrun notarytool`.
- Linux: GPG-signed checksums file alongside AppImage.
