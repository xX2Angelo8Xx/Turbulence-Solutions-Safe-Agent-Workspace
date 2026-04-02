# Test Report — SAF-073

**Tester:** Tester Agent (GitHub Copilot)
**Date:** 2026-04-02
**Iteration:** 1

## Summary

The core implementation is solid: 11 of 11 developer tests pass, covering the five main deny
categories (PowerShell env-var, Unix env-var, command substitution, eval/base64 obfuscation,
and sensitive system paths). The SAF regression suite shows zero new failures attributable to
SAF-073.

However, edge-case testing revealed **two distinct security bypasses** that allow exfiltration
commands to receive `ask` instead of `deny`. Both are High-severity gaps that fall squarely
within the scope of this WP.

---

## Tests Executed

| Test ID | Test Name | Type | Result | Notes |
|---------|-----------|------|--------|-------|
| TST-2451 | SAF-073 Developer Suite (11 tests) | Security | **Pass** | All 11 scenarios pass |
| TST-2452 | SAF-073 Tester Edge-Cases (13 tests) | Security | **Fail** | 2/13 fail (BUG-180, BUG-181) |
| TST-2453 | SAF Regression Suite | Regression | **Pass** | 0 new failures from SAF-073 |

### Edge-case detail (TST-2452)

| TC | Command | Expected | Actual | Result |
|----|---------|----------|--------|--------|
| E01 | `echo $home` (already lowercase) | deny | deny | PASS |
| E02 | `echo ${HOME}` (curly-brace syntax) | deny | **ask** | **FAIL** — BUG-180 |
| E03 | `echo $RANDOM` (non-sensitive var) | ask | ask | PASS — no false positive |
| E04 | `printenv HOME` (no $ prefix) | ask | ask | PASS — accepted limitation |
| E05 | `echo hello; cat /etc/passwd` (semicolons) | deny | deny | PASS |
| E06 | `echo aGVsbG8= \| base64 --decode` | deny | deny | PASS |
| E07 | `echo aGVsbG8= \| base64 -d` (short flag) | deny | **ask** | **FAIL** — BUG-181 |
| E08 | `cat ./project/file.txt` (relative path) | ask | ask | PASS — no false positive |
| E09 | `echo $PATH` | deny | deny | PASS |
| E10 | `export $TOKEN` | deny | deny | PASS |
| E11 | `eval(rm -rf /)` | deny | deny | PASS |
| E12 | `dir c:/windows/system32` | deny | deny | PASS |
| E13 | `cp secret.txt /tmp/exfil` | deny | deny | PASS |

---

## Bugs Found

- **BUG-180** (High): `require-approval.sh` — curly-brace env-var syntax `${HOME}` bypasses SAF-073 deny guard (logged in `docs/bugs/bugs.csv`)
- **BUG-181** (High): `require-approval.sh` — `base64 -d` short flag bypasses SAF-073 obfuscation deny guard (logged in `docs/bugs/bugs.csv`)

---

## Security Analysis

### BUG-180 — Curly-brace env-var bypass

The guard pattern `\$(home|path|user|...)` matches `$HOME` (dollar-sign immediately followed
by the variable name) but **not** `${HOME}` (curly-brace syntax). Both are valid bash for
expanding the same variable. After the hook normalises the input to lowercase, `echo ${HOME}`
becomes `echo ${home}`, and the pattern fails to match because `{` sits between `$` and `home`.

**Exploit vector:** An agent issues `echo ${HOME}/.ssh/id_rsa` — home-dir path exposure.
**Fix:** Extend the grep pattern to `\$\{?(home|path|user|...)` (add `\{?` to make the brace
optional), mirroring exactly the fix applied in BUG-177/BUG-178 for the Python security gate.

### BUG-181 — `base64 -d` short-flag bypass

The obfuscation guard pattern `base64.*decode` requires the word `decode` to appear after
`base64`. The POSIX short form `-d` performs identical decoding but does not contain `decode`.

**Exploit vector:** `echo <payload> | base64 -d | bash` — decode-and-execute attack.
**Fix:** Change the pattern to `base64.*(-d|--decode)` or, simpler and more robust,
`\bbase64\b` (deny any command that invokes `base64` at all, regardless of flag).

### No false positives in safe commands

- `echo $RANDOM`, `printenv HOME`, and `cat ./project/file.txt` all correctly return `ask`.
- Semicolon-chained commands properly evaluated; the `/etc/` path in the second half is caught.
- `eval(cmd)` (parenthesis form) correctly denied.
- Case-insensitive matching confirmed via lowercase input test.

---

## TODOs for Developer

- [ ] **Fix BUG-180**: In the `\$(home|path|user|...)` grep pattern, extend it to
  `\$\{?(home|path|user|username|secret|password|github_token|api_key|token|aws_|azure_)`
  (insert `\{?` after `\$` to also match `${VARNAME}` form). Verify with:
  - `echo ${HOME}` → deny
  - `echo ${PATH}` → deny
  - `echo ${TOKEN}` → deny
  - `echo ${RANDOM}` → ask (no false positive — `random` is not in the list)

- [ ] **Fix BUG-181**: Replace the `base64.*decode` pattern with `\bbase64\b` to deny any
  invocation of `base64` regardless of flag. Simpler and more secure — there is no legitimate
  reason for an agent to invoke the base64 binary. Verify with:
  - `echo aGVsbG8= | base64 -d` → deny
  - `echo aGVsbG8= | base64 --decode` → deny (regression)
  - `echo hello | base64` (encode-only) → deny (acceptable to over-block here)

- [ ] Ensure the two new test cases in `tests/SAF-073/test_saf073_edge_cases.py` pass:
  - `test_deny_env_var_home_curly_braces`
  - `test_deny_base64_short_flag`

---

## Verdict

**FAIL — return to Developer (In Progress)**

Two High-severity security bypasses confirmed by reproducible tests. Both are within the
declared scope of SAF-073 (env-var exfiltration and obfuscation blocking). The fixes are
small (one regex character insertion each) and well-defined in the TODOs above.
