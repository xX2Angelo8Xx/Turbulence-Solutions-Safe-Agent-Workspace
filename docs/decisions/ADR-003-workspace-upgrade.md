# ADR-003: Template Manifest and Workspace Upgrade System

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:** SAF-077, DOC-052, FIX-096  
**Supersedes:** None  
**Superseded by:** None

## Context

When the launcher updates, existing user workspaces retain their original security files (security_gate.py, zone_classifier.py, settings.json, hooks). A workspace created on v3.1.0 keeps v3.1.0 security files even after updating the launcher to v3.3.9. This means security patches in newer versions never reach deployed workspaces.

## Decision

1. A `MANIFEST.json` in `templates/agent-workbench/` lists every template file with SHA256 hashes.
2. `scripts/generate_manifest.py` regenerates the manifest (must be run before releases).
3. `src/launcher/core/workspace_upgrader.py` compares workspace files against the manifest and upgrades only security-critical files.
4. The launcher GUI offers a "Check Workspace Health" function.
5. User project files (`Project/`, `AgentDocs/`) are NEVER touched by the upgrader.

## Consequences

- **Positive:** Security patches propagate to all deployed workspaces
- **Positive:** Fresh install and upgraded workspace are verifiably identical for security files
- **Negative:** Upgrade logic adds complexity; must handle partial upgrades and rollback
- **Negative:** Manifest must be regenerated before every release (enforced by CI)

## Notes

CI includes a manifest-check job that fails if template files changed but MANIFEST.json wasn't regenerated.
