# SAF-074 Dev Log — Harden require-approval.ps1 fallback hook

## Status
In Progress

## Assigned To
Developer Agent

## Started
2026-04-02

## Objective
Harden the terminal command handler in `require-approval.ps1` to block:
1. Environment variable exfiltration (`$env:`, `${env:}`, `$HOME`, `$PATH`, etc.)
2. Dynamic execution (`Invoke-Expression`, `iex`, `Invoke-Command`, `$(...)`)
3. .NET type accelerators (`[IO.File]`, `[System.IO.File]`, `[Reflection.*]`, `Add-Type`)
4. Obfuscation patterns (`eval`, `base64 --decode`, `\x` hex escapes)
5. Sensitive system paths (`/etc/`, `/home/`, `c:/users/`, `c:/windows/`, etc.)

## Bug Reference
BUG-176 — Bash/PS1 fallback hooks share same vulnerabilities as Python gate

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/require-approval.ps1`
- `tests/SAF-074/test_saf074.py`

## Implementation Summary
Added five new deny blocks inside the `run_in_terminal|terminal|run_command` handler,
immediately after the existing `.github|.vscode|noagentzone` blocked-folder check
and before the `ASK` fallback. Mirrors the structure of SAF-073 for the bash hook.

1. **Env var exfiltration (PowerShell env: syntax)** — denies `$\{?env:` patterns
   (both `$env:VAR` and `${env:VAR}` forms).

2. **Sensitive env var names (curly-brace aware)** — denies `$\{?` followed by
   common sensitive variable names: home, path, user, username, secret, password,
   github_token, api_key, token, aws_, azure_, userprofile, appdata, programfiles.

3. **Dynamic execution** — denies `invoke-expression`, `iex`, `invoke-command`,
   `icm` as whole words; also denies `$(` dollar-paren command substitution.

4. **.NET type accelerators** — denies `[system.]io.(file|directory|path|...)`
   for file I/O; denies `[system.]reflection.` and `add-type` for code injection.

5. **Obfuscation** — denies `eval[space/(]`, `base64.*(-d|decode)`, and `\x[0-9a-f]{2}`
   hex escape sequences.

6. **Sensitive system paths** — denies absolute paths to common sensitive
   directories (`/etc/`, `/home/`, `/root/`, `/tmp/`, `/var/`, `/opt/`, `/proc/`,
   `/sys/`, `c:/users/`, `c:/windows/`, `c:/program`).

## Tests Written
- `tests/SAF-074/test_saf074.py` — 16 scenarios using subprocess to invoke the
  actual PowerShell script directly via `powershell -NoProfile -ExecutionPolicy Bypass`.
  Each test pipes a JSON payload to `require-approval.ps1` and asserts the decision.

## Test Results
16/16 passed (TST-2457). All deny scenarios verified end-to-end via PowerShell subprocess.
- env:USERNAME → deny ✓
- ${env:SECRET} → deny ✓
- $HOME → deny ✓
- ${HOME} → deny ✓
- Invoke-Expression → deny ✓
- iex → deny ✓
- $(whoami) → deny ✓
- [IO.File]::ReadAllText → deny ✓
- [System.IO.File]::ReadAllText → deny ✓
- Add-Type → deny ✓
- base64 --decode → deny ✓
- base64 -d → deny ✓
- cat /etc/passwd → deny ✓
- type c:\users\angel\secret.txt → deny ✓
- echo hello world → ask ✓ (no false positive)
- ls .github/hooks/ → deny ✓ (existing behavior preserved)

## Known Limitations
- `$HOME` and `${HOME}` detection catches common patterns; very unusual whitespace
  inside `${...}` could evade, but this is an acceptable trade-off consistent with
  the bash hook approach.
- The `$(` pattern blocks dollar-paren command substitution which is a valid
  PowerShell construct — this is intentional per security policy.
