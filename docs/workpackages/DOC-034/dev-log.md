# DOC-034 Dev Log — Update Orchestrator Release Instructions

**WP ID:** DOC-034  
**Name:** Update orchestrator release instructions  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** DOC-034/orchestrator-release-docs  
**User Story:** US-068 — Automate Release Version Management  

---

## Objective

Update the **CI/CD Pipeline Trigger** section in both orchestrator agent files to replace manual git tag instructions with `scripts/release.py` as the primary release method.

**Files targeted:**
- `.github/agents/orchestrator.agent.md`
- `.github/agents/CLOUD-orchestrator.agent.md`

---

## Implementation Summary

Replaced the CI/CD Pipeline Trigger section in both files with:

1. **Primary Method — Release Script**: Documents `scripts/release.py <version>` as the main way to trigger a release, including what the script does (bumps 5 version files, validates, commits, tags, pushes).
2. **`--dry-run` flag**: Documented for preview before executing.
3. **Validate-version CI job**: Mentioned as the safety net that runs before all build jobs.
4. **Fallback — Manual Re-tagging**: Preserved as a fallback procedure for post-tag fixes.

Both files are identical in this section.

---

## Files Changed

- `.github/agents/orchestrator.agent.md` — CI/CD Pipeline Trigger section replaced
- `.github/agents/CLOUD-orchestrator.agent.md` — CI/CD Pipeline Trigger section replaced
- `docs/workpackages/workpackages.csv` — DOC-034 status set to In Progress → Review
- `docs/workpackages/DOC-034/dev-log.md` — this file

---

## Tests Written

| File | Description |
|------|-------------|
| `tests/DOC-034/test_doc034_orchestrator_release_docs.py` | 7 tests verifying both agent files contain required release script references, `--dry-run`, `validate-version`, Fallback section, absence of old manual tagging as primary, section presence, and identical content |

---

## Test Results

All 7 tests passed. See `docs/test-results/test-results.csv` for log entry.

---

## Known Limitations

None. This is a documentation-only change with no code behaviour impact.
