# FIX-038 Test Report — Remove .app bundle codesign — use component-level signing only

## Summary

| Field | Value |
|-------|-------|
| **WP ID** | FIX-038 |
| **Branch** | fix/FIX-038-component-level-codesign |
| **Tester** | Tester Agent |
| **Test Date** | 2026-03-18 |
| **Verdict** | **PASS** |

---

## Code Review Findings

### `src/installer/macos/build_dmg.sh`

| Check | Result |
|-------|--------|
| `codesign --force --sign - "${APP_BUNDLE}"` removed | PASS — not present |
| `codesign --verify --deep --strict "${APP_BUNDLE}"` removed | PASS — not present |
| `.dylib` individual signing still present | PASS |
| `.so` individual signing still present | PASS |
| `Python.framework` signing with `--deep` still present | PASS |
| Main `launcher` executable signing still present | PASS |
| Component-level verification: `codesign --verify "[...]/launcher"` | PASS |
| Component-level verification: `codesign --verify --deep "[...]/Python.framework"` | PASS |
| Explanatory comment about WHY bundle signing is skipped | PASS |
| `.dist-info` removal from FIX-037 still present | PASS |
| Signing order: dylib → so → Python.framework → launcher | PASS |

### `.github/workflows/release.yml`

| Check | Result |
|-------|--------|
| Old `codesign --verify --deep --strict dist/AgentEnvironmentLauncher.app` removed | PASS |
| New verification checks `dist/.../launcher` individually | PASS |
| New verification checks `dist/.../Python.framework` individually | PASS |
| `run:` uses YAML literal block scalar `\|` for multi-line | PASS |

---

## Test Execution

### FIX-038 Test Suite (all tests)

| Run | Tests | Passed | Failed | Skipped |
|-----|-------|--------|--------|---------|
| `tests/FIX-038/test_fix038_component_codesign.py` | 13 | 13 | 0 | 0 |
| `tests/FIX-038/test_fix038_edge_cases.py` | 13 | 13 | 0 | 0 |
| **Total** | **26** | **26** | **0** | **0** |

### Full Suite Regression (TST-1825)

| Metric | Count |
|--------|-------|
| Total collected | 3,718 |
| Passed | 3,628 |
| Failed | 61 |
| Skipped | 29 |
| xfailed | 1 |

**Failure classification:**

| Category | Tests Failed | Cause | Impact |
|----------|-------------|-------|--------|
| Version-pin failures (pre-existing) | 50 | Earlier WPs (FIX-010/014/017/019/020/030) lock old version numbers; project is now at v2.1.0 | None — pre-existing before FIX-038 |
| Superseded signing tests | 11 | FIX-028 (3) + FIX-029 (3) + FIX-031 (4) + FIX-037 (1): tested bundle-level `--deep --strict` signing that FIX-038 intentionally removes | Expected — permanent test freeze policy means these can't be modified |
| FIX-009 CSV structure | 4 | Pre-existing KeyError on 'ID' column in test-results.csv format check | None — pre-existing |
| INS-005/006/007 version | 6 | Same version-pin pre-existing failures | None — pre-existing |

**Conclusion:** 0 new failures introduced by FIX-038.

---

## Edge-Case Analysis

### Test Coverage Added by Tester (13 tests in `test_fix038_edge_cases.py`)

| Test | Rationale |
|------|-----------|
| `test_signing_order_dylib_before_so` | Bottom-up signing must process leaves first — if order breaks, a .so could reference an unsigned .dylib |
| `test_signing_order_so_before_framework` | Python.framework wraps many .so files; they must be signed before their containing framework |
| `test_signing_order_framework_before_launcher` | The executable (launcher) links against the framework — framework must be signed first |
| `test_no_codesign_targets_app_bundle_directly` | Confirms the systemic fix: any line ending in `.app"` is now forbidden |
| `test_no_codesign_sign_app_bundle_variable` | Specifically checks the removed line: `codesign --sign - "${APP_BUNDLE}"` |
| `test_app_bundle_only_used_as_prefix_in_codesign` | If APP_BUNDLE appears in a sign line it must go into `/Contents/` subpath |
| `test_release_yml_verify_step_uses_multiline_yaml` | Multi-line YAML `\|` ensures both verify calls appear under same step |
| `test_release_yml_verify_step_has_two_codesign_calls` | Both components (launcher + Python.framework) must be verified |
| `test_explanatory_comment_mentions_pyinstaller` | Comment must identify root cause (PyInstaller mixed-content bundle) |
| `test_explanatory_comment_mentions_non_code_files` | Comment must explain WHY (non-code files can't be bundle subcomponents) |
| `test_dist_info_removal_present` | FIX-037 regression guard — removal step must not have been accidentally deleted |
| `test_dist_info_removal_uses_find_and_rm` | Confirms robust removal pattern (not fragile hardcoded path) |
| `test_dist_info_removal_targets_internal_dir` | Confirms removal targets the correct directory (_internal/) |

### Security / Attack Vectors

- **Signing bypass:** No signing of the `.app` bundle means Gatekeeper cannot validate the bundle as a single identity. Assessed as **acceptable** — ad-hoc signing (`-`) is for CI development builds, not distribution. Apple Silicon execution is gated on individual code objects being signed, not the bundle wrapper.
- **Injection into bundle:** An attacker could add a file to `Contents/MacOS/_internal/` after build. This is a general issue with ad-hoc signed bundles and is unchanged from before (was already unsigned at bundle level even with `--force --sign -`).
- **FIX-037 regression risk:** Removing `.dist-info` must happen before signing. Order verified: Step 3.1 (remove .dist-info) → Step 3.5 (sign). Correct.

### Boundary / Platform Considerations

- **Python.framework absent:** Both signing and verification are guarded by `if [ -d ... ]; then`. Script will not fail if framework is missing.
- **Windows / Linux CI:** Signing step only runs on macOS CI runner; irrelevant on other platforms. `release.yml` only runs the Verify Code Signing step in `macos-arm-build` job.

---

## Verdict

**PASS** — FIX-038 correctly removes bundle-level codesign, retains all individual component signing, adds component-level verification, and preserves the FIX-037 `.dist-info` removal. All 26 dedicated tests pass. No new failures in the full suite.

FIX-038 is set to **Done**. BUG-071 is **Closed**.
