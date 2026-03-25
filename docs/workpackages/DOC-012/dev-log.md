# Dev Log — DOC-012

**Developer:** Developer Agent  
**Date started:** 2026-03-25  
**Iteration:** 1

## Objective

Research whether MCP (Model Context Protocol) tools should be allowed within the
Turbulence Solutions project scope. Produce a research report covering:
1. Inventory of common MCP servers
2. Security implications of `mcp_*` tool calls
3. Zone-checking feasibility
4. Extensibility framework for selective allowlisting
5. Recommendation

---

## Implementation Summary

This is a **research-only workpackage**. No changes were made to `src/`, `templates/`,
or any existing source files. The deliverables are:

- `docs/workpackages/DOC-012/research-report.md` — full MCP security research report
- `tests/DOC-012/test_doc012_report.py` — structural validation tests for the report

---

## Research Summary

### Key Findings

1. **MCP server inventory**: 12+ categories of MCP servers are in common use, ranging
   from filesystem access to cloud provider APIs. Risk levels vary from "lower risk"
   (read-only search) to "critical" (filesystem write, Docker volume mounts).

2. **Security implications**: Three primary attack vectors identified:
   - Arbitrary filesystem read/write via `mcp_filesystem_*`
   - SSRF and data exfiltration via `mcp_fetch_*` and browser MCPs
   - Irreversible remote side effects via `mcp_github_push_*`, `mcp_slack_*`

3. **Zone-checking feasibility**:
   - Feasible for `mcp_filesystem_*` and `mcp_sqlite_*` (local file path arguments)
   - Not feasible for search, messaging, cloud, or database MCPs (no local path)
   - Secondary argument bypass is a residual risk even for zone-checkable tools

4. **Framework design**: Three-tier approach with `turbulence.mcp_policy` configuration
   in workspace `settings.json`. Explicit allowlist only (no wildcards). Zone-check
   mandatory for all path-bearing tools.

5. **Recommendation**: Keep blocking all `mcp_*` by default. Ready the extensibility
   framework for Phase 2 implementation (separate future SAF workpackage). First safe
   candidates: `mcp_filesystem_read_file`, `mcp_filesystem_list_directory`.

---

## Files Changed

| File | Change Type |
|------|-------------|
| `docs/workpackages/DOC-012/research-report.md` | Created (new research report) |
| `docs/workpackages/DOC-012/dev-log.md` | Created (this file) |
| `docs/workpackages/workpackages.csv` | Updated status to `In Progress` → `Review` |
| `tests/DOC-012/test_doc012_report.py` | Created (report existence and section tests) |
| `tests/DOC-012/__init__.py` | Created (package marker) |

---

## Tests Written

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/DOC-012/test_doc012_report.py` | 7 | Verify report exists, has correct sections, covers all 5 required areas |

---

## Known Limitations

- The research is based on publicly available MCP server documentation, not live traffic
  analysis. Specific argument schemas for less common MCP servers may differ slightly
  from documented behaviour.
- The framework pseudocode in Section 4.3 of the report is illustrative only and is not
  an implementation commitment — the actual implementation belongs in a future SAF WP.

---

## Decisions Made

- **No source code changes** — this WP is research-only per its description
- **Permanent blocks list** defined for Docker, database-write, cloud, and messaging MCPs
  to give future implementers clear guidance
- **Phase 2 path** outlined to avoid leaving the framework design open-ended
