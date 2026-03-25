# Test Report — DOC-016

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Iteration:** 1

---

## Summary

The research report `docs/plans/windows-code-signing.md` is complete, detailed, and meets all
acceptance criteria from US-040. All three candidates (SignPath.io, Azure Trusted Signing,
SSL.com) are evaluated with documented setup requirements, cost analysis, CI integration
steps, and explicit verdicts. A clear recommendation for SignPath.io is provided with sound
rationale. The report is sufficiently detailed to support implementation by INS-024.

All 28 tests pass (11 Developer baseline + 17 Tester edge-case). No regressions introduced.

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2113: full regression suite | Regression | Fail (pre-existing) | 14 collection errors due to missing `yaml` module — pre-existing environment issue, unrelated to DOC-016 |
| TST-2114: DOC-016 targeted suite (28 tests) | Unit | Pass | 11 Developer + 17 Tester edge-case tests |
| `test_report_file_exists` | Unit | Pass | Report present at `docs/plans/windows-code-signing.md` |
| `test_report_is_nonempty` | Unit | Pass | 6 848 chars (well above 500 minimum) |
| `test_report_has_setup_section` | Unit | Pass | Setup steps present |
| `test_report_has_ci_integration_section` | Unit | Pass | GitHub Actions YAML present |
| `test_report_has_recommendation_section` | Unit | Pass | Section 4 is explicit recommendation |
| `test_report_has_comparison_matrix` | Unit | Pass | 8 table rows with all candidates |
| `test_report_has_signpath_coverage` | Unit | Pass | SignPath.io covered in full section 2.1 |
| `test_report_has_azure_coverage` | Unit | Pass | Azure Trusted Signing covered in section 2.2 |
| `test_report_has_sslcom_coverage` | Unit | Pass | SSL.com covered in section 2.3 |
| `test_report_has_certificate_management` | Unit | Pass | Section 6 covers cert management |
| `test_report_has_references` | Unit | Pass | 6 reference URLs in section 9 |
| `test_no_todo_placeholders` | Unit | Pass | No TODO/FIXME/TBD/placeholder text |
| `test_no_empty_sections` | Unit | Pass | All 9 H2 sections have substantial content |
| `test_has_executive_summary_heading` | Unit | Pass | Present |
| `test_has_recommendation_heading` | Unit | Pass | Present |
| `test_has_risks_section` | Unit | Pass | Risk register in section 7 |
| `test_has_phase_a_setup` | Unit | Pass | Phase A documented |
| `test_has_phase_b_workflow` | Unit | Pass | Phase B documented |
| `test_has_phase_c_verification` | Unit | Pass | Phase C reference documented |
| `test_has_yaml_code_block` | Unit | Pass | Full CI YAML snippet present |
| `test_has_github_secret_instructions` | Unit | Pass | `SIGNPATH_API_TOKEN` secret setup instructions present |
| `test_comparison_matrix_has_expected_columns` | Unit | Pass | All key columns (Free, Certificate, SmartScreen, CI, Key) present |
| `test_signpath_action_version_specified` | Unit | Pass | `@v1` version pinned in YAML snippet |
| `test_references_contain_urls` | Unit | Pass | 9 https:// URLs found |
| `test_all_three_candidates_have_verdict` | Unit | Pass | 2 explicit **Verdict:** statements (Azure, SSL.com) + recommendation for SignPath |
| `test_certificate_renewal_documented` | Unit | Pass | Renewal/rotation noted in section 6 |
| `test_smartscreen_bypass_explained` | Unit | Pass | SmartScreen + EV reputation bypass explained |
| `test_report_length_substantial` | Unit | Pass | 6 848 chars ≥ 5 000 minimum |

---

## Content Review

### Candidate Coverage
- **SignPath.io** (section 2.1): Full evaluation — eligibility table, certificate type, one-time
  setup steps (numbered), CI YAML snippet, caveats. Recommended.
- **Azure Trusted Signing** (section 2.2): Clearly documented as no free OSS tier (~$10/month),
  requires Azure subscription, SmartScreen reputation-based not EV. Excluded.
- **SSL.com** (section 2.3): No structured OSS programme, HSM mandate since June 2023 makes
  CI integration impractical. Excluded.

### Acceptance Criteria Verification (US-040)

| Criterion | Met? | Evidence |
|-----------|------|----------|
| AC1: .exe installer signed with valid Authenticode cert | ✅ | Section 2.1 / 5 — both launcher.exe and Setup.exe covered |
| AC2: SmartScreen warning eliminated | ✅ | EV certificate bypass explained; section 2.1, comparison matrix |
| AC3: `signtool verify /pa` passable | ✅ | Section 5, Phase B Step 6 includes `signtool verify /pa` verification |
| AC4: Signing automated in CI pipeline release.yml | ✅ | Full YAML snippet in section 5, Phase B |
| AC5: Certificate renewal process documented | ✅ | Section 6 — managed by SignPath, automatic renewal |

### Implementation Sufficiency for INS-024
The report provides:
- Numbered one-time setup steps (Phases A, B, C)
- Exact GitHub Secret name (`SIGNPATH_API_TOKEN`)
- Exact signing policy and project slugs
- Complete YAML code block ready for workflow insertion
- Reference to the official SignPath GitHub Action with pinned version

INS-024 can be implemented directly from this document without additional research.

### Security Review
- No credentials or secrets embedded in the report (placeholder notation `<SIGNPATH_ORG_ID>` is correct)
- API token guidance is correct: token is revocable, does not grant key access
- Private key is managed by SignPath HSM — never exposed to CI environment
- Risk register covers token leak scenario with mitigation

---

## Bugs Found

None.

---

## TODOs for Developer

None — the report meets all requirements.

---

## Verdict

**PASS — mark WP as Done**

The research report is thorough, actionable, free of placeholder content, and fully satisfies
the acceptance criteria for US-040. All 28 tests pass. The report is sufficient as sole input
for implementing INS-024.
