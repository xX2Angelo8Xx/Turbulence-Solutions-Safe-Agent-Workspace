# Dev Log — DOC-055: Fix index.md Scripts Link

**WP ID:** DOC-055  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** DOC-055/fix-index-scripts-link  
**Date:** 2026-04-04  

---

## ADR Review

No ADRs relate to documentation link formatting. No prior architectural decisions are impacted by this fix.

---

## Problem

In `docs/work-rules/index.md`, the "Use a helper script" row contains a Markdown link where:
- **Display text:** `../scripts/README.md` — incorrect (implies one directory level up from the reader's perspective)
- **Href target:** `../../scripts/README.md` — correct (navigates up two levels from `docs/work-rules/` to repo root, then into `scripts/`)

The display text must be corrected to `scripts/README.md` (workspace-relative path, consistent with all other entries in the Key Project Files table).

---

## Implementation

**File changed:** `docs/work-rules/index.md`

Changed:
```markdown
| Use a helper script | [../scripts/README.md](../../scripts/README.md) |
```

To:
```markdown
| Use a helper script | [scripts/README.md](../../scripts/README.md) |
```

Only the display text was changed. The href target `../../scripts/README.md` was already correct and was not modified.

---

## Tests

- **Test file:** `tests/DOC-055/test_doc055_index_link.py`
- Tests verify:
  1. The link display text is `scripts/README.md` (not `../scripts/README.md`)
  2. The href target is `../../scripts/README.md`
  3. The target file `scripts/README.md` exists at the resolved path

---

## Known Limitations

None. This is a pure documentation text fix.
