# Turbulence Solutions — Agent Environment Launcher

Cross-platform installer and launcher that creates pre-configured, safety-hardened VS Code workspaces for AI-assisted development. Each generated project includes a Python-based security gate that enforces tool access controls, zone-based file protection, and terminal command sanitization — ensuring AI agents operate within defined boundaries.

## Architecture

```
Installer (.exe / .dmg / .AppImage)
  └── Launcher GUI (customtkinter)
        ├── User selects: project name, type, destination
        ├── Copies template to destination folder
        └── Optionally opens VS Code with the new workspace

Templates (bundled inside Launcher)
  └── agent-workbench/   ← Agent Workbench template (shipped to users)
  └── certification-pipeline/   ← Certification Pipeline template
```

## Repository Structure

```
├── .github/
│   ├── agents/
│   │   ├── developer.agent.md
│   │   ├── maintenance.agent.md
│   │   ├── orchestrator.agent.md
│   │   ├── planner.agent.md
│   │   ├── story-writer.agent.md
│   │   └── tester.agent.md
│   ├── instructions/
│   │   └── copilot-instructions.md
│   ├── prompts/
│   │   └── status-report.prompt.md
│   └── workflows/
│       ├── macos-source-test.yml
│       ├── release.yml
│       ├── staging-test.yml
│       └── test.yml
├── docs/
│   ├── bugs/
│   │   ├── User-Bug-Reports/
│   │   │   ├── 2026-03-20-workspace-review.md
│   │   │   ├── AGENT_FEEDBACK_REPORT-v3.3.11.md
│   │   │   ├── AGENT_FEEDBACK_REPORT.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.1.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.2.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.3.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.4.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.5.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.2.6.md
│   │   │   ├── AGENT_FEEDBACK_REPORT_v3.3.6.md
│   │   │   ├── AgentExperienceReport_v3.1.2.md
│   │   │   ├── BUG_REPORT-MacOS-2.0.0.md
│   │   │   ├── Minimal_Agent_Feedback-3.3.8.md
│   │   │   ├── SAE_macOS_Error_Report_v323.md
│   │   │   └── security-hook-report.md
│   │   └── bugs.jsonl
│   ├── decisions/
│   │   ├── ADR-001-draft-releases.md
│   │   ├── ADR-002-ci-test-gate.md
│   │   ├── ADR-003-workspace-upgrade.md
│   │   ├── ADR-004-architecture-decision-records.md
│   │   ├── ADR-005-no-rollback-ui.md
│   │   ├── ADR-006-defer-code-signing.md
│   │   ├── ADR-007-csv-to-jsonl-migration.md
│   │   ├── ADR-008-tests-track-code.md
│   │   ├── ADR-009-cross-wp-test-impact.md
│   │   ├── ADR-010-windows-only-ci.md
│   │   ├── ADR-011.md
│   │   ├── ADR-TEMPLATE.md
│   │   └── index.jsonl
│   ├── maintenance/
│   │   ├── .gitkeep
│   │   ├── 2026-03-11-maintenance.md
│   │   ├── 2026-03-13-maintenance.md
│   │   ├── 2026-03-14-maintenance.md
│   │   ├── 2026-03-19-maintenance.md
│   │   ├── 2026-03-20-maintenance.md
│   │   ├── 2026-03-20b-maintenance.md
│   │   ├── 2026-03-24-maintenance.md
│   │   ├── 2026-03-25-maintenance.md
│   │   ├── 2026-03-30-maintenance.md
│   │   ├── 2026-04-01-maintenance.md
│   │   ├── action-tracker.json
│   │   └── orchestrator-runs.jsonl
│   ├── plans/
│   │   ├── plan-fixLegacyValidationErrors.md
│   │   ├── plan-project-status-next-steps.md
│   │   ├── plan-v321-feedback-report.md
│   │   ├── plan-v324-update.md
│   │   ├── vscode-session-id-methoden.md
│   │   └── windows-code-signing.md
│   ├── Security Audits/
│   │   ├── SECURITY_ADVANCED_ATTACK_ANALYSIS-V3.0.0-18-03.26.md
│   │   ├── SECURITY_AUDIT_REPORT-16-03.26-Handwritten.md
│   │   ├── SECURITY_AUDIT_REPORT-16-03.26.md
│   │   ├── SECURITY_AUDIT_REPORT-V2.0.0-17.03.26.md
│   │   ├── SECURITY_AUDIT_VERIFICATION_REPORT-V2.1.2-18-03.26.md
│   │   └── SECURITY_VERIFICATION_REPORT-17-03.26.md
│   ├── status-reports/
│   │   └── 2026-03-29-status-report.md
│   ├── test-results/
│   │   └── test-results.jsonl
│   ├── user-stories/
│   │   └── user-stories.jsonl
│   ├── work-rules/
│   │   ├── agent-workflow.md
│   │   ├── branch-protection.md
│   │   ├── bug-tracking-rules.md
│   │   ├── coding-standards.md
│   │   ├── commit-branch-rules.md
│   │   ├── index.md
│   │   ├── maintenance-protocol.md
│   │   ├── recovery.md
│   │   ├── security-rules.md
│   │   ├── testing-protocol.md
│   │   ├── user-story-rules.md
│   │   └── workpackage-rules.md
│   ├── workpackages/
│   │   ├── DOC-001/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-004/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-006/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-008/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-011/
│   │   │   ├── dev-log.md
│   │   │   ├── research-report.md
│   │   │   └── test-report.md
│   │   ├── DOC-012/
│   │   │   ├── dev-log.md
│   │   │   ├── research-report.md
│   │   │   └── test-report.md
│   │   ├── DOC-013/
│   │   │   ├── dev-log.md
│   │   │   ├── research-report.md
│   │   │   └── test-report.md
│   │   ├── DOC-014/
│   │   │   ├── dev-log.md
│   │   │   ├── research-report.md
│   │   │   └── test-report.md
│   │   ├── DOC-015/
│   │   │   ├── dev-log.md
│   │   │   ├── research-report.md
│   │   │   └── test-report.md
│   │   ├── DOC-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-024/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-025/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-026/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-027/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-028/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-029/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-030/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-031/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-032/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-033/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-034/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-035/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-036/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-037/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-038/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-039/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-040/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-041/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-042/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-043/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-044/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-045/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-046/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-047/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-048/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-049/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-050/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-051/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-052/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-053/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-054/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-055/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-056/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-057/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-058/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-059/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-060/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-061/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-062/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── DOC-063/
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-001/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-004/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-006/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-008/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-011/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-012/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-013/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-014/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-015/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-024/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-025/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-026/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-027/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-028/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-029/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-030/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-031/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-032/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-033/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-034/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-035/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-036/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-037/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-038/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-039/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-040/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-041/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-042/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-043/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-044/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-045/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-046/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-047/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-048/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-049/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-050/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-051/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-052/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-053/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-054/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-055/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-056/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-057/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-058/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-059/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-060/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-061/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-062/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-063/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-064/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-065/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-066/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-067/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-068/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-069/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-070/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-071/
│   │   │   ├── dev-log.md
│   │   │   ├── fix_8space_coding_paths.py
│   │   │   ├── fix_remaining_coding_paths.py
│   │   │   ├── test-report.md
│   │   │   └── transform_tests.py
│   │   ├── FIX-072/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-073/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-074/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-075/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-076/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-077/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-078/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-079/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-080/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-081/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-082/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-083/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-084/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-085/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-086/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-087/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-088/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-089/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-090/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-091/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-092/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-093/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-094/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-095/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-096/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-097/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-098/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-099/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-100/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-102/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-103/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-104/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-105/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-106/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-107/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-108/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-109/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-110/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-111/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-112/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-113/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-114/
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-115/
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-116/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-117/
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-118/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-119/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── FIX-120/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-001/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-004/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-006/
│   │   │   ├── dev-log.md
│   │   │   ├── gui006_result.txt
│   │   │   ├── gui006_run.txt
│   │   │   ├── gui006_run2.txt
│   │   │   └── test-report.md
│   │   ├── GUI-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-008/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-011/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-012/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-013/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-014/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-015/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-033/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-034/
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── GUI-035/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-001/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-004/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-006/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-008/
│   │   │   └── dev-log.md
│   │   ├── INS-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-011/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-012/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-013/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-014/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-015/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-026/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-027/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-028/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-029/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── INS-030/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-001/
│   │   │   └── dev-log.md
│   │   ├── MNT-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-004/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-006/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-008/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-011/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-012/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-013/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-014/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-015/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-024/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-025/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-026/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-027/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-028/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── MNT-029/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-001/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-002/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-003/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-004/
│   │   │   ├── dev-log.md
│   │   │   ├── terminal-sanitization-design.md
│   │   │   └── test-report.md
│   │   ├── SAF-005/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-006/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-007/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-008/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-009/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-010/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-011/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-012/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-013/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-014/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-015/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-016/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-017/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-018/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-019/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-020/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-021/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-022/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-023/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-024/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-025/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-026/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-027/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-028/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-029/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-030/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-031/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-032/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-033/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-034/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-035/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-036/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-037/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-038/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-039/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-040/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-041/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-042/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-043/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-044/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-045/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-046/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-047/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-048/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-049/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-050/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-051/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-052/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-055/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-056/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-057/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-058/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-059/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-060/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-061/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-062/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-063/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-065/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-066/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-068/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-069/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-070/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-071/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-072/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-073/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-074/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-075/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-076/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-077/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── SAF-078/
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── validation-exceptions.json
│   │   └── workpackages.jsonl
│   ├── architecture.md
│   ├── macos-installation-guide.md
│   └── project-scope.md
├── scripts/
│   ├── hooks/
│   │   └── pre-commit
│   ├── __init__.py
│   ├── _add_wps_batch.py
│   ├── add_bug.py
│   ├── add_test_result.py
│   ├── add_workpackage.py
│   ├── archive_test_results.py
│   ├── check_test_impact.py
│   ├── csv_utils.py
│   ├── dedup_test_ids.py
│   ├── finalize_wp.py
│   ├── generate_manifest.py
│   ├── install-macos.sh
│   ├── install_hooks.py
│   ├── jsonl_utils.py
│   ├── migrate_csv_to_jsonl.py
│   ├── README.md
│   ├── release.py
│   ├── run_tests.py
│   ├── update_architecture.py
│   ├── update_bug_status.py
│   ├── validate_workspace.py
│   └── verify_parity.py
├── src/
│   ├── installer/
│   │   ├── linux/
│   │   │   ├── build_appimage.sh
│   │   │   └── README.md
│   │   ├── macos/
│   │   │   ├── build_dmg.sh
│   │   │   ├── entitlements.plist
│   │   │   └── README.md
│   │   ├── python-embed/
│   │   │   ├── _asyncio.pyd
│   │   │   ├── _bz2.pyd
│   │   │   ├── _ctypes.pyd
│   │   │   ├── _decimal.pyd
│   │   │   ├── _elementtree.pyd
│   │   │   ├── _hashlib.pyd
│   │   │   ├── _lzma.pyd
│   │   │   ├── _msi.pyd
│   │   │   ├── _multiprocessing.pyd
│   │   │   ├── _overlapped.pyd
│   │   │   ├── _queue.pyd
│   │   │   ├── _socket.pyd
│   │   │   ├── _sqlite3.pyd
│   │   │   ├── _ssl.pyd
│   │   │   ├── _uuid.pyd
│   │   │   ├── _zoneinfo.pyd
│   │   │   ├── libcrypto-3.dll
│   │   │   ├── libffi-8.dll
│   │   │   ├── libssl-3.dll
│   │   │   ├── LICENSE.txt
│   │   │   ├── pyexpat.pyd
│   │   │   ├── python.cat
│   │   │   ├── python.exe
│   │   │   ├── python3.dll
│   │   │   ├── python311._pth
│   │   │   ├── python311.dll
│   │   │   ├── python311.zip
│   │   │   ├── pythonw.exe
│   │   │   ├── README.md
│   │   │   ├── select.pyd
│   │   │   ├── sqlite3.dll
│   │   │   ├── unicodedata.pyd
│   │   │   ├── vcruntime140.dll
│   │   │   ├── vcruntime140_1.dll
│   │   │   └── winsound.pyd
│   │   ├── shims/
│   │   │   ├── README.md
│   │   │   ├── ts-python
│   │   │   └── ts-python.cmd
│   │   └── windows/
│   │       ├── Output/
│   │       ├── README.md
│   │       └── setup.iss
│   └── launcher/
│       ├── core/
│       │   ├── __init__.py
│       │   ├── applier.py
│       │   ├── downloader.py
│       │   ├── github_auth.py
│       │   ├── os_utils.py
│       │   ├── project_creator.py
│       │   ├── shim_config.py
│       │   ├── updater.py
│       │   ├── user_settings.py
│       │   ├── vscode.py
│       │   └── workspace_upgrader.py
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── components.py
│       │   └── validation.py
│       ├── __init__.py
│       ├── config.py
│       └── main.py
├── templates/
│   ├── agent-workbench/
│   │   ├── .github/
│   │   ├── .vscode/
│   │   ├── NoAgentZone/
│   │   ├── Project/
│   │   ├── .gitignore
│   │   ├── MANIFEST.json
│   │   └── README.md
│   ├── certification-pipeline/
│   │   └── README.md
│   └── clean-workspace/
│       ├── .github/
│       ├── .vscode/
│       ├── NoAgentZone/
│       ├── Project/
│       ├── .gitignore
│       ├── MANIFEST.json
│       └── README.md
├── tests/
│   ├── DOC-001/
│   ├── DOC-002/
│   ├── DOC-003/
│   ├── DOC-004/
│   ├── DOC-005/
│   ├── DOC-006/
│   ├── DOC-007/
│   ├── DOC-008/
│   ├── DOC-009/
│   ├── DOC-010/
│   ├── DOC-011/
│   ├── DOC-012/
│   ├── DOC-013/
│   ├── DOC-014/
│   ├── DOC-015/
│   ├── DOC-016/
│   ├── DOC-017/
│   ├── DOC-018/
│   ├── DOC-019/
│   ├── DOC-020/
│   ├── DOC-021/
│   ├── DOC-022/
│   ├── DOC-023/
│   ├── DOC-024/
│   ├── DOC-025/
│   ├── DOC-026/
│   ├── DOC-027/
│   ├── DOC-028/
│   ├── DOC-029/
│   ├── DOC-030/
│   ├── DOC-031/
│   ├── DOC-032/
│   ├── DOC-033/
│   ├── DOC-034/
│   ├── DOC-035/
│   ├── DOC-036/
│   ├── DOC-037/
│   ├── DOC-038/
│   ├── DOC-039/
│   ├── DOC-040/
│   ├── DOC-041/
│   ├── DOC-042/
│   ├── DOC-043/
│   ├── DOC-044/
│   ├── DOC-045/
│   ├── DOC-046/
│   ├── DOC-047/
│   ├── DOC-048/
│   ├── DOC-049/
│   ├── DOC-050/
│   ├── DOC-051/
│   ├── DOC-052/
│   ├── DOC-053/
│   ├── DOC-054/
│   ├── DOC-055/
│   ├── DOC-056/
│   ├── DOC-057/
│   ├── DOC-058/
│   ├── DOC-059/
│   ├── DOC-060/
│   ├── DOC-061/
│   ├── DOC-062/
│   ├── DOC-063/
│   ├── FIX-001/
│   ├── FIX-002/
│   ├── FIX-003/
│   ├── FIX-004/
│   ├── FIX-005/
│   ├── FIX-006/
│   ├── FIX-007/
│   ├── FIX-008/
│   ├── FIX-009/
│   ├── FIX-010/
│   ├── FIX-011/
│   ├── FIX-012/
│   ├── FIX-013/
│   ├── FIX-014/
│   ├── FIX-015/
│   ├── FIX-016/
│   ├── FIX-017/
│   ├── FIX-018/
│   ├── FIX-019/
│   ├── FIX-020/
│   ├── FIX-021/
│   ├── FIX-022/
│   ├── FIX-023/
│   ├── FIX-024/
│   ├── FIX-025/
│   ├── FIX-026/
│   ├── FIX-027/
│   ├── FIX-028/
│   ├── FIX-029/
│   ├── FIX-030/
│   ├── FIX-031/
│   ├── FIX-032/
│   ├── FIX-033/
│   ├── FIX-034/
│   ├── FIX-035/
│   ├── FIX-036/
│   ├── FIX-037/
│   ├── FIX-038/
│   ├── FIX-039/
│   ├── FIX-040/
│   ├── FIX-041/
│   ├── FIX-042/
│   ├── FIX-043/
│   ├── FIX-044/
│   ├── FIX-045/
│   ├── FIX-046/
│   ├── FIX-047/
│   ├── FIX-048/
│   ├── FIX-049/
│   ├── FIX-050/
│   ├── FIX-051/
│   ├── FIX-052/
│   ├── FIX-053/
│   ├── FIX-054/
│   ├── FIX-055/
│   ├── FIX-056/
│   ├── FIX-057/
│   ├── FIX-058/
│   ├── FIX-059/
│   ├── FIX-060/
│   ├── FIX-061/
│   ├── FIX-062/
│   ├── FIX-063/
│   ├── FIX-064/
│   ├── FIX-065/
│   ├── FIX-066/
│   ├── FIX-067/
│   ├── FIX-068/
│   ├── FIX-069/
│   ├── FIX-070/
│   ├── FIX-071/
│   ├── FIX-072/
│   ├── FIX-073/
│   ├── FIX-074/
│   ├── FIX-075/
│   ├── FIX-076/
│   ├── FIX-077/
│   ├── FIX-078/
│   ├── FIX-079/
│   ├── FIX-080/
│   ├── FIX-081/
│   ├── FIX-082/
│   ├── FIX-083/
│   ├── FIX-084/
│   ├── FIX-085/
│   ├── FIX-086/
│   ├── FIX-087/
│   ├── FIX-088/
│   ├── FIX-089/
│   ├── FIX-090/
│   ├── FIX-091/
│   ├── FIX-092/
│   ├── FIX-093/
│   ├── FIX-094/
│   ├── FIX-095/
│   ├── FIX-096/
│   ├── FIX-097/
│   ├── FIX-098/
│   ├── FIX-099/
│   ├── FIX-100/
│   ├── FIX-101/
│   ├── FIX-102/
│   ├── FIX-103/
│   ├── FIX-104/
│   ├── FIX-105/
│   ├── FIX-106/
│   ├── FIX-107/
│   ├── FIX-108/
│   ├── FIX-109/
│   ├── FIX-110/
│   ├── FIX-111/
│   ├── FIX-112/
│   ├── FIX-113/
│   ├── FIX-114/
│   ├── FIX-115/
│   ├── FIX-116/
│   ├── FIX-117/
│   ├── FIX-118/
│   ├── FIX-119/
│   ├── FIX-120/
│   ├── GUI-001/
│   ├── GUI-002/
│   ├── GUI-003/
│   ├── GUI-004/
│   ├── GUI-005/
│   ├── GUI-006/
│   ├── GUI-007/
│   ├── GUI-008/
│   ├── GUI-009/
│   ├── GUI-010/
│   ├── GUI-011/
│   ├── GUI-012/
│   ├── GUI-013/
│   ├── GUI-014/
│   ├── GUI-015/
│   ├── GUI-016/
│   ├── GUI-017/
│   ├── GUI-018/
│   ├── GUI-019/
│   ├── GUI-020/
│   ├── GUI-021/
│   ├── GUI-022/
│   ├── GUI-023/
│   ├── GUI-033/
│   ├── GUI-034/
│   ├── GUI-035/
│   ├── INS-001/
│   ├── INS-002/
│   ├── INS-003/
│   ├── INS-004/
│   ├── INS-005/
│   ├── INS-006/
│   ├── INS-007/
│   ├── INS-009/
│   ├── INS-010/
│   ├── INS-011/
│   ├── INS-012/
│   ├── INS-013/
│   ├── INS-014/
│   ├── INS-015/
│   ├── INS-016/
│   ├── INS-017/
│   ├── INS-018/
│   ├── INS-019/
│   ├── INS-020/
│   ├── INS-021/
│   ├── INS-022/
│   ├── INS-023/
│   ├── INS-026/
│   ├── INS-027/
│   ├── INS-028/
│   ├── INS-029/
│   ├── INS-030/
│   ├── MNT-001/
│   ├── MNT-002/
│   ├── MNT-003/
│   ├── MNT-004/
│   ├── MNT-005/
│   ├── MNT-006/
│   ├── MNT-007/
│   ├── MNT-008/
│   ├── MNT-009/
│   ├── MNT-010/
│   ├── MNT-011/
│   ├── MNT-012/
│   ├── MNT-013/
│   ├── MNT-014/
│   ├── MNT-015/
│   ├── MNT-016/
│   ├── MNT-017/
│   ├── MNT-018/
│   ├── MNT-019/
│   ├── MNT-020/
│   ├── MNT-021/
│   ├── MNT-022/
│   ├── MNT-023/
│   ├── MNT-024/
│   ├── MNT-025/
│   ├── MNT-026/
│   ├── MNT-027/
│   ├── MNT-028/
│   ├── MNT-029/
│   ├── SAF-001/
│   ├── SAF-002/
│   ├── SAF-003/
│   ├── SAF-004/
│   ├── SAF-005/
│   ├── SAF-006/
│   ├── SAF-007/
│   ├── SAF-008/
│   ├── SAF-009/
│   ├── SAF-010/
│   ├── SAF-011/
│   ├── SAF-012/
│   ├── SAF-013/
│   ├── SAF-014/
│   ├── SAF-015/
│   ├── SAF-016/
│   ├── SAF-017/
│   ├── SAF-018/
│   ├── SAF-019/
│   ├── SAF-020/
│   ├── SAF-021/
│   ├── SAF-022/
│   ├── SAF-023/
│   ├── SAF-024/
│   ├── SAF-025/
│   ├── SAF-026/
│   ├── SAF-027/
│   ├── SAF-028/
│   ├── SAF-029/
│   ├── SAF-030/
│   ├── SAF-031/
│   ├── SAF-032/
│   ├── SAF-033/
│   ├── SAF-034/
│   ├── SAF-035/
│   ├── SAF-036/
│   ├── SAF-037/
│   ├── SAF-038/
│   ├── SAF-039/
│   ├── SAF-040/
│   ├── SAF-041/
│   ├── SAF-042/
│   ├── SAF-043/
│   ├── SAF-044/
│   ├── SAF-045/
│   ├── SAF-046/
│   ├── SAF-047/
│   ├── SAF-048/
│   ├── SAF-049/
│   ├── SAF-050/
│   ├── SAF-051/
│   ├── SAF-052/
│   ├── SAF-055/
│   ├── SAF-056/
│   ├── SAF-057/
│   ├── SAF-058/
│   ├── SAF-059/
│   ├── SAF-060/
│   ├── SAF-061/
│   ├── SAF-062/
│   ├── SAF-063/
│   ├── SAF-065/
│   ├── SAF-066/
│   ├── SAF-068/
│   ├── SAF-069/
│   ├── SAF-070/
│   ├── SAF-071/
│   ├── SAF-072/
│   ├── SAF-073/
│   ├── SAF-074/
│   ├── SAF-075/
│   ├── SAF-076/
│   ├── SAF-077/
│   ├── SAF-078/
│   ├── shared/
│   ├── snapshots/
│   ├── __init__.py
│   ├── conftest.py
│   └── regression-baseline.json
├── launcher.spec
├── Makefile
├── pyproject.toml
├── python-embed.zip
├── TS-Logo.ico
└── TS-Logo.png
```

## Template System

The launcher ships two templates bundled inside the executable:

| Template | Path | Purpose |
|----------|------|---------|
| **Agent Workbench** | `templates/agent-workbench/` | Full safety-hardened workspace shipped to end users. Contains the security gate, agent definitions, AgentDocs, and all supporting tooling. |
| **Certification Pipeline** | `templates/certification-pipeline/` | Stub template reserved for future use. |

Prior to v3.3.0 the template was named `safe-agent-workspace`. All references have been updated to `agent-workbench`.

## Agent System

Agent definitions live in `.github/agents/` and are loaded by VS Code GitHub Copilot:

| File | Role |
|------|------|
| `orchestrator.agent.md` | Decomposes multi-WP tasks and delegates to Developer subagents |
| `developer.agent.md` | Implements a single workpackage end-to-end |
| `tester.agent.md` | Reviews and validates a workpackage marked for Review |
| `story-writer.agent.md` | Creates and refines user stories |
| `maintenance.agent.md` | Runs the 9-point maintenance checklist |

Cloud variants (`CLOUD-*.agent.md`) mirror the local agents but target the cloud Copilot environment.

### AgentDocs System

The `templates/agent-workbench/Project/AgentDocs/` directory is a structured documentation system designed for agents operating inside deployed workspaces. It contains:

| File | Purpose |
|------|---------|
| `AGENT-RULES.md` | Mandatory operating rules consolidated from all rule files — the single authoritative reference agents read at session start |
| `architecture.md` | Project architecture notes for the deployed workspace |
| `decisions.md` | Decision log tracking key design choices |
| `open-questions.md` | Open questions and unresolved items |
| `plan.md` | Project plan document |
| `progress.md` | Progress log updated by agents during development |
| `research-log.md` | Research log for tracking external information |

The AgentDocs system was introduced in v3.3.0 (DOC-035) and consolidated in v3.3.5 (DOC-045) to replace the older distributed rule file system.

## Workspace Prefix

All workspaces generated by the launcher use the `SAE-` prefix for their root folder name (e.g. `SAE-MyProject`). The prefix was updated in v3.3.5 (GUI-033). Any references to the old prefix in documentation or tooling are stale and should be updated.

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v3.3.6 | 2026-03 | Agent feedback cycle; security gate tool name normalization (SAF-063); prefix rename tests (DOC-048); AGENT-RULES consolidation tests (DOC-047). |
| v3.3.5 | 2026-03 | Workspace prefix renamed to `SAE-` (GUI-033); AGENT-RULES consolidated into AgentDocs (DOC-045); copilot-instructions slimmed (DOC-046). |
| v3.3.4 | 2026-03 | Agent frontmatter tools and model updated (DOC-041/DOC-042). |
| v3.3.2 | 2026-03 | Agent default model updated; coordinator YAML syntax fixed (DOC-042). |
| v3.3.1 | 2026-03 | CREATE_NO_WINDOW flag added to suppress terminal flash on Windows (FIX-092); app.py and requirements.txt removed from template (FIX-091). |
| v3.3.0 | 2026-03 | AgentDocs folder created with AGENT-RULES, TOOL-MATRIX, QUICKREF (DOC-035); agent personas rewritten with AgentDocs philosophy (DOC-036); new prompts added (DOC-037). |
| v3.2.6 | 2026-03 | Denial counter configurable threshold and persistence (SAF-036/SAF-037). |

## Task Tracking

All work is tracked in [workpackages/workpackages.jsonl](workpackages/workpackages.jsonl) (JSONL format — one JSON object per line). Do not track tasks in this file.

Each workpackage in active development gets a dedicated folder under `docs/workpackages/<WP-ID>/` containing the developer's log (`dev-log.md`) and the tester's report (`test-report.md`). See [work-rules/workpackage-rules.md](work-rules/workpackage-rules.md) for details.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI) · **FIX** (Fix / Bug Fix) · **DOC** (Documentation)

All rules and workflows are documented in [work-rules/index.md](work-rules/index.md) — the central hub.

## Development Setup

> **CI/CD scope note:** CI/CD currently targets Windows only (see ADR-010). macOS and Linux workflows are preserved but disabled.

Prerequisites:
- Python 3.11+
- VS Code with GitHub Copilot
- GitHub CLI (`gh`) authenticated as `xX2Angelo8Xx`

### First-time setup

```powershell
# 1. Clone the repository
git clone https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git "Github Repository"
cd "Github Repository"

# 2. Create the workspace virtual environment (never use global pip)
python -m venv .venv

# 3. Install the project in editable mode with all dev dependencies
.venv\Scripts\pip install -e ".[dev]"

# 4. Run the full test suite to verify setup
.venv\Scripts\python -m pytest tests/ -v
```

> All Python commands in this project must use `.venv\Scripts\python` (Windows) or `.venv/bin/python` (macOS/Linux). Never install packages globally.

### Git configuration (one-time per machine)

```powershell
# Authenticate GitHub CLI with the project account
gh auth login --hostname github.com

# Set repository-local git identity
git config user.name "xX2Angelo8Xx"
git config user.email "angelomichaelamon2001@gmail.com"
```

## Security Policy

This project enforces a **safety-first** development policy:

- The Python security gate (`security_gate.py`) replaces the previous PowerShell/Bash hook scripts, closing all known bypass vectors identified in the security audit.
- Configurable denial counter with threshold, reset, and disable options (SAF-036/SAF-037).
- All security-critical code requires both a protection test and a bypass-attempt test.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- See [copilot-instructions.md](../.github/instructions/copilot-instructions.md) for the landing page and [work-rules/index.md](work-rules/index.md) for the complete rule set enforced on all contributors and AI agents.
