# SAF-073 Dev Log — Harden require-approval.sh fallback hook

## Status
Review

## Assigned To
Developer Agent

## Started
2026-04-02

## Objective
Harden the terminal command handler in `require-approval.sh` to block:
1. Environment variable exfiltration (`$env:`, `$HOME`, `$PATH`, etc.)
2. Command substitution (`$(cmd)`, backtick substitution)
3. Obfuscation patterns (`eval`, `base64 --decode`, `\x` hex escapes)
4. Sensitive system paths (`/etc/`, `/home/`, `/root/`, `/tmp/`, `c:/users/`, etc.)

## Bug Reference
BUG-176 — Bash/PS1 fallback hooks share same vulnerabilities as Python gate

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/require-approval.sh`
- `tests/SAF-073/test_saf073.py`

## Implementation Summary
Added four new deny blocks inside the `run_in_terminal|terminal|run_command` handler,
immediately after the existing blocked-folder check and before the `ASK` fallback:

1. **Env var exfiltration** — denies `$\{?env:` (PowerShell) and common sensitive
   Unix/shell env var names (`$HOME`, `$PATH`, `$USER`, `$USERNAME`, `$SECRET`,
   `$PASSWORD`, `$GITHUB_TOKEN`, `$API_KEY`, `$TOKEN`, `$AWS_*`, `$AZURE_*`).

2. **Command substitution** — denies `$(` (dollar-paren) and backtick+word-char
   patterns.

3. **Obfuscation** — denies `eval `, `eval(`, `base64.*decode`, and `\x` hex
   escape sequences.

4. **Sensitive system paths** — denies absolute paths to common sensitive
   directories (`/etc/`, `/home/`, `/root/`, `/tmp/`, `/var/`, `/opt/`, `/proc/`,
   `/sys/`, `c:/users/`, `c:/windows/`, `c:/program`).

## Tests Written
- `tests/SAF-073/test_saf073.py` — 11 scenarios using subprocess to invoke the
  actual bash script directly (bash available via Git Bash on Windows).
  Each test pipes a JSON payload to require-approval.sh and asserts the decision.

## Test Results
11/11 passed (TST-2450). All deny scenarios verified end-to-end via Git Bash subprocess.
Fixed \s→[[:space:]] in grep -E pattern (POSIX compliance for eval detection).

## Known Limitations
- Backtick detection uses a simple heuristic (`\`` followed by word char); very
  unusual backtick usage in JSON strings could produce false positives, but this
  is an acceptable trade-off for security.
