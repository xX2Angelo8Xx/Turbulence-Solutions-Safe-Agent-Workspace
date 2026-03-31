# Dev Log — DOC-037: Create 3 Structured Prompts

**WP ID:** DOC-037  
**Type:** DOC  
**Assigned To:** Developer Agent  
**Status:** In Progress → Review  
**Date:** 2026-03-31  

---

## Objective

Create 3 structured prompt files in `templates/agent-workbench/.github/prompts/`:
1. `critical-review.prompt.md` — phased critique with severity ratings
2. `prototype.prompt.md` — fast skeleton with expansion points
3. `root-cause-analysis.prompt.md` — causal chain tracing

Each prompt follows a 3-phase workflow with a defined output format block.

---

## Implementation Summary

### Files Created

| File | Path |
|------|------|
| `critical-review.prompt.md` | `templates/agent-workbench/.github/prompts/` |
| `prototype.prompt.md` | `templates/agent-workbench/.github/prompts/` |
| `root-cause-analysis.prompt.md` | `templates/agent-workbench/.github/prompts/` |

### Details

**critical-review.prompt.md**  
- Phase 1: Parse the subject (identify type, summarize, flag if incomplete)  
- Phase 2: Find flaws (logic, assumptions, edge cases, scalability, security, dependencies)  
- Phase 3: Rank top 3 risks with mitigations; overall confidence rating  
- Output: findings table + top 3 risks + confidence statement  

**prototype.prompt.md**  
- Phase 1: Extract minimal requirements; separate must-haves from nice-to-haves  
- Phase 2: Define skeleton (entry points, interfaces, data flow, file structure)  
- Phase 3: Implement runnable skeleton with TODO markers; verify it runs  
- Output: entry point, file tree, expansion points list, known shortcuts  

**root-cause-analysis.prompt.md**  
- Phase 1: Describe symptom precisely; distinguish symptom from error  
- Phase 2: Trace chain backwards with evidence; eliminate surface causes  
- Phase 3: Confirm root cause; draw causal chain; propose minimal fix  
- Output: causal chain table + root cause statement + confidence + recommended fix  

### Existing File Preserved

`debug-workspace.prompt.md` was NOT modified.

---

## Tests

No automated tests required for documentation-only WP. Verification performed manually:
- All 3 files exist with valid YAML frontmatter (`description` key present)
- Each file has exactly 3 phases + output format section
- `debug-workspace.prompt.md` unmodified

---

## Decisions

- Used fenced code blocks (` ``` `) inside the output format sections to clearly delineate the template structure, consistent with `debug-workspace.prompt.md` style.
- Working directly on `main` branch per explicit user instruction (no feature branch).
