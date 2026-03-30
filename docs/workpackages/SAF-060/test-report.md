# SAF-060 Test Report

**WP ID:** SAF-060  
**Branch:** SAF-060/memory-fix  
**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Verdict:** PASS ✅

---

## 1. Summary

The one-line fix in `validate_memory()` — adding `tool_input.get("path")` as a fallback after `tool_input.get("filePath")` — correctly resolves BUG-137. The VS Code memory tool sends the path under the `"path"` key inside `tool_input`; the original code only checked `"filePath"`, causing all memory operations to fail closed.

The fix is minimal, targeted, and does not weaken any security property. All 39 developer and tester tests pass. Zero new regressions across the full suite.

---

## 2. Code Review

**File:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`  
**Function:** `validate_memory()` (line 2712)

### Fix correctness

```python
raw_path = tool_input.get("filePath")
if not isinstance(raw_path, str) or not raw_path:
    # SAF-060: VS Code memory tool sends path as "path" key, not "filePath"
    raw_path = tool_input.get("path")
if not isinstance(raw_path, str) or not raw_path:
    raw_path = data.get("filePath")
if not isinstance(raw_path, str) or not raw_path:
    raw_path = data.get("path")
if not isinstance(raw_path, str) or not raw_path:
    return "deny"
```

**Assessment:** Correct. The fallback chain maintains the correct priority:
1. `tool_input["filePath"]` (original VS Code hook format)
2. `tool_input["path"]` (actual VS Code memory tool format — SAF-060 fix)
3. `data["filePath"]` (top-level legacy)
4. `data["path"]` (top-level fallback)
5. Fail closed → `"deny"`

**Security impact:** No weakening. The added fallback only changes which key is examined for path extraction; all downstream validation (normpath, lower, zone classification, write-protection boundary) remains unchanged.

**Docstring:** Updated to reflect the SAF-060 change — `"path"` key is now mentioned in the extraction logic.

---

## 3. Test Results

| Test Run | Type | Tests | Result | TST ID |
|----------|------|-------|--------|--------|
| SAF-060 developer tests | Unit | 15 passed | ✅ Pass | TST-2254 |
| SAF-060 tester edge cases | Security | 24 passed | ✅ Pass | TST-2255 |
| SAF-048 regression suite | Regression | 77 passed | ✅ Pass | TST-2256 |
| Full suite regression check | Regression | 7114 passed, 73 pre-existing | ✅ Pass | TST-2257 |

**Total SAF-060 tests: 39** (15 developer + 24 tester)

---

## 4. Edge Cases Tested (Tester-Added)

### Path traversal (`TestPathTraversal`)
| Test | Expected | Result |
|------|----------|--------|
| `/memories/../.github/hooks/security_gate.py` create | deny | ✅ deny |
| `/memories/session/../../.github/` create | deny | ✅ deny |
| `/memories/../etc/passwd` read | deny | ✅ deny |
| `/MEMORIES/../.GITHUB/hooks/script.py` create (mixed case) | deny | ✅ deny |
| `/memories/session/../preferences.md` read (resolves inside /memories/) | allow | ✅ allow |
| `/memories/session/../preferences.md` save (write outside session) | deny | ✅ deny |

### Invalid path values (`TestInvalidPathValues`)
| Value | Expected | Result |
|-------|----------|--------|
| `""` empty string | deny | ✅ deny |
| `None` | deny | ✅ deny |
| `42` integer | deny | ✅ deny |
| `["/memories/"]` list | deny | ✅ deny |
| `"/"` root slash | deny | ✅ deny |
| `"   "` whitespace only | deny | ✅ deny |

### Conflicting filePath + path keys (`TestConflictingPathKeys`)
| Scenario | Expected | Result |
|----------|----------|--------|
| `filePath=/memories/` (safe) + `path=/etc/passwd` (malicious) | allow (filePath wins) | ✅ allow |
| `filePath=/etc/passwd` (dangerous) + `path=/memories/` (safe) | deny (filePath wins) | ✅ deny |
| `filePath=/.github/config` (dangerous) + `path=/memories/session/` + create | deny | ✅ deny |
| `filePath=""` + `path=/memories/session/notes.md` | allow (falls through to path) | ✅ allow |
| `filePath=None` + `path=/etc/passwd` | deny (path key used, denied) | ✅ deny |

### System-level paths (`TestSystemPaths`)
| Path | Expected | Result |
|------|----------|--------|
| `/etc/passwd` | deny | ✅ deny |
| `/etc/shadow` | deny | ✅ deny |
| `C:\Windows\system.ini` | deny | ✅ deny |
| `C:\Windows\System32` | deny | ✅ deny |

### `"data"` field not used as fallback (`TestDataFieldNotFallback`)
| Scenario | Expected | Result |
|----------|----------|--------|
| `tool_input={"data": "/memories/"}` | deny (fail closed) | ✅ deny |
| Top-level `{"data": "/memories/"}` | deny (fail closed) | ✅ deny |
| `tool_input={"data": "/memories/session/notes.md", "command": "create"}` | deny | ✅ deny |

---

## 5. Security Analysis

### Priority conflict: `filePath` vs `path`
`filePath` is checked first, so it cannot be overridden by a supplied `"path"` key. An attacker cannot whitelist themselves by adding a safe `"path"` key alongside a malicious `"filePath"` — confirmed by test.

### Traversal via new `"path"` key
Path traversal through `..` segments is normalized by `posixpath.normpath()` before the `/memories/` prefix check, so `/memories/../.github/` correctly denies. The existing dot-segment normalization logic works correctly with the new `"path"` key — SAF-060 doesn't change it, and tester confirmed it works end-to-end.

### `"data"` field not exploitable
The extraction chain does not include a `"data"` key at any level. Any path supplied only in `"data"` causes a fail-closed deny. No new attack surface introduced.

### No schema expansion risk
The fix adds one fallback key (`tool_input["path"]`). This is the documented VS Code memory tool schema. No unexpected key sources are added.

---

## 6. Regressions

- **SAF-048 (memory tool):** 77/77 tests pass. No regressions.
- **Full suite:** Failure count identical to `main` baseline (73 pre-existing failures, none introduced by SAF-060).
- **DOC-008 pre-existing failure:** `test_existing_content_preserved` fails on both `main` and this branch — not related to SAF-060.

---

## 7. Bugs Found

No new bugs. The fix addresses BUG-137 completely.

---

## 8. Verdict

**PASS** — SAF-060 is approved for merge.

- Root cause correctly identified and fixed
- Fix is minimal and doesn't weaken any security property
- `filePath` priority over `path` confirmed (no bypass possible)
- Traversal, empty/null, system paths, and data-field vectors all denied
- Zero new regressions
