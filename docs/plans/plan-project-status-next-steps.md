# Project Status & Next Steps Plan — Agent Environment Launcher

**Created:** 2026-03-20
**Version:** 3.0.3

---

## Current Project Status (v3.0.3, March 20 2026)

### Overall Health
- **Version:** 3.0.3 (released 2026-03-20)
- **Workpackages:** 103/117 done (88%), 4 in progress, 10 open
- **Bugs:** 76/87 closed (87%), 11 open
- **Tests:** ~1,887 test results, ~98% pass rate (with some stale/duplicate issues)

### Platform Status Comparison

| Dimension | Windows | macOS (arm64) | Linux |
|-----------|---------|---------------|-------|
| **Build** | ✅ CI passing | ✅ CI passing | ✅ CI passing |
| **Installer** | ✅ Inno Setup .exe | ✅ DMG (build_dmg.sh) | ✅ AppImage |
| **Code Signing** | Ad-hoc (sufficient) | Ad-hoc only (INSUFFICIENT) | None needed |
| **Real User Testing** | ✅ Developer (Windows PC) | ❌ BROKEN — crash on launch | ❌ No real user testing |
| **Bundled Python** | ✅ python-embed (36MB) | Uses PyInstaller framework | Uses PyInstaller framework |
| **Known Blockers** | None | **CRITICAL: App "damaged" error** | Unknown (untested by users) |

### Critical Issue: macOS Launch Failure (v3.0.3)

**Symptom:** "AgentEnvironmentLauncher ist beschädigt und kann nicht geöffnet werden" on macOS 14.3, M3 MacBook Air. The DMG was downloaded via Safari (quarantine flag applied).

**Root Cause Analysis:**
The project went through 6 fix iterations (FIX-028→FIX-039) to fix code signing, evolving from `--deep` bundle signing to bottom-up component-only signing. However, the fundamental problem remains:

1. **Ad-hoc signing ≠ trusted signing.** macOS Gatekeeper rejects ad-hoc signed apps downloaded from the internet (quarantine flag set by Safari/Chrome).
2. **No notarization.** Apple requires apps distributed outside the App Store to be notarized (stapled ticket proving Apple scanned the binary). Without it, downloaded apps are flagged as "damaged."
3. **No Developer ID certificate.** Proper signing requires an Apple Developer account ($99/year).

**Why CI passes but real users fail:** CI builds run `codesign --verify` which validates the signature *structure*, but doesn't test Gatekeeper enforcement. A locally-built or CI-verified app can have a structurally valid ad-hoc signature that Gatekeeper still rejects when the quarantine attribute is present.

### Open Work Items
- **FIX-051–054:** 4 in-progress WPs fixing stale test regressions
- **FIX-059–060:** Planned legacy validation error cleanup (45 artifacts)
- **BUG-078, 080, 085:** High-severity test infrastructure bugs
- **Recurring issues:** TST-ID duplicates (3rd occurrence), stale branch cleanup, test coverage gaps

---

## Plan: Next Steps for Development

### Phase 1: Fix macOS Launch (CRITICAL — Blocks real-world usage) ✅ COMPLETE

Since this is a company-internal project with one macOS user, the developer will personally assist with installation. Focus on making the signing as robust as possible; final verification happens when assisting the macOS user directly.

**1a. Create macOS entitlements file:**
- New file: `src/installer/macos/entitlements.plist`
- Entitlements: `com.apple.security.cs.allow-unsigned-executable-memory`, `com.apple.security.cs.disable-library-validation`
- These allow the embedded Python.framework to execute properly on Apple Silicon

**1b. Fix PyInstaller codesign identity:**
- Set `codesign_identity='-'` in `launcher.spec` (explicit ad-hoc signing vs `None` which may skip signing)
- This ensures PyInstaller produces a properly ad-hoc signed binary

**1c. Improve build_dmg.sh signing:**
- Pass entitlements file during component signing (`--entitlements`)
- Sign the main launcher executable inside the `.app` bundle (with entitlements)
- Sign the entire `.app` bundle at the end (with `--deep` removed, using entitlements)
- Add `--options runtime` for hardened runtime (required for notarization readiness)

**1d. Add CI quarantine simulation test:**
- In `.github/workflows/release.yml`, add a step after code signing that:
  - Sets quarantine attribute on the `.app`
  - Attempts to verify with `spctl --assess`
  - Documents expected behavior (ad-hoc will fail spctl but pass codesign)

**1e. macOS installation guide:**
- Create `docs/macos-installation-guide.md` with clear instructions for:
  - Removing quarantine: `xattr -cr /path/to/AgentEnvironmentLauncher.app`
  - Right-click → Open (bypasses Gatekeeper first-launch)
  - System Settings → Privacy & Security → "Open Anyway"

**Files modified:**
- `src/installer/macos/entitlements.plist` (new)
- `launcher.spec` (modify codesign_identity)
- `src/installer/macos/build_dmg.sh` (improve signing with entitlements)
- `.github/workflows/release.yml` (add quarantine test step)
- `docs/macos-installation-guide.md` (new)

---

### Phase 2: Stabilize Test Infrastructure (HIGH — Blocks confidence) ✅ COMPLETE

Complete the in-progress FIX-051–054 to resolve stale test regressions:
1. FIX-051: Fix 6 SAF-034 tests broken by FIX-048
2. FIX-052: Fix 6 FIX-047 tests with hardcoded version
3. FIX-053: Fix INS-011 tests killed by `os._exit()`
4. FIX-054: Fix 12 FIX-048 tests after cmd.exe wrapper removal

Then execute the legacy cleanup plan (FIX-059 + FIX-060):
5. FIX-059: Fix validator case-sensitivity + normalize CSV status values
6. FIX-060: Create missing test folders, dev-logs, test-reports (45 artifacts)

---

### Phase 3: Resolve Recurring Process Issues (MEDIUM) ✅ COMPLETE

Address the enforcement gaps identified in the 2026-03-20 workspace review:
1. **TST-ID uniqueness check** — Already enforced by `_check_duplicate_ids()` in `validate_workspace.py` (runs in pre-commit hook)
2. **Branch cleanup** — Already handled by `finalize_wp.py` Steps 5 and 10 (delete branch + stale branch check)
3. **Block WP finalization without tests** — Added Step 1b in `finalize_wp.py` requiring `tests/<WP-ID>/` to exist with test files
4. **Stale documentation references** — `maintenance-protocol.md` Check 9 already updated to `templates/coding/`

---

### Phase 4: Linux User Validation (LOW — No known issues)

- Recruit a Linux tester or set up a VM/container test environment
- Validate AppImage launches on Ubuntu 22.04+ and Fedora 38+
- Test the full workflow: download → launch → create project → open VS Code

---

### Phase 5: Feature Development (FUTURE — After stability)

Once all platforms are stable and tests are clean:
- Creative/Marketing template (templates/creative/) — listed in project scope but not yet built
- Enhanced auto-update UX — download progress, rollback on failure
- Broader template ecosystem — user-contributed templates

---

## Decisions & Assumptions
- macOS: Developer will personally assist the single macOS user with installation; no Apple Developer account required now
- Linux: Assumed working based on CI; real validation deferred until a tester is available
- FIX-059/060 plan already exists and is well-designed; no redesign needed
- Phase 3 process improvements should be tracked as new workpackages

## Verification
1. **macOS:** Developer assists user with `xattr -cr` workaround on v3.0.3 → confirm launch works
2. **Tests:** Full `pytest` suite passes with 0 failures after Phase 2
3. **Validator:** `python scripts/validate_workspace.py` returns 0 errors after Phase 2
4. **Linux:** Manual launch test on at least one real Linux system (Phase 4)
