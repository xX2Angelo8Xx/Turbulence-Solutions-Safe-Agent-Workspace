# Dev Log — SAF-002

**Developer:** Developer Agent
**Date started:** 2026-03-11
**Iteration:** 1

## Objective

Extract and harden the 3-tier zone classification logic from `security_gate.py` (SAF-001) into a standalone `zone_classifier.py` module. The module uses `pathlib.PurePosixPath.relative_to()` as the primary zone-membership check, hardening against prefix-match bypass attacks that string-startswith comparisons are vulnerable to. A pattern-based regex fallback (Method 2) is retained for paths that fall outside the workspace root. Update `security_gate.py` to delegate zone decisions to the new module.

Zones:
- **allow** — `Project/`
- **deny** — `.github/`, `.vscode/`, `NoAgentZone/`
- **ask** — everything else (default / fail-safe)

## Implementation Summary

### zone_classifier.py

New module at `Default-Project/.github/hooks/scripts/zone_classifier.py`. Implements:

- `normalize_path(p: str) -> str` — canonicalizes a raw path to lowercase forward-slash POSIX form: strips null bytes, converts backslashes, handles WSL `/mnt/c/...` and Git Bash `/c/...` prefixes, resolves `..` via `posixpath.normpath`.
- `classify(raw_path: str, ws_root: str) -> ZoneDecision` — 3-tier classifier.

**Method 1 (pathlib):** After normalizing and resolving relative paths against `ws_root`, constructs `PurePosixPath` objects and calls `.relative_to()`. Uses `.parts[0]` for first-segment identification. Unlike `str.startswith()`, `relative_to()` correctly rejects sibling prefixes (e.g., `project-evil/` does not match `project/`).

**Method 2 (regex fallback):** Pattern scan using `_BLOCKED_PATTERN` and `_ALLOW_PATTERN`. Catches paths from different roots, UNC paths, and any case where Method 1's `relative_to()` raises `ValueError`.

**Fail-closed design:** Default return is `"ask"` — no path accidentally receives `"allow"`.

### security_gate.py (updated)

- `import zone_classifier` added (simple module-level import; works because the scripts directory is on `sys.path` by the time the script runs, both in production and in tests).
- `get_zone()` replaced with a thin backward-compatible wrapper calling `zone_classifier.classify()`.
- `decide()` simplified: the manual normalization + `get_zone()` call is replaced by a single `zone_classifier.classify(raw_path, ws_root)` call. Zone classifier handles normalization and relative-path resolution internally.
- `normalize_path()` retained in security_gate.py (still used by terminal tool scanning in `decide()`).

### Key security properties preserved/improved

| Property | SAF-001 | SAF-002 |
|---|---|---|
| Path traversal (`../../.github/`) | Resolved via `posixpath.normpath` | Same — normalize_path in zone_classifier |
| Prefix-match bypass (`project-evil/`) | Method 2 pattern fallback | Method 1 `relative_to()` catches it; Method 2 still present |
| Null bytes | Stripped in `normalize_path` | Same — normalize_path in zone_classifier |
| UNC paths | Method 2 pattern fallback | Same behaviour |
| Fail-closed default | `"ask"` | `"ask"` |

## Files Changed

- `Default-Project/.github/hooks/scripts/zone_classifier.py` — created (SAF-002 deliverable)
- `Default-Project/.github/hooks/scripts/security_gate.py` — updated (imports zone_classifier; get_zone() delegated; decide() simplified)
- `tests/SAF-002/__init__.py` — created
- `tests/SAF-002/test_saf002_zone_classifier.py` — created (40 tests)
- `docs/workpackages/SAF-002/dev-log.md` — this file
- `docs/workpackages/workpackages.csv` — SAF-002 status updated to In Progress → Review

## Tests Written

**Unit — normalize_path:**
- `test_normalize_null_byte_stripped` — null byte removed before any comparison
- `test_normalize_double_backslash` — JSON double-escaped `\\` converted
- `test_normalize_single_backslash` — single `\` converted
- `test_normalize_wsl_prefix` — `/mnt/c/...` → `c:/...`
- `test_normalize_gitbash_prefix` — `/c/...` → `c:/...`
- `test_normalize_lowercase` — path fully lowercased
- `test_normalize_trailing_slash` — trailing `/` stripped
- `test_normalize_dotdot_resolved` — `..` components resolved

**Unit — classify() basic zones:**
- `test_classify_allow_project_root` — `Project/` → allow
- `test_classify_allow_project_nested` — `Project/src/main.py` → allow
- `test_classify_deny_github` — `.github/secret` → deny
- `test_classify_deny_vscode` — `.vscode/settings.json` → deny
- `test_classify_deny_noagentzone` — `NoAgentZone/private.md` → deny
- `test_classify_ask_docs` — `docs/readme.md` → ask
- `test_classify_ask_root_file` — `README.md` → ask
- `test_classify_ask_src` — `src/launcher/main.py` → ask

**Security — protection tests:**
- `test_classify_deny_github_method1` — `.github/` matched by Method 1
- `test_classify_allow_project_uses_relative_to` — `project/` matched by `relative_to()`

**Security — bypass attempt tests:**
- `test_bypass_path_traversal_dotdot` — `project/../.github/secret` denied after `..` resolution
- `test_bypass_deep_traversal` — `project/../../../../.github/x` denied
- `test_bypass_prefix_sibling` — `project-evil/.github/x` denied via Method 2
- `test_bypass_null_byte_before_github` — null byte before `.github` stripped then denied
- `test_bypass_unc_github` — `\\server\share\.github\secret` denied via Method 2
- `test_bypass_relative_path_github` — relative `.github/secret` resolved against ws_root and denied
- `test_bypass_mixed_case_github` — `.GITHUB/secret` lowercased and denied
- `test_bypass_mixed_case_noagentzone` — `NoAgentZone/file` lowercased and denied

**Cross-platform:**
- `test_cross_platform_windows_allow` — `C:\workspace\Project\main.py` allowed
- `test_cross_platform_windows_deny` — `C:\workspace\.github\secret` denied
- `test_cross_platform_wsl_allow` — `/mnt/c/workspace/project/x.py` allowed
- `test_cross_platform_wsl_deny` — `/mnt/c/workspace/.vscode/settings.json` denied
- `test_cross_platform_gitbash_allow` — `/c/workspace/project/main.py` allowed
- `test_cross_platform_gitbash_deny` — `/c/workspace/.github/secret` denied

**Integration (security_gate.py uses zone_classifier):**
- `test_security_gate_imports_zone_classifier` — zone_classifier importable from scripts dir
- `test_get_zone_backward_compat_allow` — `sg.get_zone()` still returns "allow" for Project/
- `test_get_zone_backward_compat_deny` — `sg.get_zone()` still returns "deny" for .github/
- `test_get_zone_backward_compat_ask` — `sg.get_zone()` still returns "ask" for docs/
- `test_decide_project_allow` — full decide() allows read_file on Project/
- `test_decide_github_deny` — full decide() denies read_file on .github/
- `test_decide_ask_zone` — full decide() returns ask for docs/
- `test_regression_all_saf001_tests_pass` — full SAF-001 test suite still passes

## Known Limitations

- Symlink resolution is not performed. `PurePosixPath` is used (no filesystem access), so a symlink inside `Project/` pointing to `.github/` would receive "allow". Symlink dereference would require `Path.resolve()` (filesystem access for each hook invocation) and is deferred.
- `ws_root` is still derived from `os.getcwd()` in `security_gate.py`. If the working directory does not match the workspace root, zone decisions may be incorrect. This limitation was documented in SAF-001 and is unchanged.

---

## Iteration 2 — 2026-03-11

### Tester Feedback Addressed

- **BUG-010** (TST-184, TST-185) — `normalize_path()` only stripped `\x00`. Other C0 control characters (`\t`, `\n`, `\r`, etc.) survived into zone comparison, allowing `\t.github` to bypass `_DENY_DIRS`. Fixed by replacing `p.replace("\x00", "")` with `re.sub(r'[\x00-\x1f]', '', p)` to strip the full C0 range (`\x00`–`\x1f`) in a single pass.
- **BUG-011** (TST-186) — Method 2's allow branch matched `_ALLOW_PATTERN` (`r"/project(/|$)"`) anywhere in the normalised path, including UNC paths on foreign hosts (`\\server\share\project\...`). Fixed by adding a workspace-containment guard: the allow branch now only fires when `norm.startswith(ws_clean + "/") or norm == ws_clean`. Paths outside the workspace root fall through to `"ask"`.

### Additional Changes

- None — both fixes are confined to `normalize_path()` and the Method 2 allow branch in `zone_classifier.py`. No other files were modified.

### Test Results

- SAF-002: **54/54 passed** (40 original + 14 Tester edge-case tests, including TST-184, TST-185, TST-186)
- SAF-001 regression: **60/60 passed** — no regressions
- Combined (SAF-001 + SAF-002): **114/114 passed**
