# Test Report — SAF-048

**Tester:** GitHub Copilot (Tester Agent)
**Date:** 2026-03-25
**Iteration:** 2 (re-test after Developer Iteration 2 fixes)

---

## Summary

**Developer Iteration 2 fixes are effective** — all 18 previously failing security edge-case tests now pass.
All 57 SAF-048 tests (33 developer + 24 tester) pass.
BUG-121 (path traversal read), BUG-122 (session/../ write bypass), BUG-123 (null bytes/unicode), and BUG-124 (case normalization) are all resolved.

However, the fix for BUG-123 introduces a **regression in a pre-existing SAF-038 test**: the null byte + Unicode control char check was placed BEFORE the virtual/filesystem path branch, so it now also rejects real filesystem paths with embedded null bytes. Before SAF-048, these went to `zone_classifier.classify()` which strips C0 control chars and allows paths that resolve inside the project. After SAF-048, they are denied early. This breaks `test_memory_null_byte_in_project_path_allow` in `tests/SAF-038/`. BUG-125 logged.

**Verdict: FAIL — return to Developer (Iteration 3).**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| SAF-048 developer tests (33) | Unit | PASS (TST-2186) | All virtual reads, writes, fail-closed, cross-platform, BUG-113 regression |
| SAF-048 tester edge-cases (24) | Security | **PASS** (TST-2185) | All 24 previously-failing traversal/null-byte/case tests now pass — BUG-121..124 fixed |
| SAF-048 full suite (57 tests) | Unit + Security | **PASS 57/57** (TST-2188) | 57 passed, 0 failed |
| SAF-038 regression check | Regression | **FAIL** | `test_memory_null_byte_in_project_path_allow` now returns `deny`; expected `allow` — BUG-125 |
| SAF-025 pycache check | Regression | FAIL (pre-existing) | `__pycache__` present from prior test runs; gitignored artifact, unrelated to SAF-048 |
| Full test suite (6,533 passing) | Regression | 73 pre-existing failures | All 73 failures confirmed present on `main` branch; none caused by SAF-048 except BUG-125 |

---

## SAF-048 Tests (All Pass)

All 18 tests that were failing in Iteration 1 now pass:

| Category | Tests | Result |
|---|---|---|
| Path traversal READ (BUG-121) | 4 tests | PASS |
| session/../ WRITE bypass (BUG-122) | 6 tests | PASS |
| Null bytes + Unicode Cc/Cf (BUG-123) | 3 + 3 = 6 tests | PASS |
| Case normalization (BUG-124) | 4 tests | PASS |

---

## Regression Found

### BUG-125 — SAF-048 null byte check denies filesystem project paths (HIGH)

**Root cause:** The null byte and Unicode control char check in `validate_memory()` is placed after `raw_path.replace("\\", "/")` but BEFORE the virtual-path branch. It applies to ALL paths — both virtual `/memories/` paths AND real filesystem paths. Before SAF-048, filesystem paths went directly to `zone_classifier.classify()`, which calls `normalize_path()` that **strips** C0 control characters (inc. `\x00`) before classification.

**Failing test:**
- `tests/SAF-038/test_saf038_edge_cases.py::TestNullByteInjection::test_memory_null_byte_in_project_path_allow`
- Path: `/workspace/project/memories\x00/notes.md`
- Before SAF-048: `zone_classifier` strips `\x00` → path resolves inside project → `allow`
- After SAF-048: null byte check fires → `deny`

**Reproduction:**
```
pytest tests/SAF-038/test_saf038_edge_cases.py::TestNullByteInjection::test_memory_null_byte_in_project_path_allow -v
```

---

## Bugs Found This Iteration

- **BUG-125** (High): SAF-048 null byte check in validate_memory() denies SAF-038 project-path with null byte (logged in bugs.csv, ID auto-assigned, TST-2189)

---

## TODO for Developer (Iteration 3)

Choose ONE of the following fix paths and implement it:

### Option A — Keep strict null byte denial everywhere (RECOMMENDED from security perspective)

Change the SAF-038 test to expect `"deny"` for the null byte in project-path case. Add a comment in both test and production code documenting this intentional policy change:

**In `tests/SAF-038/test_saf038_edge_cases.py`:**
```python
def test_memory_null_byte_in_project_path_allow(self):
    # POLICY CHANGE SAF-048: null bytes are now denied immediately in validate_memory()
    # before zone_classifier is consulted. This is stricter than the old
    # strip-then-classify behavior but is correct: null bytes are never
    # legitimate in memory tool file paths.
    path = f"{WS}/project/memories\x00/notes.md"
    data = {"tool_input": {"filePath": path}}
    assert sg.validate_memory(data, WS) == "deny"  # Changed from "allow" by SAF-048
```

**In `security_gate.py` `validate_memory()` docstring**, add a note that null bytes in filesystem paths are now denied immediately (changed from SAF-038's strip-then-classify behavior).

### Option B — Scope null byte check to virtual paths only

Move the null byte/unicode check to INSIDE the virtual-path branch. Filesystem paths (non-virtual) continue to zone_classifier which already strips C0 chars:

```python
norm_virtual = raw_path.replace("\\", "/")
norm_virtual = posixpath.normpath(norm_virtual)
norm_virtual = norm_virtual.lower()

if norm_virtual == "/memories" or norm_virtual.startswith("/memories/"):
    # BUG-123: Reject null bytes and Unicode control/format chars
    # only for virtual memory paths (filesystem paths go to zone_classifier
    # which already strips C0 chars via normalize_path).
    _FORBIDDEN_CATS = {"Cc", "Cf"}
    raw_for_check = raw_path.replace("\\", "/")
    if "\x00" in raw_for_check or any(
        unicodedata.category(ch) in _FORBIDDEN_CATS for ch in raw_for_check
    ):
        return "deny"
    # ... write check etc.
```

> Note: this requires the forbidden-char check to operate on the original `raw_path` characters (before normpath which would strip the null) — use a pre-normpath copy.

### Requirements for Iteration 3 re-submission

- [ ] All 57 SAF-048 tests must continue to pass (do NOT weaken them).
- [ ] `tests/SAF-038/test_saf038_edge_cases.py::TestNullByteInjection::test_memory_null_byte_in_project_path_allow` must pass.
- [ ] Re-run `update_hashes.py` after any code change to `security_gate.py`.
- [ ] Mark BUG-125 as `Fixed In WP = SAF-048` in `bugs.csv`.
- [ ] Log new test results via `scripts/add_test_result.py`.

---

## Verdict

**FAIL — return to Developer (In Progress). Iteration 3 required.**

The four security fixes from Iteration 1 are all correctly implemented. The only blocker is the BUG-125 regression: the null byte check scope is too broad and silently changed the behavior for SAF-038's existing test. One targeted change to either the test or the code placement will clear this.
