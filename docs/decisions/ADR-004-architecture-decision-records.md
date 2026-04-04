# ADR-004: Adopt Architecture Decision Records (ADRs)

**Status:** Active  
**Date:** 2026-04-03  
**Related WPs:** MNT-012, DOC-053  
**Supersedes:** None  
**Superseded by:** None

## Context

Design decisions were previously scattered across 150+ `dev-log.md` files. There was no centralized record of WHY something was decided. Agents had no way to discover prior conflicting decisions without reading all dev-logs (impossible within context limits). When WP-A decided "hide NoAgentZone from users" and WP-B later decided "show NoAgentZone", there was no mechanism to detect the contradiction.

## Decision

1. All significant architectural decisions are recorded in `docs/decisions/` as `ADR-NNN-short-title.md`.
2. An `index.csv` provides a queryable overview of all ADRs.
3. When a new decision supersedes a prior one, the old ADR is marked "Superseded by ADR-NNN".
4. Agents must check the ADR index before starting development (Prior Art Check in agent-workflow.md).
5. `validate_workspace.py` warns if a Done WP references a superseded ADR.

## Consequences

- **Positive:** Conflicting decisions are detected before implementation
- **Positive:** Agents can quickly scan the ADR index instead of reading all dev-logs
- **Positive:** Decision rationale is preserved for future reference
- **Negative:** Small overhead per decision (creating the ADR file)
- **Negative:** Agents must read one additional file during startup

## Notes

The ADR template is at `docs/decisions/ADR-TEMPLATE.md`. Context tiers for agents: Tier 1 (always load: copilot-instructions, relevant WP), Tier 2 (load if relevant: ADRs, related WPs), Tier 3 (on-demand: full architecture, all rules).
