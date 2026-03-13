# Dev Log — FIX-004: Convert shell scripts to LF line endings

## Workpackage
- **ID:** FIX-004
- **Branch:** fix/FIX-004
- **Date:** 2026-03-13
- **Assigned To:** Developer Agent

## Problem

Two tests in `tests/INS-006/test_ins006_edge_cases.py` failed:
- `TestLineEndings::test_no_crlf_line_endings` — "build_dmg.sh contains Windows CRLF line endings"
- `TestLineEndings::test_no_bare_cr` — "build_dmg.sh contains bare CR characters"

**Root cause:** `src/installer/macos/build_dmg.sh` was checked out on Windows with
`core.autocrlf=true`, which converts LF→CRLF on checkout. The `.gitattributes`
rule `*.sh text eol=lf` was added in a later commit (6014797), but existing
working-tree copies were not refreshed — leaving the file with CRLF line endings
on disk. The git blob itself was already stored with LF.

## Fix

The working-tree file `src/installer/macos/build_dmg.sh` was converted from CRLF
to LF-only using Python in binary mode:

```python
p = 'src/installer/macos/build_dmg.sh'
d = open(p, 'rb').read()
open(p, 'wb').write(d.replace(b'\r\n', b'\n').replace(b'\r', b''))
```

**Verification:**
- File on disk: 4099 bytes, 0 CR bytes, 118 LF bytes
- Git blob: already LF (no blob change needed)
- `git ls-files --eol` shows `i/lf w/lf attr/text eol=lf` — consistent

**`src/installer/linux/build_appimage.sh` was also checked:** 0 CR bytes — no fix needed.

## Files Changed

| File | Change |
|------|--------|
| `src/installer/macos/build_dmg.sh` | Working-tree CRLF → LF (git blob unchanged, already LF) |

## Tests

| Suite | Run | Result |
|-------|-----|--------|
| `tests/INS-006/` | 63 tests | 63 passed ✓ |
| `tests/INS-007/` | 85 tests | 85 passed ✓ |

Previously failing tests now pass:
- `TestLineEndings::test_no_crlf_line_endings` ✓
- `TestLineEndings::test_no_bare_cr` ✓

## Iteration 1 Verification (2026-03-13)

Re-verified by Developer Agent. Full evidence chain:

1. **Disk file bytes** — `src/installer/macos/build_dmg.sh`: 4099 bytes, 0 CR (0x0D), 118 LF.
   `src/installer/linux/build_appimage.sh`: 0 CR, 148 LF.
2. **Git index blob hash** — SHA1 computed from raw LF disk content matches the
   hash git has stored in the index for both files (`d0872aa...` / `624b55d...`).
   This proves the git objects are LF-only — not CRLF.
3. **`git ls-files --eol`** — `i/lf w/lf attr/text eol=lf` for both files.
4. **Test run** — `tests/INS-006/` 63/63 pass; `tests/INS-007/` 85/85 pass
   (148/148 total). Logged as TST-602.

Note: Earlier investigation appeared to show CRLF in git objects via `git show |
python` pipe, but this was a Windows pipe artifact where the terminal injected
CRLF into the piped output stream. The SHA1 hash comparison proved the objects
have always been LF-only.

## Recurrence Prevention

`.gitattributes` already contains `*.sh text eol=lf`. Future checkouts of
`build_dmg.sh` will receive LF line endings regardless of `core.autocrlf`
setting, because `eol=lf` overrides `core.autocrlf` on checkout.
