# SAF-041 Test Report

## Summary

| Field | Value |
|-------|-------|
| **WP ID** | SAF-041 |
| **WP Name** | Add shell utility commands to terminal allowlist |
| **Tester** | Tester Agent |
| **Date** | 2026-03-24 |
| **Verdict** | **PASS** |

---

## Scope

Tested that `touch`, `chmod`, and `ln` were correctly added to the terminal
allowlist in `security_gate.py` (Category J) with `path_args_restricted=True`
and appear in `_PROJECT_FALLBACK_VERBS`.

---

## Code Review

| Check | Result |
|-------|--------|
| `touch` in `_COMMAND_ALLOWLIST` with `path_args_restricted=True` | ✅ Confirmed (line 634) |
| `chmod` in `_COMMAND_ALLOWLIST` with `path_args_restricted=True` | ✅ Confirmed (line 641) |
| `ln` in `_COMMAND_ALLOWLIST` with `path_args_restricted=True` | ✅ Confirmed (line 648) |
| All three in `_PROJECT_FALLBACK_VERBS` | ✅ Confirmed (line 1383) |
| `allow_arbitrary_paths=False` on all three | ✅ Confirmed |
| Hash updated after security_gate.py change | ✅ hash sync tests pass (TST-SAF-025) |
| Cross-zone ln protection (both path args zone-checked) | ✅ Relies on `_validate_args` step 5 which iterates ALL token-args — no special case needed |

---

## Test Runs

| Test ID | Name | Type | Tests | Result |
|---------|------|------|-------|--------|
| TST-2055 | SAF-041 developer shell utility tests | Unit | 23 | ✅ PASS |
| TST-2056 | SAF-041 tester edge-case tests | Security | 17 | ✅ PASS |
| TST-2057 | SAF-041 full suite regression check | Unit | 4884 | ✅ PASS (no regressions) |

**Total: 40 SAF-041 tests, all passing.**

---

## Developer Tests (23)

- **touch**: allowed in project, denied for `.github/`, `.vscode/`, `NoAgentZone/`, outside root; multiple targets; mixed (any outside → deny)
- **chmod**: allowed with numeric mode (`755`) and recursive flag (`-R`) in project; denied for `.github/`, `.vscode/`, `NoAgentZone/`, outside root
- **ln**: both paths in project → allowed; source outside → denied; target in `.github/`/`.vscode/`/`NoAgentZone/` → denied; source in `.github/` → denied; both outside → denied; `ln -s` (soft) both project → allowed; cross-zone bridge attempts denied

---

## Tester Edge-Case Tests (17)

### ln flag variants and path traversal
- `ln -s` (symbolic) both project → **PASS allowed**
- `ln -sf` (force soft) both project → **PASS allowed**
- `ln --symbolic` (long flag) both project → **PASS allowed**
- `ln` with `project/src/../../.github/evil.sh` path traversal → **PASS denied** (zone classifier resolves and rejects)
- `ln` with `project/../../NoAgentZone/secret.txt` traversal → **PASS denied**
- `ln` single arg (hard link, no link_name) in project → **PASS allowed**
- `ln` single arg absolute outside → **PASS denied**
- `ln` single arg `.github/` path → **PASS denied**

### touch dotfiles
- `touch project/.env` → **PASS allowed** (dotfiles inside project are fine)
- `touch project/.gitignore` → **PASS allowed**
- `touch .github/.env` → **PASS denied** (restricted zone, dotfile irrelevant)

### chmod symbolic modes and outside-project
- `chmod +x project/src/newfile.txt` → **PASS allowed**
- `chmod a+r project/src/newfile.txt` → **PASS allowed**
- `chmod u=rw project/src/newfile.txt` → **PASS allowed**
- `chmod +x ./root_config.json` → **PASS denied** (outside project)
- `chmod 755 c:/external/other_project/file.txt` → **PASS denied**  
- `chmod +x project/../../.github/hooks/pre-tool-call.sh` → **PASS denied** (traversal into restricted zone)

---

## Security Analysis

**Attack vectors considered:**

1. **Path traversal via `../../`** — The zone classifier normalises paths before classification; traversals into `.github/`, `.vscode/`, and `NoAgentZone/` are correctly denied. Verified in edge-case tests.

2. **Symlink bridge attack** — `ln -s /etc/passwd project/evil` would be denied because `/etc/passwd` is outside the workspace. `ln project/file .github/evil` is also denied (`.github/` target). Both endpoints are checked, so no single-endpoint bypass is possible.

3. **Flag injection** — `ln -sf` and `ln --symbolic` are handled automatically; flags are stripped from path-arg classification, and the path tokens are still zone-checked regardless of which flags are present.

4. **chmod privilege escalation on project files** — Allowed, but scoped to project folder only. This is intentional — agents need to make scripts executable.

5. **chmod on restricted-zone files** — Denied. An agent cannot `chmod 777 .github/hooks/pre-tool-call.sh` to weaken the hook.

6. **Windows compatibility** — `chmod` and `ln` are POSIX commands not present on Windows. The gate allows them if invoked, but the OS will simply not find the binary. No Windows-specific bypass possible.

7. **Off-by-one / boundary** — `ln` with one argument exercises the "no second path arg" path through the validator; the single path is still zone-checked.

**No security issues found.**

---

## Regression

Full test suite (excluding 14 pre-existing yaml-module collection errors and 71 pre-existing failures already present on `main`) shows **0 new failures**. SAF-041 adds 40 new passing tests.

---

## Verdict

**PASS** — Implementation is correct, complete, and secure. All acceptance criteria for ACs 2–4 of US-036 are satisfied. No regressions introduced.
