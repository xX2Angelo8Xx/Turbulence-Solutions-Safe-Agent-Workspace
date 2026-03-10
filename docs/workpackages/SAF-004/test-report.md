# Test Report — SAF-004

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 1

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
