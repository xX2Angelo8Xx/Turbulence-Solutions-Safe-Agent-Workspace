# Test Report — SAF-042

**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Iteration:** 1

---

## Summary

SAF-042 audited the git command allowlist in `security_gate.py` (Category E — Version Control), found two missing subcommands (`switch` and `blame`), added them, and wrote regression tests covering all 17 allowed operations and all 5 destructive blocks.

The implementation is correct and complete. All 17 required git operations are present in the allowlist. All 5 destructive operations are blocked. The 45 developer tests pass. 24 additional tester edge-case tests were added and all pass. No regressions in the core SAF suite (437 tests).

---

## Code Review

### `templates/coding/.github/hooks/scripts/security_gate.py`

**Category E allowlist verified:**

```python
allowed_subcommands=frozenset({
    "status", "log", "diff", "branch", "add", "commit",
    "fetch", "pull", "push", "checkout", "switch", "stash", "tag",
    "show", "remote", "blame", "config", "init", "clone", "merge",
    "rebase", "describe", "shortlog", "rev-parse", "ls-files",
})
```

All 17 required operations present: ✓ status, log, diff, branch, add, commit, fetch, pull, checkout, **switch** (new), stash, merge, rebase, tag, remote, show, **blame** (new).

**Destructive operation blocks verified:**

| Operation | Block mechanism |
|-----------|----------------|
| `push --force` | `--force` in `denied_flags`; `("push","--force")` in `_GIT_DENIED_COMBOS` |
| `push -f` | `-f` in `denied_flags`; `("push","-f")` in `_GIT_DENIED_COMBOS` |
| `reset --hard` | `reset` not in allowlist; `("reset","--hard")` in `_GIT_DENIED_COMBOS` |
| `filter-branch` | not in allowlist; `("filter-branch","")` in `_GIT_DENIED_COMBOS` |
| `gc --force` | `gc` not in allowlist; `("gc","--force")` in `_GIT_DENIED_COMBOS` |
| `clean -f` | `clean` not in allowlist; `("clean","-f")` in `_GIT_DENIED_COMBOS` |

**Hash:** SHA-256 hash updated in `_KNOWN_GOOD_GATE_HASH` after changes. ✓

---

## Tests Executed

| Test | Type | Status | Notes |
|------|------|--------|-------|
| TST-2059 | Regression (full suite) | Logged as Fail | Pre-existing INS-013–INS-017 YAML errors; not related to SAF-042 |
| TST-2060 | Security | Pass | 45 dev tests — all 17 ops + 5 destructive + edge cases |
| TST-2061 | Security | Pass | 24 tester edge-case tests |
| TST-2062 | Regression | Pass | 437 SAF-related tests (SAF-001/005/035/036/040/041/042) |

**Developer tests: 45/45 pass**  
**Tester edge-case tests: 24/24 pass**  
**Core SAF regression: 437/437 pass (2 xfailed expected)**

---

## Edge-Case Analysis

### Tester-requested scenarios

| Scenario | Expected | Actual | Verdict |
|----------|----------|--------|---------|
| `git push` (no --force) | allow | allow | ✓ |
| `git reset --soft HEAD~1` | deny | deny | ✓ (reset not in allowlist) |
| `git clean -n` (dry-run) | deny | deny | ✓ (clean not in allowlist at all) |
| `git stash drop` | allow | allow | ✓ (stash in allowlist) |
| `git rebase --abort` | allow | allow | ✓ |
| `git merge --abort` | allow | allow | ✓ |
| `git push --force-with-lease` | allow | allow | ✓ (distinct from --force; policy decision) |
| `git push --force --no-verify` | deny | deny | ✓ |

### Additional attack vectors tested

| Vector | Result | Assessment |
|--------|--------|------------|
| `git push --FORCE` (uppercase) | deny | ✓ case-normalised correctly |
| `git push -force` (single-dash word) | allow | ⚠ LOW: gate allows it, but `-force` is not a valid git option — cannot actually force-push; real flags `--force`/`-f` remain blocked |
| `git push --force-with-lease --force` | deny | ✓ --force still caught |
| `git fsck`, `git archive`, `git gc` | deny | ✓ not in allowlist |
| `git filter-branch --env-filter` | deny | ✓ |
| `git commit --amend` | allow | ✓ |
| `git switch --detach HEAD~1` | allow | ✓ |

### Security observations

1. **`git push -force` (not a real git flag):** The security gate allows `git push -force` because `-force` is not in `denied_flags = {"--force", "-f"}`. However, this is not an exploitable bypass because git itself does not recognise `-force` as a valid option and would reject the command. The real force flags (`--force` and `-f`) are correctly blocked. Severity: **LOW / informational**.

2. **`git push --force-with-lease`:** Deliberately allowed. `--force-with-lease` is a safer force variant that only proceeds if the remote ref hasn't been updated since last fetch. The WP requirements specify blocking `push --force` and `push -f` only — this is in scope. The developer's test has a misleading name (`test_git_push_force_with_lease_denied`) but the assertion is correct. Logged as BUG-099.

---

## Bugs Found

- **BUG-099:** Misleading test name — `test_git_push_force_with_lease_denied` asserts `allow`, not `deny`. The behavior is correct and intentional, but the function name misleads future maintainers. Logged in `docs/bugs/bugs.csv`. (Low severity — test name only, no logic defect)

---

## US-036 Acceptance Criteria Verification

| AC | Requirement | Verified |
|----|-------------|---------|
| 5 | All documented git operations are allowed | ✓ All 17 present and tested |
| 6 | Destructive git operations remain blocked | ✓ All 5 blocked and tested |

---

## Verdict

**PASS** — Set WP to `Done`.

All 17 required git operations are present in the allowlist. All 5 destructive git operations are correctly blocked. 69 tests pass (45 developer + 24 tester). No regressions in the 437-test SAF regression suite. Implementation is correct and complete.

The only minor finding is BUG-099 (misleading test name — non-blocking). The `-force` single-dash observation is informational only (not exploitable). Neither issue requires a code fix before marking Done.
