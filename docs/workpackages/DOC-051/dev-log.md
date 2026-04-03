# Dev Log — DOC-051

**Developer:** Developer Agent
**Date started:** 2026-04-03
**Iteration:** 1

## Objective

Create documentation for `tests/regression-baseline.json`: describe its format, when to update it (after bug fixes, after intentional behaviour changes), and who is responsible for updates (Developer, Tester, Orchestrator). Add a "Regression Baseline" section to `docs/work-rules/testing-protocol.md` and ensure `agent-workflow.md` references the file. Verify the three active agents (Developer, Tester, Orchestrator) are all aware of its role. Fixes maintenance finding M-06.

## ADR Check

`docs/decisions/index.csv` lists one ADR: ADR-001 (Use Draft GitHub Releases for Pre-Release Testing). No ADRs relate to regression baselines or testing infrastructure — no prior decisions to acknowledge or supersede.

## Implementation Summary

1. Added a **"## Regression Baseline"** section to `docs/work-rules/testing-protocol.md` documenting:
   - Purpose: tracks known-failing tests so CI does not flag them as new regressions.
   - Exact JSON schema: top-level metadata fields (`_comment`, `_count`, `_updated`) plus the `known_failures` map.
   - When to update: Developer removes an entry after fixing a bug; Orchestrator sweeps staleness at release; Developer or Tester adds an entry for a newly discovered known failure.
   - Who updates per role (Developer / Tester / Orchestrator).
   - How to update: direct JSON editing (no script exists; section notes this clearly).

2. Added a **"Update regression baseline"** row to the **Mandatory Script Usage** table in `docs/work-rules/agent-workflow.md` (noting direct JSON editing with the mandatory `_count` and `_updated` fields — no dedicated script exists, so the table entry explains the procedure rather than pointing to a script).

3. Added a regression-baseline awareness line to `docs/work-rules/agent-workflow.md` Pre-Handoff Checklist for Developers: "If this WP is a bug fix, remove the corresponding entry from `tests/regression-baseline.json`."

4. Added a reference note to `.github/agents/developer.agent.md` — the developer pre-handoff checklist now includes a regression baseline step for bug-fix WPs (the Tester and Orchestrator agent files already referenced it).

## Files Changed

- `docs/work-rules/testing-protocol.md` — Added "## Regression Baseline" section
- `docs/work-rules/agent-workflow.md` — Added regression baseline note to Developer Pre-Handoff Checklist and to Mandatory Script Usage table
- `.github/agents/developer.agent.md` — Added regression baseline note to Pre-Handoff Checklist

## Tests Written

- `tests/DOC-051/test_doc051_regression_baseline_docs.py` — validates that testing-protocol.md contains the required Regression Baseline section headings and keywords; validates agent-workflow.md references the baseline file; validates developer.agent.md references the baseline file.

## Known Limitations

- No dedicated update script exists for `tests/regression-baseline.json`. The documentation notes that direct JSON editing is the correct procedure and explains exactly what fields to update.
