# Dev Log — SAF-004

**Developer:** Developer Agent
**Date started:** 2026-03-10
**Iteration:** 1

## Objective

Write a design document specifying the allowlist approach for terminal command sanitization.
The document must define permitted command patterns, document all known edge cases (string
fragmentation, variable concatenation, multi-interpreter bypasses), and be detailed enough
that SAF-005 can be implemented purely from reading it. Addresses audit finding 1 (the current
shell scripts use simple string-literal pattern matching that is bypassable).

## Implementation Summary

Created `docs/workpackages/SAF-004/terminal-sanitization-design.md`.

The design document specifies:

- **Threat model**: five distinct attack vectors (direct zone access, string fragmentation,
  variable concatenation, multi-interpreter bypass, encoding bypass / obfuscation)
- **Design principles**: allowlist > denylist, fail-closed, defence-in-depth, no in-hook
  evaluation of shell commands
- **5-stage detection pipeline**: extract → normalize → pre-scan obfuscation → tokenize →
  allowlist match
- **Obfuscation pre-scan patterns**: 15 regex patterns that trigger an immediate deny
  before the allowlist is consulted (catches all known bypass families)
- **Allowlist specification**: 10 command categories (Python runtime, pip, pytest, build tools,
  git, Node/npm ecosystem, read-only file inspection, environment inspection, VS Code CLI,
  shell utilities) with per-command allowed argument rules and denied flags listed explicitly
- **Denied-pattern catalogue**: explicit denylist of ~25 command/flag patterns as a safety-net
  second layer beneath the allowlist
- **Edge case analysis**: string fragmentation, variable concatenation, multi-interpreter,
  encoded commands, pipe-to-interpreter, subshell execution — each with example attacks and
  how the design prevents them
- **Platform considerations**: Windows (PowerShell 5.1, PowerShell 7+, cmd.exe) vs.
  macOS/Linux (bash, sh, zsh, fish) syntax differences and how each is handled
- **Integration architecture**: `sanitize_terminal_command(command: str) -> tuple[str, str]`
  function signature, where it slots into the existing `decide()` function in security_gate.py,
  and data-flow diagram
- **Escape hatch**: administrator-managed `terminal-exceptions.json` file in the hooks
  directory (itself protected by the zone restriction), format specification, and what safety
  checks still apply to exception-listed commands
- **Test plan for SAF-005**: 40 named test cases across unit, security (protection + bypass),
  and cross-platform categories

## Files Changed

- `docs/workpackages/SAF-004/terminal-sanitization-design.md` — New file; complete design
  document for terminal command allowlist (SAF-005 implementation target)

## Tests Written

This workpackage produces a design document only — no executable code was written. The test
plan for the forthcoming implementation is specified in Section 11 of the design document.
No entries are added to `docs/test-results/test-results.csv` for this WP.

## Known Limitations

- The allowlist is necessarily conservative. Commands that feel legitimate but are not listed
  (e.g., `curl` for downloading packages) will be denied until explicitly added via the escape
  hatch or a subsequent SAF WP amendment.
- Shell parsing is intentionally shallow: the pre-scan and tokenizer deliberately avoid
  implementing a full shell grammar. This means highly convoluted obfuscation that mimics
  legitimate commands could theoretically pass the pre-scan; defence-in-depth through the path
  zone check in Stage 5 mitigates this residual risk.
- The escape hatch relies on humans creating `.github/hooks/terminal-exceptions.json`; the
  format and loading logic must be implemented carefully in SAF-005 to avoid introducing a new
  bypass vector (e.g., JSON injection into the exceptions file).

---

## Iteration 2

**Date:** 2026-03-10
**Triggered by:** Tester report — 4 bugs (BUG-005 to BUG-008) + TODO-5 from test-report.md

### Changes Made

All changes are in `docs/workpackages/SAF-004/terminal-sanitization-design.md`.

**BUG-008 (Medium) — Pattern count corrected (Section 5, Stage 3 block)**
- "Apply 15 regex patterns (Section 6)" replaced with "Apply all obfuscation pre-scan
  patterns from `_OBFUSCATION_PATTERNS` (Section 6 and Section 10 platform patterns;
  28 patterns total)". The stale "15" count was inconsistent with the 28 patterns
  (P-01–P-28) actually defined in the specification.

**BUG-005 (High) — Chain-splitting added to Stage 4 formal spec (Section 5)**
- Stage 4 block in the pipeline diagram now explicitly states: before whitespace-splitting,
  split on `;`, `&&`, and `||` to produce command segments; apply Stages 4 and 5 to EACH
  segment; if ANY segment returns deny → overall result is deny. The primary verb check and
  allowlist lookup operate on each segment independently.
- Previously this requirement only appeared in Section 9.6 as a buried "implementation
  requirement" — it is now normative in the pipeline specification.

**BUG-007 (Medium) — P-10 implementation reference updated (Section 6 code block)**
- The `_OBFUSCATION_PATTERNS` list entry for P-10 was updated from the incomplete
  `(?:powershell|pwsh)[^\n]*?-enc(?:odedcommand)?\b` to the corrected pattern from
  Section 9.4: `(?:powershell|pwsh)[^\n]*?-e(?:nc(?:odedcommand)?)?\s+[A-Za-z0-9+/=]{10,}`.
- Added inline comment: `# P-10 — extended to catch -e (abbreviation of -EncodedCommand)`.

**BUG-006 (High) — Escape hatch residual checks extended to full pre-scan (Section 12.4)**
- Replaced the partial enumeration (P-01–P-09 + P-10 listed separately) with:
  1. Full obfuscation pre-scan (P-01 to P-28) — ALL `_OBFUSCATION_PATTERNS` entries applied;
     no exception can override any pre-scan pattern.
  2. Zone check on all path arguments — unchanged.
- This closes the security gap where patterns P-11–P-28 (eval, exec, source, IEX, `$()`,
  backtick, pipe-to-interpreter, process substitution, execution-policy bypass, Invoke-Item,
  Set-Alias, New-Alias) could have been bypassed by an exception-listed command.

**TODO-5 (Medium) — Version-alias matching specified for `python3.x`/`pip3.x` (Section 7.2)**
- Added explicit version-alias matching note to Category A: verb matching uses
  `re.match(r'^python3?\.\d+$', verb)` → treated as `python`; any other scheme (python2,
  python27) → deny. The table placeholder `"python3.x"` must NOT be a literal dict key.
- Added corresponding note to Category B: `re.match(r'^pip3\.\d+$', verb)` → treated as
  `pip`; pip2/pip2.7 → deny.

### Tests Written

No executable code was changed. This remains a design-document-only WP. No new test-results
entries required.

### Files Changed

- `docs/workpackages/SAF-004/terminal-sanitization-design.md` — Five targeted edits
  addressing BUG-005, BUG-006, BUG-007, BUG-008, and TODO-5.
- `docs/workpackages/workpackages.csv` — Status updated to `Review`.
- `docs/workpackages/SAF-004/dev-log.md` — This iteration section added.
