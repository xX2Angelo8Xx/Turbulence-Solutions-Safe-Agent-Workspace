# Test Report — SAF-004

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 2

---

## Summary

All five issues raised in Iteration 1 (BUG-005, BUG-006, BUG-007, BUG-008, TODO-5) have been
correctly addressed. The design document is now internally consistent, normatively complete,
and safe to hand to an implementer. The full test suite (96/96) passes with no regressions.

**Verdict: PASS — SAF-004 marked Done.**

---

## Verification of Iteration 1 Issues

### BUG-005 — Stage 4 chain-splitting (HIGH-SEC)
**Status: FIXED ✅**

Section 5 Stage 4 block now explicitly reads:

> Before whitespace-splitting, split the normalized command on `;`, `&&`, and `||` to produce
> a list of command segments. Apply Stages 4 and 5 to EACH segment. If ANY segment returns
> deny → the overall result is deny. The primary verb check and allowlist lookup operate on
> each segment independently.

The requirement is now normative in the pipeline specification, not buried in Section 9.6.

---

### BUG-006 — Escape hatch residual checks cover P-01 to P-28 (HIGH-SEC)
**Status: FIXED ✅**

Section 12.4 now reads:

> **Full obfuscation pre-scan (P-01 to P-28)** — ALL patterns in `_OBFUSCATION_PATTERNS` are
> applied to the exception-matched command. No exception can override any pre-scan pattern.
> This subsumes the former P-01–P-09 (interpreter-chaining) and P-10 (encoded commands)
> restrictions and extends coverage to `eval`, `exec`, `source`, IEX, `$()`, backtick
> subshell, pipe-to-interpreter, process substitution, PowerShell execution-policy bypass,
> `Invoke-Item`, `Set-Alias`, `New-Alias`, and all other patterns defined in Sections 6 and 10.

Patterns P-11 to P-28 can no longer be bypassed via an exception entry.

---

### BUG-007 — P-10 code block includes -e short flag (MEDIUM)
**Status: FIXED ✅**

Section 6 implementation reference code block P-10 now reads:

```python
re.compile(r"(?:powershell|pwsh)[^\n]*?-e(?:nc(?:odedcommand)?)?\s+[A-Za-z0-9+/=]{10,}"),  # P-10 — extended to catch -e (abbreviation of -EncodedCommand)
```

The `-e` short flag abbreviation of `-EncodedCommand` is now covered by the authoritative
implementation reference.

---

### BUG-008 — Pattern count corrected to 28 (MEDIUM)
**Status: FIXED ✅**

Section 5 Stage 3 block now states:

> Apply all obfuscation pre-scan patterns from `_OBFUSCATION_PATTERNS` (Section 6 and
> Section 10 platform patterns; 28 patterns total)

Count verified: P-01 to P-23 (Section 6) = 23 + P-24 to P-28 (Section 10) = 5 → **28 total**.

---

### TODO-5 — python3.x / pip3.x version-alias matching (MEDIUM)
**Status: FIXED ✅**

Section 7.2 Category A now includes:

> **Version-alias matching (Category A):** The implementation MUST normalize version-specific
> verb variants using `re.match(r'^python3?\.\d+$', verb)` → treated as `python`. Any other
> version scheme (e.g., `python2`, `python27`) is NOT in the allowlist → deny. The literal
> string `"python3.x"` in the table above is a documentation placeholder; the allowlist
> dictionary must NOT have a key `"python3.x"`.

Section 7.2 Category B includes the equivalent for pip:

> **Version-alias matching (Category B):** The implementation MUST normalize `pip3.<N>` verb
> variants using `re.match(r'^pip3\.\d+$', verb)` → treated as `pip`. Any other version
> scheme (e.g., `pip2`, `pip2.7`) is NOT in the allowlist → deny.

---

## Tests Executed

| Test ID | Test | Type | Result | Notes |
|---------|------|------|--------|-------|
| TST-119 | Stage 4 chain-separator coverage (re-review) | Design Review | Pass | BUG-005 fix confirmed |
| TST-120 | Escape hatch residual checks cover P-01 to P-28 (re-review) | Security | Pass | BUG-006 fix confirmed |
| TST-121 | P-10 -e short flag in Section 6 code block (re-review) | Design Review | Pass | BUG-007 fix confirmed |
| TST-122 | Pre-scan pattern count = 28 (re-review) | Design Review | Pass | BUG-008 fix confirmed |
| TST-123 | python3.x / pip3.x matching mechanism (re-review) | Design Review | Pass | TODO-5 fix confirmed |
| TST-124 | Full regression suite (96 tests) | Regression | Pass | 96/96 pass — no regressions |

---

## Additional Observations (Non-Blocking)

**Observation 1 — Section 6 code block is incomplete (23/28 patterns)**

The `_OBFUSCATION_PATTERNS` list in Section 6 contains only P-01 to P-23. Patterns P-24 to
P-28 are defined separately in Section 10. Section 5 correctly directs the implementer to
use "Section 6 and Section 10 platform patterns; 28 patterns total", so the split is not a
defect. However, an implementer who copies the Section 6 list verbatim without reading
Section 10 would produce an incomplete list. This is a documentation structure risk. It does
NOT block this WP but should be consolidated in SAF-005 (all 28 patterns in one list).

**Observation 2 — Section 9.4 prose shows the old P-10 pattern**

The opening of Section 9.4 "How the design prevents it" still cites the old P-10 pattern
`(?:powershell|pwsh)[^\n]*?-enc(?:odedcommand)?\b` before going on to identify the `-e` gap
and provide the fix. This is intentionally narrative (describing the old state then fixing
it), but could confuse an implementer skimming the section. The Section 6 code block is
authoritative and is correct. Not a blocking issue.

**Observation 3 — python regex allows `python.X` (no digit-3 required)**

The specified pattern `r'^python3?\.\d+$'` matches `python.9` (the `3?` makes the `3`
optional). The executable `python.9` does not exist in practice, so this is an extremely
low-risk edge case. If matched, the verb is normalized as `python` and all Category A
constraints still apply. Not an exploitable vector.

---

## Bugs Found

None in Iteration 2.

---

## TODOs for Developer

None — all Iteration 1 TODOs resolved.

---

## Verdict

**PASS — SAF-004 is marked Done. SAF-005 (implementation) is unblocked.**


---

## Summary

The design document is thorough, well-structured, and demonstrates genuine depth in threat
modeling. The five-stage pipeline, obfuscation pre-scan catalogue, and test plan are strong.
However, **three security issues** were found that could cause SAF-005 to produce an insecure
implementation if built purely from the current document:

1. The Stage 4 formal spec (Section 5) does not mention `&&`, `||`, `;` as command chain
   separators. A developer following the formal spec would produce a tokenizer that misses
   chained commands entirely.
2. The escape hatch residual checks (Section 12.4) only block P-01 to P-09 (interpreter
   chains) and P-10 (encoded commands). Patterns P-11 to P-28 — covering `eval`, `exec`,
   `source`, IEX, `$()`, backtick subshell, pipe-to-interpreter, process substitution, and
   PowerShell aliases — are **not** included in the residual check list. An exception-listed
   command could exploit these vectors.
3. The P-10 correction identified in Section 9.4 (extending the pattern to also catch
   PowerShell's `-e` short flag) is not reflected in the implementation reference code block
   at the end of Section 6.

Two additional medium-severity clarity issues reduce implementer confidence:

4. Section 5 states "15 regex patterns" for Stage 3 but the specification defines 28 patterns
   (P-01 to P-23 in Section 6; P-24 to P-28 in Section 10).
5. The allowlist entries for `python3.x` and `pip3.x` (Section 7.2) describe version-wildcard
   verbs without specifying whether the implementation uses regex matching or explicit
   enumeration — leaving SAF-005 to decide a security-relevant detail independently.

**Verdict: FAIL — Return to Developer with TODOs below.**

---

## Tests Executed

| Test ID | Test | Type | Result | Notes |
|---------|------|------|--------|-------|
| TST-105 | Stage 4 formal spec chain-separator coverage | Design Review | Fail | Section 5 Stage 4 spec omits `&&`, `||`, `;` splitting; only in Section 9.6 |
| TST-106 | Escape hatch residual-check coverage (Section 12.4) | Security Review | Fail | P-11 to P-28 not listed; eval/exec/source/IEX etc. bypassable via exception |
| TST-107 | Pre-scan pattern count consistency | Design Review | Fail | Section 5 says "15 patterns"; actual spec defines 28 |
| TST-108 | P-10 fix reflected in code reference block | Design Review | Fail | Section 9.4 fix not in Section 6 implementation code block |
| TST-109 | python3.x / pip3.x verb-matching mechanism specified | Design Review | Fail | Dict-key vs regex match unspecified; security-relevant ambiguity |
| TST-110 | Full regression suite (92 tests — INS-001, INS-002, SAF-001) | Regression | Pass | 92/92 pass; no regressions introduced by design-doc-only WP |

---

## Bugs Found

- **BUG-005**: Stage 4 formal spec omits `&&`/`||`/`;` command-chain-separator requirement (logged in docs/bugs/bugs.csv)
- **BUG-006**: Escape hatch residual checks (Section 12.4) don't cover pre-scan patterns P-11 to P-28 (logged in docs/bugs/bugs.csv)
- **BUG-007**: P-10 implementation reference code in Section 6 not updated with fix from Section 9.4 (logged in docs/bugs/bugs.csv)
- **BUG-008**: Pattern count discrepancy — Section 5 says "15 regex patterns" but spec defines 28 (logged in docs/bugs/bugs.csv)

---

## TODOs for Developer

### TODO-1 — [HIGH-SEC] Add `&&`, `||`, `;` splitting to Stage 4 formal specification

**Location:** Section 5, Stage 4 block.

**Problem:** The pipeline diagram and Stage 4 bullet list only describe "Split on whitespace
respecting single and double quotes." The requirement to split on `;`, `&&`, and `||` — and
to run Stage 5 on EACH resulting segment — is only stated in Section 9.6 as a buried
"Implementation requirement." An implementer reading Section 5 would correctly build a
tokenizer that cannot detect `git status; rm -rf .` as a chained attack. The test plan
validates this behavior (T-043, T-059, T-060) which would catch it, but the design spec
must be authoritative on its own.

**Required fix:** Update the Stage 4 block in Section 5 to explicitly state:

> Before whitespace-splitting, split the normalized command on `;`, `&&`, and `||` to
> produce a list of command segments. Apply Stages 4 and 5 to **each** segment. If ANY
> segment returns deny → the overall result is deny. The primary verb check and allowlist
> lookup operate on each segment independently.

Also update the Stage 4 definition to match (the text in Section 9.6 is sufficient but
it must be part of the normative pipeline spec, not a footnote in the edge-cases section).

---

### TODO-2 — [HIGH-SEC] Expand escape hatch residual checks to cover full pre-scan catalogue

**Location:** Section 12.4.

**Problem:** The residual safety checks state:
1. No interpreter-chaining flags (P-01 to P-09) — exception cannot override these
2. No encoded commands (P-10) — exception cannot override
3. Zone check on all path arguments

This means patterns P-11 to P-28 — which cover `IEX`, `Invoke-Expression`,
`Start-Process`, `& $var`, `[Convert]::FromBase64String`, pipe-to-interpreter, backtick
subshell, `$()` subshell, `eval`, `exec`, `source`, POSIX dot-source, PowerShell
execution-policy bypass, `Invoke-Item`, `Set-Alias`, `New-Alias`, and process substitution
— are **not** blocked by residual checks. An exception-listed `curl` command could be
exploited as: `curl https://api.example.com ; eval $payload` if the exception pattern is
too broad, sliding through residual checks.

**Required fix:** Replace the enumeration in Section 12.4 with:

> 1. **Full obfuscation pre-scan (P-01 to P-28)** — ALL patterns in `_OBFUSCATION_PATTERNS`
>    are applied to the exception-matched command. No exception can override any pre-scan pattern.
> 2. **Zone check on all path arguments** — exception cannot access restricted zones.

This collapses the two original items into one (the pre-scan already subsumes P-01 and P-10)
and removes the security gap created by the partial enumeration.

---

### TODO-3 — [MEDIUM] Update Section 6 implementation reference code with P-10 fix

**Location:** Section 6 — "Full Pre-scan Pattern List (implementation reference)" code block.

**Problem:** Section 9.4 correctly identifies that P-10 as written does not match the
`-e` short flag (`powershell -e BASE64...`) and provides a corrected pattern:

```python
re.compile(r"(?:powershell|pwsh)[^\n]*?-e(?:nc(?:odedcommand)?)?\s+[A-Za-z0-9+/=]{10,}")
```

However, the implementation reference code block at end of Section 6 still shows the
original incomplete version. An implementer copying from Section 6 as the authoritative
reference would implement the bypass-vulnerable version.

**Required fix:** Replace the P-10 entry in the Section 6 code block with the corrected
pattern from Section 9.4. Add a comment noting the fix (e.g., `# P-10 — extended to catch
-e (abbreviation of -EncodedCommand)`).

---

### TODO-4 — [MEDIUM] Fix pattern count in Section 5

**Location:** Section 5, Stage 3 block — text reads "Apply 15 regex patterns (Section 6)."

**Problem:** The specification defines 28 patterns: P-01 to P-23 in Section 6, and P-24 to
P-28 in Section 10.3. The "15" count is stale and conflicts with the authoritative list.

**Required fix:** Update the sentence to read "Apply all obfuscation pre-scan patterns from
`_OBFUSCATION_PATTERNS` (Section 6 and Section 10 platform patterns; 28 patterns total)."
Alternatively, consolidate all 28 patterns into Section 6 and remove the partial definitions
from Section 10 to avoid split specifications.

---

### TODO-5 — [MEDIUM] Specify verb matching mechanism for `python3.x` / `pip3.x`

**Location:** Section 7.2, Category A and Category B allowlist tables.

**Problem:** The tables list `python3.x` (meaning any version-specific alias like `python3.11`,
`python3.12`) and `pip3.x`, but a Python dictionary keyed by the literal string `"python3.x"`
would never match `python3.11`. The implementation must either:
- Use prefix/regex matching on the primary verb before lookup, OR
- Enumerate concrete known versions as separate entries

This is a security-relevant choice: an overly broad regex (`python\d+(\.\d+)?`) would allow
`python2` or `python27`, which may have different flag semantics.

**Required fix:** Add an explicit note to Category A and Category B:

> **Version-alias matching:** The implementation must normalize version-specific verb variants
> using: `re.match(r'^python3?\.\d+$', verb)` → treated as `python`. Any other version scheme
> (e.g., `python2`, `python27`) is NOT in the allowlist → deny.

Provide corresponding normalization rules for `pip3.x`.

---

### TODO-6 — [LOW] Address Unicode normalization

**Location:** Section 5, Stage 2.

**Problem:** The design has no Unicode normalization step. An attacker could use Unicode
lookalike characters (e.g., Unicode EN DASH U+2013 in place of ASCII HYPHEN U+002D) to
avoid matching pre-scan patterns. While this is a sophisticated attack, it is a known bypass
class.

**Required fix:** Add to Stage 2: "Normalize Unicode: apply NFKC normalization
(`unicodedata.normalize('NFKC', command)`) to collapse compatibility equivalents and
lookalike characters before any pattern matching."

---

### TODO-7 — [INFO] Update WP status to `Review` in workpackages.csv

**Problem:** workpackages.csv shows SAF-004 as `Open`. The Developer must update the status
to `Review` before handoff per agent-workflow Step 7.

---

## Verdict

**FAIL — Return SAF-004 to Developer (In Progress). Address TODOs 1–5 as minimum before re-review.**

TODOs 1 and 2 are security blocking — they define behaviors that would lead SAF-005 to
produce an insecure implementation. TODOs 3, 4, and 5 are medium-severity clarity issues
that reduce the document's ability to serve as a standalone implementation spec. TODO 6 is
a low-severity hardening recommendation. TODO 7 is a process correction.

The document's overall quality is high. Once these gaps are addressed, it should pass review.
