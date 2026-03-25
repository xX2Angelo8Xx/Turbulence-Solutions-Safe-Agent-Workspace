# Test Report — SAF-048

**Tester:** GitHub Copilot (Tester Agent)
**Date:** 2026-03-25
**Iteration:** 3 (re-test after Developer Iteration 3 BUG-125 fix)

---

## Summary

**PASS. SAF-048 is complete and correct.**

Developer Iteration 3 resolved BUG-125 by choosing Option A: the SAF-038 test
`test_memory_null_byte_in_project_path_allow` was renamed to
`test_memory_null_byte_in_project_path_deny` and its assertion updated to
expect `"deny"`. This is an intentional security policy improvement — null bytes
in any path are now denied early, eliminating the old accidental
strip-then-classify weakness.

All 185 SAF-048 + SAF-038 tests pass. 20 additional tester edge-case tests were
added in this iteration and all pass (TST-2193).

Full suite: **72 pre-existing failures** (all unrelated to SAF-048), **6,534 passing**.
72 failures confirmed present on `main`; none caused by SAF-048.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| SAF-048 dev tests (33) | Unit | PASS (TST-2186) | Virtual reads, writes, fail-closed, cross-platform, BUG-113 regression |
| SAF-048 iter 1 tester edge-cases (24) | Security | PASS (TST-2185) | Traversal, null-byte, case — all BUG-121..124 fixes verified |
| SAF-048 iter 2 full suite (57 tests) | Unit + Security | PASS (TST-2188) | 57 passed, 0 failed |
| SAF-038 regression check | Regression | **PASS** | `test_memory_null_byte_in_project_path_deny` passes; BUG-125 resolved |
| SAF-048 iter 3 tester edge-cases (20) | Security | **PASS (TST-2193)** | New: false prefix, dir write, non-string command, BUG-125 policy, long paths, command precision |
| SAF-048 + SAF-038 combined (185 tests) | All | **PASS 185/185 (TST-2193)** | 185 passed, 0 failed |
| Full test suite (6,534 passing) | Regression | 72 pre-existing failures | All 72 confirmed present on `main`; none caused by SAF-048 |

---

## Security Review

### `validate_memory()` implementation

**Input handling:**
- Path extracted from `tool_input.filePath` first, then `data.filePath`, then `data.path`. Correctly typed. Fails closed on missing/empty path.

**Character validation (BUG-123):**
- Null bytes rejected via explicit `"\x00"` check.
- Unicode Cc/Cf characters rejected via `unicodedata.category()`.
- Applies to ALL paths before any further logic — intentional strictest-first enforcement.

**Dot-dot resolution (BUG-121, BUG-122):**
- `posixpath.normpath()` called before `/memories/` prefix check — collapses `..` segments.
- `/memories/../../.github` → `/.github` → not a memory path → zone_classifier → deny.
- `/memories/session/../preferences.md` → `/memories/preferences.md` → not session → write denied.

**Case normalization (BUG-124):**
- `.lower()` applied to `norm_virtual` after normpath — before prefix check.
- `/MEMORIES/session/notes.md` recognized as virtual path after normalization.

**Virtual path detection:**
- `norm_virtual == "/memories"` handles bare root.
- `norm_virtual.startswith("/memories/")` handles all sub-paths.
- False prefixes (`/memoriesX/`, `/memories.evil/`, `/memories-backup/`) fall through to zone_classifier → deny.

**Write restriction:**
- `command` field detected case-insensitively via substring match on known write-op words.
- Non-string commands safely coerced to string (None/False/0 → `""` → read; list with "save" → detected).
- Writes to `/memories/session/` → allow. Writes to non-session paths → deny.
- Writes to bare `/memories/session` (no trailing slash, normpath removes slash, startswith misses) → deny. Correct.

**Non-virtual path passthrough:**
- Filesystem paths still go to `zone_classifier.classify()` unchanged. SAF-038 protections unaffected.

**Imports:** `import posixpath` (line 8) and `import unicodedata` (line 10) both present.

---

## SAF-048 Tests Coverage

| Category | Count | Result |
|---|---|---|
| BUG-113 regression (virtual read allow) | 3 | PASS |
| Virtual reads — all /memories/ sub-paths | 8 | PASS |
| Virtual writes — session allowed | 5 | PASS |
| Virtual writes — non-session denied | 5 | PASS |
| Fail-closed (no path / empty / None / wrong type) | 6 | PASS |
| Cross-platform (Windows backslash) | 2 | PASS |
| Filesystem path passthrough (SAF-038 regression) | 4 | PASS |
| Path traversal READ (BUG-121) | 4 | PASS |
| Path traversal WRITE (BUG-122) | 6 | PASS |
| Null bytes (BUG-123) | 3 | PASS |
| Case variations (BUG-124) | 4 | PASS |
| Unicode tricks (RLO, ZWNBSP, homoglyph) | 3 | PASS |
| Empty after normalization | 4 | PASS |
| False prefix boundary | 3 | PASS |
| Write to directory path | 2 | PASS |
| Non-string command handling | 4 | PASS |
| BUG-125 policy verification | 2 | PASS |
| Case normalization exact match | 2 | PASS |
| Long session paths | 2 | PASS |
| Command substring precision | 4 | PASS |
| **Total** | **76** | **ALL PASS** |

*(Plus 109 SAF-038 tests = 185 combined)*

---

## Notes

### Minor limitation noted (not a bug)
Write calls to the bare directory path `/memories/session/` (trailing slash normalized
away by `posixpath.normpath`) are denied. This is correct — memory tool writes
target files, not directories. Documented and verified by test.

### Command substring matching precision
The `any(op in command for op in _WRITE_OPS)` approach may produce false positives
for commands containing write-op substrings in unrelated words (e.g., `"recreation"`
does NOT contain `"create"` — verified). False positives result in denying non-session
writes — always the safe direction.

---

## Bugs Found This Iteration

None. BUG-125 (from Iteration 2) is Closed.

---

## Verdict

**PASS.**

All SAF-048 acceptance criteria met:
- memory view /memories/ → allow
- memory view /memories/session/ → allow
- memory write /memories/session/notes.md → allow
- Path traversal via .. → deny
- Null bytes and Unicode Cc/Cf characters → deny
- Case-insensitive virtual path recognition
- Non-session writes denied
- All SAF-038 tests still pass (no regressions)
- All 185 SAF-048 + SAF-038 tests pass
- Full suite regression check: 72 pre-existing failures (all on main), none from SAF-048
