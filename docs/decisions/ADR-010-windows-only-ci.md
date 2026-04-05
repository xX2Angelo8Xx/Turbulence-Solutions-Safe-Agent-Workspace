# ADR-010: Windows-Only CI Until Stable Release

**Status:** Active
**Date:** 2026-04-05
**Related WPs:** MNT-027, MNT-028

---

## Context

The project is officially cross-platform (Windows, macOS, Linux). However, running CI on
all three platforms introduced several problems:

- **Cost:** macOS CI runners cost approximately 10× more than Ubuntu runners and ~5× more
  than Windows runners per minute. Running macOS and Linux jobs alongside Windows doubled
  CI costs without proportional quality gains.
- **Noise:** Most CI failures on macOS/Linux were test-infrastructure issues — missing
  PowerShell, fixture conflicts, wrong shim file creation — rather than genuine
  platform-specific regressions in the source code.
- **Duplication:** macOS/Linux test runs were not revealing unique bugs in the application
  code. Failures were mirrored from Windows or caused by CI configuration differences.
- **Stability:** The project has not yet reached a stable 1.0 release. Focusing engineering
  effort on one well-understood platform reduces noise and accelerates development velocity.

The CI workflow was updated in MNT-027 to disable macOS and Linux jobs.

---

## Decision

Run CI tests and build release artifacts on **Windows only** until the project reaches a
stable v4.0 release.

Specifically:

1. All GitHub Actions CI test jobs run on `windows-latest` only.
2. Release artifact builds (`PyInstaller` executables) are produced for Windows only.
3. All cross-platform source code is **preserved** — no platform-specific code is removed.
4. macOS/Linux CI jobs are **disabled** (commented out or conditioned), not deleted, so
   they can be re-enabled without redesign.
5. macOS and Linux are documented as "Deferred" platforms in the project scope.

---

## Consequences

### Positive

- Fewer false-positive CI failures from test-infrastructure issues on macOS/Linux.
- Faster CI feedback loop (one platform instead of three).
- Reduced CI costs by eliminating macOS runners.
- Less engineering time spent debugging platform-specific CI configuration.

### Negative

- macOS/Linux regressions in application code will not be caught in CI until those jobs
  are re-enabled.
- Users on macOS/Linux will not have pre-built release artifacts available.

### Mitigations

- All source code remains cross-platform; manual testing on macOS/Linux is still possible.
- Re-enablement criteria are documented below so the decision can be revisited.

---

## Re-Enablement Criteria

macOS/Linux CI jobs should be re-enabled when:

1. The project reaches a stable v4.0 release on Windows.
2. A dedicated CI budget review has been completed.
3. macOS/Linux test infrastructure issues (PowerShell availability, fixture conflicts) have
   been resolved or isolated.

---

## Alternatives Considered

- **Run on Ubuntu only:** Lower cost than macOS but still introduces platform-specific
  failures without meaningful benefit before stable release.
- **Run on all three platforms with stricter test filtering:** Would require significant
  investment in CI configuration that is better deferred until stable.
- **Use matrix strategy with `fail-fast: false`:** Reduces blocking but does not reduce
  cost or noise.
