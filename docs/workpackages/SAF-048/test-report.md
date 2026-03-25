# Test Report — SAF-048

**Tester:** GitHub Copilot (Tester Agent)
**Date:** 2026-03-25
**Iteration:** 1

---

## Summary

The Developer's 33 tests all pass and the SAF-038 regression is correctly fixed — `/memories/` and `/memories/session/` reads work, session writes work, and user-memory writes are denied as required.

However, tester edge-case tests reveal **18 security failures** across four vulnerability categories. Two are **high-severity security bypasses** that allow an adversarial model to evade the virtual-path special-casing and subvert the write-protection boundary. The WP cannot be approved in its current state.

**Verdict: FAIL — return to Developer.**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| SAF-048 developer tests (33 tests) | Unit | PASS (TST-2186) | All virtual reads, writes, fail-closed, cross-platform, BUG-113 regression |
| SAF-048 tester edge-cases (39 new tests) | Security | FAIL (TST-2187) | 18 failures — see detail below |
| SAF-036 – SAF-045 full suite | Regression | PASS | No regressions introduced by SAF-048 |
| SAF-001 – SAF-035 full suite | Regression | PASS* | *SAF-010 (2 failures) and SAF-025 (1 failure) are pre-existing on main and unrelated to SAF-048 |

---

## Failures Detail

### Category 1 — Path Traversal READ Bypass (HIGH severity) — BUG-121

**Root cause:** `norm_virtual = raw_path.replace("\\", "/")` normalises backslashes but does **not** resolve `..` segments. Any path that lexically starts with `/memories/` but contains dot-dots passes the virtual check unchallenged and returns `"allow"` — bypassing the zone classifier entirely.

| Failing test | Path | Current result | Expected |
|---|---|---|---|
| `test_traversal_to_security_gate_read` | `/memories/../../.github/hooks/scripts/security_gate.py` | `allow` | `deny` |
| `test_traversal_to_etc_passwd_read` | `/memories/../../../etc/passwd` | `allow` | `deny` |
| `test_traversal_to_env_file_read` | `/memories/../../.env` | `allow` | `deny` |
| `test_traversal_deep_in_session_read` | `/memories/session/../../../../etc/passwd` | `allow` | `deny` |

### Category 2 — session/../ WRITE Bypass (HIGH severity) — BUG-122

**Root cause:** The write guard `norm_virtual.startswith("/memories/session/")` is a string-prefix check, not a resolved-path check. `/memories/session/../preferences.md` passes the check lexically yet conceptually resolves to `/memories/preferences.md` (user memory), and `/memories/session/../../.github/secrets` escapes the entire `/memories/` namespace.

| Failing test | Path | Command | Current result | Expected |
|---|---|---|---|---|
| `test_session_dotdot_write_denied` | `/memories/session/../preferences.md` | `save` | `allow` | `deny` |
| `test_session_dotdot_write_to_repo_memory` | `/memories/session/../repo/creds.md` | `write` | `allow` | `deny` |
| `test_session_deep_traversal_to_github_write` | `/memories/session/../../.github/secrets` | `write` | `allow` | `deny` |
| `test_session_traversal_create_command` | `/memories/session/../preferences.md` | `create` | `allow` | `deny` |
| `test_session_traversal_update_command` | `/memories/session/../preferences.md` | `update` | `allow` | `deny` |
| `test_session_traversal_delete_command` | `/memories/session/../preferences.md` | `delete` | `allow` | `deny` |

### Category 3 — Null Bytes and Unicode Control Characters (MEDIUM severity) — BUG-123

**Root cause:** No character validation is performed on paths after the backslash normalization. Null bytes (`\x00`) and Unicode control/format characters (Right-to-Left Override U+202E, BOM/ZWNBSP U+FEFF) are passed through unchanged.

| Failing test | Path | Current result | Expected |
|---|---|---|---|
| `test_null_byte_in_session_path` | `/memories/session/\x00passwd` | `allow` | `deny` |
| `test_null_byte_in_user_memory_path` | `/memories/\x00evil` | `allow` | `deny` |
| `test_null_byte_write_to_session` | `/memories/session/\x00` (write) | `allow` | `deny` |
| `test_rtl_override_in_path` | `/memories/session/\u202enotes.md` | `allow` | `deny` |
| `test_zero_width_no_break_space_in_path` | `/memories/session/\ufeffnotes.md` | `allow` | `deny` |

### Category 4 — No Case Normalization (LOW severity) — BUG-124

**Root cause:** `norm_virtual = raw_path.replace("\\", "/")` does not lowercase the path before the `/memories/` prefix check. Paths with uppercase letters (e.g., `/MEMORIES/session/`) fall through to the zone classifier which denies them. Denying is safe but incorrect per WP requirements.

| Failing test | Path | Current result | Expected |
|---|---|---|---|
| `test_upper_memories_session_read` | `/MEMORIES/session/notes.md` | `deny` | `allow` |
| `test_mixed_case_memories_session_read` | `/Memories/Session/notes.md` | `deny` | `allow` |
| `test_upper_memories_session_write` | `/MEMORIES/session/notes.md` (save) | `deny` | `allow` |

---

## Bugs Found

- **BUG-121** (High): validate_memory path traversal bypass via `/memories/../../` — read allowed (logged in bugs.csv)
- **BUG-122** (High): validate_memory `session/../` write bypass allows writing to user memory (logged in bugs.csv)
- **BUG-123** (Medium): validate_memory allows null bytes and Unicode control chars in memory paths (logged in bugs.csv)
- **BUG-124** (Low): validate_memory does not normalize case — `/MEMORIES/` denied instead of allowed (logged in bugs.csv)

---

## TODOs for Developer

- [ ] **[BUG-121 / BUG-122 — Critical] Resolve dot-dot segments before the virtual-path check.**
  After `norm_virtual = raw_path.replace("\\", "/")`, apply `posixpath.normpath(norm_virtual)` (or equivalent) to collapse `..` and `.` segments. Only then apply the `startswith("/memories/")` check. This prevents both the read-bypass (BUG-121) and the write-bypass (BUG-122).

  ```python
  import posixpath
  norm_virtual = posixpath.normpath(raw_path.replace("\\", "/"))
  # Now /memories/../../.github normalizes to /.github — correctly excluded
  # and /memories/session/../preferences.md normalizes to /memories/preferences.md — denied for writes
  ```

- [ ] **[BUG-123 — Medium] Reject paths containing null bytes or Unicode control/format characters.**
  After normalizing to `norm_virtual`, check for disallowed characters:
  ```python
  import unicodedata
  _FORBIDDEN_CATS = {"Cc", "Cf"}  # Control, Format
  if "\x00" in norm_virtual or any(
      unicodedata.category(ch) in _FORBIDDEN_CATS for ch in norm_virtual
  ):
      return "deny"
  ```

- [ ] **[BUG-124 — Low] Add lowercase normalization so /MEMORIES/ is recognized as a virtual path.**
  Apply `.lower()` to `norm_virtual` before the `startswith("/memories/")` check.
  Note: the write check must also compare against the lowercased path.

- [ ] **Update `update_hashes.py`** after all code changes to keep the integrity hash consistent.

- [ ] **All new tests in `tests/SAF-048/test_saf048_tester_edge_cases.py` must pass** before re-submitting. Do not delete or weaken these tests.

---

## Verdict

**FAIL — return to Developer (In Progress).**

The core BUG-113 fix works correctly, and the Developer's tests pass. However, two high-severity security bypasses (path traversal read and `session/../` write bypass) allow the virtual-path shortcut to be exploited to subvert zone classification. In a project with the highest security classification, these must be fixed before the WP can be approved.
