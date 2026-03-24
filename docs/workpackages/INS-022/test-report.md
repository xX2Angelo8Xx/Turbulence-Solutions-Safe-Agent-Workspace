# Test Report — INS-022: Create persistent settings module

| Field | Value |
|-------|-------|
| WP ID | INS-022 |
| Tester | Tester Agent |
| Date | 2026-03-24 |
| Branch | `INS-022/persistent-settings` |
| Verdict | **PASS** |

---

## Summary

All 43 tests pass (21 developer + 22 tester edge cases). No regressions introduced in the wider test suite. One low-severity known-limitation bug logged (BUG-100).

---

## Review Findings

### Code quality

`src/launcher/core/user_settings.py` is clean, stdlib-only, and well-structured.

| Check | Result |
|-------|--------|
| Public API matches WP spec | ✅ |
| OS-appropriate path (Windows / macOS / Linux / XDG) | ✅ |
| Atomic write (tempfile + os.replace) | ✅ |
| Missing file → defaults returned without raising | ✅ |
| Corrupt file (invalid JSON) → defaults returned | ✅ |
| Non-dict JSON → defaults returned | ✅ |
| Temp file cleaned up on write failure | ✅ |
| No secrets / absolute paths | ✅ |
| No eval/exec | ✅ |
| Default settings schema (`include_readmes: True`) | ✅ |
| Default merging (new keys from defaults added; user overrides preserved) | ✅ |

### User Story AC verification (US-039 — INS-022 scope only)

> AC 2: The checkbox state is persisted in OS-appropriate user settings and
> restored on later launches.

The module provides `load_settings()` / `save_settings()` / `get_setting()` /
`set_setting()` with OS-appropriate paths and full persistence. ✅

> AC 5 (implied): Settings survive app restarts, missing files, and corruption.

`load_settings()` catches all exceptions and falls back to defaults. ✅

---

## Test Runs

| ID | Name | Type | Result | Notes |
|----|------|------|--------|-------|
| TST-2064 | INS-022 developer tests (21) | Unit | Pass | All 21 developer-authored tests |
| TST-2065 | INS-022 tester edge-case tests (22) | Unit | Pass | 22 edge-case tests added by Tester |

---

## Edge Cases Tested (Tester additions — `test_ins022_edge_cases.py`)

| Class | Scenario |
|-------|----------|
| `TestUnicodeHandling` | Emoji, CJK, Arabic in values; non-ASCII key names; UTF-8 on disk (ensure_ascii=False) |
| `TestNestedDicts` | 2-level and 4-level nested dicts round-trip |
| `TestFalsyValues` | `False`, `0`, `""`, `None`, `[]` each preserved through save/load |
| `TestReadErrors` | PermissionError on read → defaults; raw binary (invalid UTF-8) → defaults |
| `TestWriteErrors` | PermissionError on os.replace propagates; no .tmp files left; original file untouched |
| `TestConcurrentWrites` | 5 threads × 20 writes each; file stays valid JSON even if some writes raise PermissionError |
| `TestLargePayload` | 500-key dict round-trips without data loss |
| `TestSpecialKeyCharacters` | Dots and spaces in key names preserved |
| `TestWindowsPathFallback` | Missing LOCALAPPDATA falls back to `~/AppData/Local` |
| `TestEmptyDict` | Empty dict saved correctly; defaults merged; overwrite replaces file |

---

## Bugs Found

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| BUG-100 | `save_settings`: `os.replace()` PermissionError on Windows under concurrent writes | Low | Open |

**BUG-100 detail:** On Windows, concurrent calls to `save_settings()` from multiple
threads can raise `PermissionError(13)` when two temp files race to `os.replace()`
to the same destination. This is a known Windows limitation (same root cause as
BUG-096/SAF-037). The file is **never** left corrupt — the atomic-write guarantee
holds. Normal single-threaded usage is fully correct. Thread safety is out of scope
for INS-022. Recommend a future WP to add a `threading.Lock` if concurrent writes
become a real use case.

---

## Regression Check

The broader test suite (excluding 14 directories with pre-existing `PyYAML` import
errors unrelated to this WP) shows 72 pre-existing failures (all in INS-019,
SAF-010, SAF-022, SAF-025) that are confirmed pre-existing on this branch.
INS-022 introduces zero new failures.

---

## Verdict

**PASS** — Implementation is correct, complete, and well-tested. WP status → Done.
