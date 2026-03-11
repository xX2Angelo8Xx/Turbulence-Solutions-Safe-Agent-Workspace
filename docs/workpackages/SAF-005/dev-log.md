# Dev Log — SAF-005

**Developer:** Developer Agent
**Date started:** 2026-03-11
**Iteration:** 1

## Objective

Implement the terminal allowlist defined in SAF-004 design document. Replace the existing
string-literal denylist pattern matching for terminal tools in `security_gate.py` with the
full 5-stage detection pipeline specified in `terminal-sanitization-design.md`. The goal is
to fully eliminate the terminal string fragmentation attack vector.

## Implementation Summary

The SAF-004 design document specified a complete 5-stage pipeline:

1. **Stage 1** — Extract the `command` field from `tool_input`. Deny if absent or non-string.
2. **Stage 2** — Normalize: strip/collapse whitespace. Do NOT lowercase yet.
3. **Stage 3** — Obfuscation pre-scan: apply all 28 `_OBFUSCATION_PATTERNS` against the
   lowercased command. Any match → immediate deny.
4. **Stage 4** — Tokenize: split on `;`, `&&`, `||` into segments; for each segment split on
   whitespace respecting quotes; extract primary verb; deny if verb starts with `$` or contains
   `${`/`$(`.
5. **Stage 5** — Allowlist lookup: check primary verb against `_COMMAND_ALLOWLIST`; validate
   arguments per per-command rules; check path args via `get_zone()`; deny if path args
   contain `$` (variable reference with unknown runtime value).

After Stage 5, if the verb is not allowlisted, check the escape hatch
(`terminal-exceptions.json`) before returning deny. Even exception-listed commands still go
through the full obfuscation pre-scan and zone check.

Terminal commands **never** return `allow` — the best outcome is `ask`.

Key design decisions:
- `CommandRule` dataclass stores denied_flags, allowed_subcommands, path_args_restricted,
  allow_arbitrary_paths, and notes per allowlist entry.
- Version aliases (`python3.12`, `pip3.9`, etc.) are normalized to `python` / `pip` via regex
  before allowlist lookup.
- `pip install` with `-m` flag delegation is handled: `python -m pytest` checks module name.
- Chain splitting on `;`, `&&`, `||` applied before tokenization so chained malicious
  commands are each evaluated independently.
- `$` in any path-like argument → deny (fragmentation prevention, Section 9.1).
- The escape hatch file is only consulted when the allowlist fails; obfuscation pre-scan
  remains non-overridable even for exception-listed patterns.

## Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — Added `dataclasses` and
  `shlex` imports. Added `_OBFUSCATION_PATTERNS` (28 patterns), `_EXPLICIT_DENY_PATTERNS`,
  `CommandRule` dataclass, `_COMMAND_ALLOWLIST` dictionary (Categories A–J), and
  `_PYTHON_ALLOWED_MODULES`, `_GIT_DENIED_COMBOS` constants. Added helper functions
  `_is_path_like()`, `_normalize_terminal_command()`, `_split_segments()`,
  `_tokenize_segment()`, `_extract_verb()`, `_check_path_arg()`, `_validate_args()`,
  `load_terminal_exceptions()`, `sanitize_terminal_command()`. Modified `decide()` terminal
  tool branch to call `sanitize_terminal_command()`. Added fallback to look for `command`
  at data root level when not in `tool_input` (preserves backward compat with SAF-001 tests).

## Tests Written

- `tests/SAF-005/test_saf005_terminal_sanitization.py` — 80 tests covering all T-001–T-080
  from the design doc test plan:
  - T-001 to T-029: unit tests (extraction, normalization, tokenization, allowlist)
  - T-030 to T-045: security protection tests
  - T-046 to T-061: security bypass-attempt tests
  - T-062 to T-070: cross-platform tests
  - T-071 to T-076: escape hatch / exception tests
  - T-077 to T-080: regression tests

## Test Results

- **SAF-005 tests:** 80/80 pass
- **Full regression suite:** 257/260 pass
- **Pre-existing failures (not caused by SAF-005):** 3 SAF-002 security-bug tests added by
  the Tester during SAF-002 review (`test_security_tab_before_deny_dir`,
  `test_security_newline_before_deny_dir`, `test_security_unc_path_project_outside_workspace_not_allow`).
  These are bugs in `zone_classifier.py` to be fixed in a SAF-002 iteration.

## Known Limitations

- The `_tokenize_segment()` function uses Python's `shlex` module for quote-aware splitting.
  `shlex` in POSIX mode does not handle all PowerShell quoting nuances; however, Stage 3
  catches the dangerous PowerShell patterns before tokenization.
- The `load_terminal_exceptions()` function is called on each invocation of
  `sanitize_terminal_command()`. This is consistent with Section 12.5 of the design (pick up
  changes without VS Code restart) but adds a small I/O cost per terminal invocation.
- `node` as a verb is on the allowlist (for `.js` file execution), but inline `node -e` is
  denied by P-05 in Stage 3.
- `ls -R` (capital R) is denied because tokens are lowercased before validation, matching
  the denied flag `-r`.

---

## Iteration 2 — 2026-03-11

### Tester Feedback Addressed

- **BUG-013 (BLOCKING)** — Shell redirect to restricted zone returns `ask`: Added step 6 to
  `_validate_args` that scans all arg tokens for `>` and `>>` redirect operators and
  zone-checks the immediately following token via `_check_path_arg`, regardless of the
  primary verb's `path_args_restricted` or `allow_arbitrary_paths` setting. Commands like
  `echo evil > .github/security_gate.py` now correctly return `deny`.

- **BUG-014 (BLOCKING)** — `npm --prefix` path to restricted zone not zone-checked: Resolved
  as a consequence of the BUG-015 fix. Since `npm` has `allow_arbitrary_paths=False`, the
  updated step 5 zone-checks all path-like args including `.github/node_modules` which
  follows `--prefix`.

- **BUG-015 (MEDIUM)** — `allow_arbitrary_paths` field never enforced: Changed step 5
  condition in `_validate_args` from `if rule.path_args_restricted:` to
  `if rule.path_args_restricted or not rule.allow_arbitrary_paths:`. Commands with
  `allow_arbitrary_paths=False` (npm, yarn, pnpm, hatch, build, twine, code) now have
  their path-like arguments zone-checked.

- **Advisory — `_GIT_DENIED_COMBOS` dead code**: Removed the inner `if denied_flag:` guard
  in the git combo check. The entry `("filter-branch", "")` now correctly returns `False`
  (deny) when subcmd matches and denied_flag is empty-string (meaning deny any usage of that
  subcommand regardless of flags). Previously this path was unreachable.

### Additional Changes

- Restored `zone_classifier.py` to `Default-Project/.github/hooks/scripts/` from the
  SAF-002 branch (it was a missing dependency not committed to the SAF-005 branch).

### Tests Run

- **SAF-005 developer tests (T-001 to T-080):** 80/80 pass
- **SAF-005 tester edge-case tests (ET-001 to ET-026):** 26/26 pass (was 21/26)
- **Full SAF/INS regression (excluding pre-existing GUI-001 and SAF-002 failures):** 232/232 pass

---

## Iteration 3 — 2026-03-11

### Tester Feedback Addressed

- **BUG-016 (BLOCKING)** — No-space and fd-prefixed shell redirect variants bypass zone
  check in `_validate_args` Step 6 (ET-027 to ET-032). Two bypass forms were discovered:

  1. **No-space redirect** — `echo evil>.github/file`: shlex produces a single token
     `evil>.github/file`; the old `tok in _REDIRECT_TOKENS` check requires an exact match
     of `>` or `>>` and misses the embedded `>`.

  2. **fd-prefixed redirect** — `echo evil 1>.github/file`: shlex produces token
     `1>.github/file`; `1>` ≠ `>` so the old frozenset membership test fails.

  **Fix applied** — Replaced the `_REDIRECT_TOKENS` frozenset and membership test in Step 6
  with two regex-based checks:

  - `_REDIRECT_OP_RE = re.compile(r'^[0-9]*>>?$')` — matches standalone redirect operators
    (plain `>`, `>>`, and fd-prefixed `1>`, `2>`, `1>>`, `2>>` etc.). When a token matches,
    the next token is zone-checked as the redirect destination (same behaviour as before,
    now extended to fd-prefixed operators).

  - `_EMBEDDED_REDIRECT_RE = re.compile(r'>>?(.+)$')` — applied to every token that does
    NOT match `_REDIRECT_OP_RE`. If the token itself contains `>` or `>>` followed by a
    non-empty suffix (e.g. `evil>.github/file` or `1>.github/file`), the suffix is
    extracted and zone-checked as the redirect destination.

  Both fixes are applied together in the same loop so all three redirect forms are handled:
  a) standalone `>` / `>>`, b) standalone fd-prefixed `1>` / `2>`, c) embedded.

### Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py` — Step 6 of `_validate_args`
  updated: removed `_REDIRECT_TOKENS` frozenset; added `_REDIRECT_OP_RE` and
  `_EMBEDDED_REDIRECT_RE` compiled patterns; expanded loop to handle both standalone
  fd-prefixed operators and embedded redirects within a single token.

### Tests Run

- **SAF-005 full suite (112 tests):** 112/112 pass
  - T-001 to T-080 (developer tests): 80 pass
  - ET-001 to ET-026 (Tester Iteration 1 & 2 edge-cases): 26 pass
  - ET-027 to ET-032 (Tester Iteration 3 BUG-016 edge-cases): 6 pass (all previously failing)
