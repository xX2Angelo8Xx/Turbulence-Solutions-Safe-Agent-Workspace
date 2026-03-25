# DOC-016 Developer Log

**WP ID:** DOC-016  
**Name:** Research free Windows code signing for OSS  
**Branch:** DOC-016/code-signing-research  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-25  

---

## Implementation Summary

This workpackage required researching free Windows Authenticode code signing options
suitable for an open-source GitHub project, then producing a written research report
with a recommendation, setup requirements, CI integration steps, and certificate management guidance.

### Approach

Evaluated three candidate services as specified in the WP description:

1. **SignPath.io** — Free OSS plan
2. **Azure Trusted Signing** — Pay-per-use (no free OSS tier)
3. **SSL.com OSS programme** — No structured free programme; HSM requirement complicates CI

### Key Findings

- **SignPath.io** is the only genuinely free option for public GitHub OSS projects.
- SignPath provides EV-grade Authenticode certificates, which bypass SmartScreen reputation
  building — the signed binary is trusted immediately without needing download count accumulation.
- Azure Trusted Signing has no free tier (~$10/month minimum).
- SSL.com has no structured free OSS programme and the CA/B Forum HSM mandate (June 2023)
  makes software-based EV key storage non-compliant.
- A **one-time human account setup and OSS application review** (1–5 business days) is
  unavoidable for all three options. After approval, the pipeline is fully automated.

### Deliverable

Research report: `docs/plans/windows-code-signing.md`

Contents:
- Executive summary
- Requirements overview
- Evaluation of all three options with detailed analysis
- Comparison matrix
- Recommendation with rationale
- Step-by-step implementation plan (Phases A, B, C)
- Certificate management guidance
- Risk register with mitigations
- References section

---

## Files Changed

| File | Action |
|------|--------|
| `docs/plans/windows-code-signing.md` | Created — research report |
| `docs/workpackages/DOC-016/dev-log.md` | Created — this file |
| `docs/workpackages/workpackages.csv` | Updated status to In Progress → Review |
| `tests/DOC-016/test_doc016_report.py` | Created — document presence and structure tests |

---

## Tests Written

Location: `tests/DOC-016/test_doc016_report.py`

| Test | Description |
|------|-------------|
| `test_report_file_exists` | Verifies `docs/plans/windows-code-signing.md` exists |
| `test_report_is_nonempty` | Verifies the file has at least 500 characters |
| `test_report_has_setup_section` | Verifies "Setup" content is present |
| `test_report_has_ci_integration_section` | Verifies CI integration content is present |
| `test_report_has_recommendation_section` | Verifies recommendation content is present |
| `test_report_has_comparison_matrix` | Verifies a comparison table is present |
| `test_report_has_signpath_coverage` | Verifies SignPath.io is evaluated |
| `test_report_has_azure_coverage` | Verifies Azure Trusted Signing is evaluated |
| `test_report_has_sslcom_coverage` | Verifies SSL.com is evaluated |
| `test_report_has_certificate_management` | Verifies certificate management guidance is present |
| `test_report_has_references` | Verifies a references section exists |

All 11 tests pass.

---

## Known Limitations

- Research is based on publicly available documentation as of 2026-03-25. Pricing and
  programme availability may change.
- The SignPath OSS application requires human review; exact timeline cannot be guaranteed.
- The CI workflow snippets in the report are templates — actual org-id and slug values
  must be filled in after SignPath account creation (covered in INS-024).

---

## Decisions Made

- Chose not to include self-signed certificate option — it provides no user trust benefit
  over unsigned binaries and would muddy the recommendation.
- Included explicit "no-cost transition period" guidance so the project is not blocked on
  signing approval.
- Kept the implementation plan in the report itself (not a separate file) since DOC WPs
  are documentation-only deliverables.
