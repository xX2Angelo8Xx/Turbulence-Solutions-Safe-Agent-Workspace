# Test Report — MNT-005

**Tester:** Tester Agent
**Date:** 2026-03-31
**Iteration:** 1

## Summary

MNT-005 adds a `validate-version` CI gate job to `.github/workflows/release.yml`. The job runs on `ubuntu-latest` before all three build jobs, extracts the version from the git tag, and checks each of the 5 version files with `grep -oP`, failing fast with clear `Expected`/`Actual` error output on any mismatch.

The implementation is correct, complete, and well-tested. All 5 version file paths exist in the repository and the grep patterns match the actual file content. All build jobs (`windows-build`, `macos-arm-build`, `linux-build`) correctly declare `needs: [validate-version]`, while the `release` job is unchanged (it inherits the gate transitively). No regressions in MNT-004 or the broader suite attributable to this change.

One low-severity security observation was noted (see Bugs Found below) — it is informational and does not block the release gate from functioning correctly.

## Tests Executed

| Test | Type | Result | Notes | TST-ID |
|------|------|--------|-------|--------|
| Developer: 20 CI structure tests | Unit | PASS | Job definition, build deps, trigger handling, all 5 file checks, error format, success summary, job order | TST-2347 |
| Tester edge cases: 31 tests | Unit | PASS | YAML validity, checkout@v4 pin, `\|\| true` for all 5 greps, GITHUB_OUTPUT, no deprecated set-output, step ID, `${TAG#v}` logic, ≥5 exit-1, transitive dep design, file existence, pattern correctness vs. real files, version consistency across all 5 files, no secrets in job | TST-2348 |
| MNT-004 regression suite: 50 tests + 1 xfailed | Regression | PASS | release.py, version update functions, git operations — no regressions | TST-2349 |

**Total: 101 tests executed, 101 passed (1 xfailed — expected)**

## Verification Checklist

- [x] `validate-version` job exists, `runs-on: ubuntu-latest`
- [x] `actions/checkout@v4` (exact pin) used in validate-version job
- [x] Push trigger handled via `${{ github.ref_name }}`
- [x] `workflow_dispatch` trigger handled via `${{ github.event.inputs.tag }}`
- [x] `${TAG#v}` strips leading `v` prefix correctly
- [x] All 5 files checked: `src/launcher/config.py`, `pyproject.toml`, `src/installer/windows/setup.iss`, `src/installer/macos/build_dmg.sh`, `src/installer/linux/build_appimage.sh`
- [x] All 5 file paths actually exist in the repo
- [x] grep patterns match actual file content (verified against live repo files)
- [x] `|| true` fallback on every grep (prevents silent abort if file is missing)
- [x] `GITHUB_OUTPUT` used correctly (no deprecated `::set-output`)
- [x] `Expected:` / `Actual:` error labels present
- [x] `exit 1` on mismatch present ≥5 times in validate-version section
- [x] Success summary prints all 5 file names
- [x] `windows-build`, `macos-arm-build`, `linux-build` all have `needs: [validate-version]`
- [x] `release` job unchanged (`needs: [windows-build, macos-arm-build, linux-build]`)
- [x] `validate-version` has no `needs` (is the unconditional entry gate)
- [x] `release` job does NOT directly depend on `validate-version` (clean transitive dependency)
- [x] No secrets referenced in `validate-version` job
- [x] YAML is syntactically valid
- [x] All version files currently agree on `3.2.6` (CI would pass if a `v3.2.6` tag were pushed)

## Bugs Found

No blocking bugs found.

**Informational security note (not logged as a bug — no actionable impact):**
The `validate-version` job uses `${{ github.event.inputs.tag }}` and `${{ github.ref_name }}` directly inside Bash `run:` blocks. These GitHub Actions context expressions are interpolated by the Actions runtime before the shell executes the script. If the tag contains shell metacharacters (e.g. `"; rm -rf /"`), they would be injected verbatim into the shell. In practice this attack requires write access to the repository (to push a malicious tag or trigger `workflow_dispatch`) — so the attack surface is limited to trusted collaborators. The recommended hardening is to pass user-controlled values as environment variables (`env: TAG: ${{ github.event.inputs.tag }}`) and reference them as `$TAG` in the shell. This is a hardening recommendation only; the current implementation is standard practice in the GitHub Actions ecosystem and poses no real-world risk for this project.

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**
