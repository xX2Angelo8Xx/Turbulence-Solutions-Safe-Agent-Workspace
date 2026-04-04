# FIX-097 Dev Log — Make --rc Flag Meaningful

**WP ID:** FIX-097  
**Branch:** FIX-097/remove-rc-flag  
**Assigned To:** Developer Agent  
**Date:** 2026-04-04  

---

## ADR References

- **ADR-001 (Draft GitHub Releases):** Active. Confirms that all releases are created as drafts by default. The `--rc` flag was cosmetic — it only printed a reminder banner but did not change draft behaviour. This WP removes the flag, making the draft nature of all releases explicit in documentation.

---

## Problem Statement

`scripts/release.py` had an `--rc` argument that was purely cosmetic: it printed a longer reminder banner but did not change the version tag, the commit message, or the draft/publish workflow in any way. This contradicts the principle that CLI flags should be meaningful. The `orchestrator.agent.md` also documented this flag as "cosmetic", and `tests/MNT-013` verified that documentation.

Since ADR-001 already mandates that **all** releases are drafts, there is no need for an opt-in RC flag. The recommended fix (option b from the WP) is to remove the flag entirely and update all references.

---

## Implementation

**Option chosen:** (b) Remove the `--rc` flag. All releases are already draft by default per ADR-001.

### Files changed

| File | Change |
|------|--------|
| `scripts/release.py` | Removed `--rc` argparse argument and `if args.rc:` conditional block. Updated module docstring and NOTE output to clarify all releases are draft. |
| `.github/agents/orchestrator.agent.md` | Removed `--rc` from example command and removed the cosmetic-flag note. |
| `tests/MNT-013/test_mnt013_human_approval_gate.py` | Updated `test_rc_flag_clarified_as_cosmetic` → `test_all_releases_are_draft_documented` to verify the new documentation. |
| `tests/FIX-097/test_fix097_rc_flag_removed.py` | New regression tests verifying `--rc` is absent from release.py. |

---

## Tests Written

- `tests/FIX-097/test_fix097_rc_flag_removed.py` — 4 tests:
  1. `test_rc_flag_not_in_argparse` — parse `--rc` should raise SystemExit (unrecognised argument)
  2. `test_args_rc_not_referenced_in_source` — source code does not reference `args.rc`
  3. `test_help_text_mentions_draft` — `--help` output mentions "draft"
  4. `test_dry_run_still_works` — `--dry-run` flag still works as before

---

## Known Limitations

None. The change is purely cosmetic removal — no functional behaviour changes.
