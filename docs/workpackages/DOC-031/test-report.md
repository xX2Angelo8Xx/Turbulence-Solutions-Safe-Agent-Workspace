# Test Report — DOC-031

**Tester:** Tester Agent (GitHub Copilot)
**Date:** 2026-03-30
**Iteration:** 1

## Summary

AGENT-RULES.md has been completely rewritten and accurately reflects actual gate
behavior. All v3.2.5 feedback issues are resolved. The document is 148 lines
(down from ~200 — a 26% reduction). All 30 automated tests pass, 110 regression
tests across related DOC workpackages show no regressions.

## Content Accuracy Review

| Claim | Verified | Notes |
|-------|----------|-------|
| §1 — `.venv` creation via `python -m venv` | ✅ | Line present in Terminal Rules |
| §1 — System Python fallback (`python script.py`) | ✅ | Documented as acceptable fallback |
| §2 — `.github/` partial read-only model | ✅ | Table row correctly describes all 4 allowed subdirs |
| §2 — `read_file` allowed for instructions/skills/agents/prompts | ✅ | Explicit in table and §3 matrix |
| §2 — `list_dir` denied on `.github/` | ✅ | Explicit in table and §3 matrix |
| §2 — All writes to `.github/` denied | ✅ | "All writes are denied" |
| §2 — `.github/hooks/` fully denied (reads+writes) | ✅ | "fully denied (no reads or writes)" |
| §2 — `.vscode/` fully denied | ✅ | "Fully denied. No reads or writes." |
| §2 — `NoAgentZone/` fully denied | ✅ | "Fully denied. No reads or writes." |
| §3 — `read_file` notes mention `.github/` read access | ✅ | Lists all 4 allowed paths; denies hooks/ |
| §3 — `list_dir` notes deny `.github/` | ✅ | "denied in `.github/`…" |
| §3 — `memory` tool listed as Allowed | ✅ | Memory row present |
| §3 — No "blocked by design" stale reference | ✅ | Absent from document |
| §4 — `cmd /c` in blocked commands | ✅ | Both `cmd /c` and `cmd.exe /c` listed |
| §5 — All 5 blocked git operations present | ✅ | push --force, reset --hard, filter-branch, gc --force, clean -f |
| §5 — Standard allowed operations listed | ✅ | Full table present |
| §6 — Block budget system described | ✅ | "Block N of M" language present |
| §7 — Known Workarounds reasonable, no stale entries | ✅ | 8 relevant entries |
| §8 — Agent Personas section removed | ✅ | Does not appear |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2334: DOC-031 developer tests (10) | Unit | PASS | All 10 developer assertions |
| TST-2335: DOC-031 tester edge cases (20) | Unit | PASS | All 20 tester assertions |
| TST-2336: DOC-031 regression suite (110) | Regression | PASS | DOC-031 + DOC-001/003/004/005 |

## Bugs Found

None.

## TODOs for Developer

None.

## Verdict

PASS — mark WP as Done.
