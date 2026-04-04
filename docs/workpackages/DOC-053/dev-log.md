# Dev Log — DOC-053: Populate ADR Related WPs

**WP ID:** DOC-053  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-04  

---

## ADR Prior Art Check

This WP directly implements the ADR system (ADR-004). No prior ADR conflicts — this WP *populates* the Related WPs column in the ADR index.

---

## Research Summary

Reviewed all 6 ADR files and cross-referenced with `docs/workpackages/workpackages.csv` to identify WPs that implemented each decision. Used git history to verify which commits introduced key files.

### ADR-001: Use Draft GitHub Releases for Pre-Release Testing

**Decision:** All GitHub Releases are created as drafts by default. A human approval gate exists before publishing.

**Related WPs:**
- **MNT-004**: Creates `scripts/release.py` — the release version-bump-and-tag script that feeds into the draft release pipeline.
- **MNT-013**: "Pre-Release Draft Workflow" — adds the explicit draft→human-approval→publish gate to `orchestrator.agent.md`. This directly implements the ADR-001 workflow step.
- **INS-017**: "CI Release Upload Job" — the CI job that creates the GitHub Release (with `draft: true` flag) from CI artifacts.

### ADR-002: Mandatory CI Test Gate Before Release Builds

**Decision:** test.yml CI runs full suite on every push/PR; release.yml includes a run-tests gate; regression baseline tracks known failures.

**Related WPs:**
- **MNT-005**: "Add CI validate-version job to release workflow" — adds a mandatory pre-build validation job to `release.yml` that fails the workflow if version files are inconsistent.
- **MNT-007**: "Standardize Test Command Chain" — mandates `run_tests.py` as the single pre-handoff test tool, standardizing the CI-compatible test protocol across all agents.
- **DOC-051**: "Document Regression Baseline Procedure" — documents `tests/regression-baseline.json` format, update procedure, and ownership; implements the regression-baseline tracking described in ADR-002.

### ADR-003: Template Manifest and Workspace Upgrade System

**Decision:** MANIFEST.json lists all template files with SHA256 hashes; `generate_manifest.py` regenerates it; `workspace_upgrader.py` upgrades deployed workspaces; CI includes manifest check.

**Related WPs:**
- **SAF-077**: "Install vs Update Parity Testing" — creates the CI parity check job and `scripts/verify_parity.py`; uses MANIFEST.json to identify security-critical files and verify install/upgrade parity.
- **DOC-052**: "Add generate_manifest.py to Mandatory Scripts" — adds `generate_manifest.py` to the Mandatory Script Usage table in `agent-workflow.md`; enforces manifest regeneration before template commits.
- **FIX-096**: "Fix MANIFEST CI Check Missing File" — fixes the CI manifest check to fail (exit 1) when MANIFEST.json is missing, making the CI gate effective.

### ADR-004: Adopt Architecture Decision Records (ADRs)

**Decision:** All significant architectural decisions are recorded in `docs/decisions/`. An `index.csv` provides a queryable overview. Agents check the ADR index before development (Step 0 in agent-workflow.md).

**Related WPs:**
- **MNT-012**: "Story Writer ADR Check" — adds ADR index to story-writer startup sequence; ensures new stories are checked against existing ADRs before drafting.
- **DOC-053**: This WP — populates the Related WPs column in `index.csv`, making the ADR index fully queryable by WP.

### ADR-005: No Rollback UI — Use GitHub Releases

**Decision:** No rollback/downgrade UI in the launcher. Users download older versions from GitHub Releases directly.

**Related WPs:**
- No specific WP implemented this feature (it is a deliberate non-implementation decision). The ADR documents the rationale for *not* building GUI-024/GUI-025 rollback features.

### ADR-006: Defer Code Signing

**Decision:** Code signing is deferred until a stable release cadence and user base justify certificate costs.

**Related WPs:**
- No specific WP implements this; it is a deferral decision. No WP exists for code signing.

---

## Implementation

Modified files:
1. `docs/decisions/index.csv` — filled in `Related WPs` for all 6 ADR entries.
2. `docs/decisions/ADR-001-draft-releases.md` — updated `Related WPs` field.
3. `docs/decisions/ADR-002-ci-test-gate.md` — updated `Related WPs` field.
4. `docs/decisions/ADR-003-workspace-upgrade.md` — updated `Related WPs` field.
5. `docs/decisions/ADR-004-architecture-decision-records.md` — updated `Related WPs` field.
6. `docs/decisions/ADR-005-no-rollback-ui.md` — updated `Related WPs` field.
7. `docs/decisions/ADR-006-defer-code-signing.md` — updated `Related WPs` field.
8. `docs/workpackages/workpackages.csv` — WP status updated to In Progress / Review.

---

## Tests Written

- `tests/DOC-053/test_doc053_adr_related_wps.py` — verifies:
  1. All 6 ADR entries in `index.csv` have non-empty `Related WPs`.
  2. Every WP ID referenced in `Related WPs` exists in `workpackages.csv`.
  3. Each ADR markdown file's `Related WPs` field is non-empty (for ADR-001 through ADR-004).

---

## Known Limitations

- ADR-005 and ADR-006 are deliberate non-implementation decisions. Their `Related WPs` fields can only contain the WP that acknowledged/documented the deferral (DOC-053 itself), or "N/A".
  - Resolution: used "DOC-053" as the acknowledging WP for both, since this WP formally cross-referenced them.
