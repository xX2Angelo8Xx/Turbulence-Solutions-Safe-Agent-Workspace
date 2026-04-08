# Test Report — SAF-080

**Tester:** Tester Agent
**Date:** 2026-04-08
**Iteration:** 1

## Summary

SAF-080 fixes a real security bypass: `Remove-Item .github,` (and similar bare
deny-zone names with trailing commas) was previously allowed because `shlex`
tokenises the PowerShell array-operator comma as part of the token, and the
trailing comma caused two failure modes — (1) `_is_path_like()` returning False
for bare names, skipping zone checks entirely, and (2) `_try_project_fallback()`'s
deny-zone guard missing the entry due to string inequality (`.github,` ≠ `.github`).

The fix — `stripped = stripped.rstrip(",")` immediately after
`stripped = tok.strip("\"'")` in `_validate_args()` step 5 — is minimal,
surgical, and correctly targeted. Both template copies (`agent-workbench` and
`clean-workspace`) are byte-identical and hashes were regenerated.

All 22 tests pass (16 developer + 6 tester edge cases). Snapshot tests pass.
No regressions in any adjacent SAF test suite.

**Verdict: PASS**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2788: SAF-080 developer suite (16 tests) | Security | Pass | Logged by Developer via `run_tests.py` |
| TST-2789: SAF-080 tester suite (22 tests) | Security | Pass | Logged by Tester via `run_tests.py`; includes 6 edge-case tests added by Tester |
| Snapshot suite (12 tests) | Security | Pass | `tests/snapshots/security_gate/` — required because `security_gate.py` was modified |
| SAF-035 regression (175 tests) | Security | Pass | Adjacent test suite for denial counter — no regressions |
| SAF-001 suite | Security | Pass | Core security gate — no regressions |
| SAF-002 suite | Security | Pass | Zone classifier — no regressions |

### Tester Edge Cases Added (`tests/SAF-080/`)

| Test | Purpose | Result |
|------|---------|--------|
| `test_remove_item_multiple_trailing_commas_github_denied` | `.github,,,` → 3 trailing commas, still denied | PASS |
| `test_remove_item_multiple_trailing_commas_vscode_denied` | `.vscode,,` → 2 trailing commas, still denied | PASS |
| `test_remove_item_github_mixed_case_with_trailing_comma_denied` | `.GitHub,` → case-insensitive deny guard | PASS |
| `test_remove_item_quoted_path_with_trailing_comma_allowed` | `'project/file.py',` → quote-strip then comma-strip → allowed | PASS |
| `test_remove_item_quoted_github_with_trailing_comma_denied` | `'.github',` → quote-strip then comma-strip → denied | PASS |
| `test_remove_item_comma_only_token_no_crash` | `Remove-Item , project/file.py` → lone comma becomes empty string, no crash | PASS |

---

## Attack Vectors Assessed

| Vector | Analysis | Status |
|--------|----------|--------|
| Multiple trailing commas (`.github,,,`) | `rstrip(',')` removes ALL trailing commas — correctly blocked | Safe |
| Case variation (`.GitHub,`) | `_try_project_fallback` uses `p.lower()` — correctly blocked | Safe |
| URL injection via comma (e.g. `Remove-Item https://evil.com,`) | Already caught by SAF-047 URL regex in `_try_project_fallback` | Safe |
| Lone comma token becoming empty string after `rstrip` | Empty string is not path-like → loop skips it harmlessly | Safe |
| Quoted+comma (`'.github',`) | Quote-strip → `".github,"` → comma-strip → `".github"` → blocked | Safe |
| Middle comma in deny-zone path (`.github/file,name.py`) | `rstrip` is trailing-only; middle comma preserved, deny zone still caught | Safe |
| `NoAgentZone` bare name without path separator | Pre-existing limitation acknowledged in dev-log; out of scope for SAF-080 | Known gap, pre-existing |
| Template parity | SHA-256 of both `security_gate.py` files match: `8ECDC897…` | Verified |
| Snapshot regression | All 12 golden-file snapshots pass unchanged | Safe |

---

## Bugs Found

None.

---

## TODOs for Developer

None — no action required.

---

## Verdict

**PASS** — mark WP as `Done`.

The fix is correct, minimal, and verified. No new regressions introduced.
Both template instances are in sync. All pre-checklist items satisfied.
