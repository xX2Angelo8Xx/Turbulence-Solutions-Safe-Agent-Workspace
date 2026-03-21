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
  └── coding/          ← Coding workspace template (shipped to users)
  └── creative-marketing/   ← Marketing/creative template
```

## Repository Structure

```
├── .github/
│   ├── agents/
│   │   ├── CLOUD-developer.agent.md
│   │   ├── CLOUD-maintenance.agent.md
│   │   ├── CLOUD-orchestrator.agent.md
│   │   ├── CLOUD-story-writer.agent.md
│   │   ├── CLOUD-tester.agent.md
│   │   ├── developer.agent.md
│   │   ├── maintenance.agent.md
│   │   ├── orchestrator.agent.md
│   │   ├── story-writer.agent.md
│   │   └── tester.agent.md
│   ├── instructions/
│   │   └── copilot-instructions.md
│   └── workflows/
│       └── release.yml
├── docs/
│   ├── bugs/
│   │   ├── User-Bug-Reports/
│   │   │   ├── 2026-03-20-workspace-review.md
│   │   │   ├── AgentExperienceReport_v3.1.2.md
│   │   │   └── BUG_REPORT-MacOS-2.0.0.md
│   │   └── bugs.csv
│   ├── maintenance/
│   │   ├── .gitkeep
│   │   ├── 2026-03-11-maintenance.md
│   │   ├── 2026-03-13-maintenance.md
│   │   ├── 2026-03-14-maintenance.md
│   │   ├── 2026-03-19-maintenance.md
│   │   ├── 2026-03-20-maintenance.md
│   │   ├── 2026-03-20b-maintenance.md
│   │   └── action-tracker.json
│   ├── plans/
│   │   ├── plan-fixLegacyValidationErrors.md
│   │   ├── plan-project-status-next-steps.md
│   │   └── vscode-session-id-methoden.md
│   ├── Security Audits/
│   │   ├── SECURITY_ADVANCED_ATTACK_ANALYSIS-V3.0.0-18-03.26.md
│   │   ├── SECURITY_AUDIT_REPORT-16-03.26-Handwritten.md
│   │   ├── SECURITY_AUDIT_REPORT-16-03.26.md
│   │   ├── SECURITY_AUDIT_REPORT-V2.0.0-17.03.26.md
│   │   ├── SECURITY_AUDIT_VERIFICATION_REPORT-V2.1.2-18-03.26.md
│   │   └── SECURITY_VERIFICATION_REPORT-17-03.26.md
│   ├── test-results/
│   │   └── test-results.csv
│   ├── user-stories/
│   │   └── user-stories.csv
│   ├── work-rules/
│   │   ├── agent-workflow.md
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
│   │   │   ├── .finalization-state.json
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
│   │   ├── MNT-001/
│   │   │   └── dev-log.md
│   │   ├── MNT-002/
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
│   │   │   ├── .finalization-state.json
│   │   │   ├── dev-log.md
│   │   │   └── test-report.md
│   │   ├── validation-exceptions.json
│   │   └── workpackages.csv
│   ├── architecture.md
│   ├── macos-installation-guide.md
│   └── project-scope.md
├── scripts/
│   ├── hooks/
│   │   └── pre-commit
│   ├── __init__.py
│   ├── _repair_csvs.py
│   ├── _verify.py
│   ├── add_bug.py
│   ├── add_test_result.py
│   ├── add_workpackage.py
│   ├── archive_test_results.py
│   ├── csv_utils.py
│   ├── dedup_test_ids.py
│   ├── finalize_wp.py
│   ├── install_hooks.py
│   ├── README.md
│   ├── run_tests.py
│   ├── update_architecture.py
│   └── validate_workspace.py
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
│   │   │   └── README.md
│   │   ├── shims/
│   │   │   ├── README.md
│   │   │   ├── ts-python
│   │   │   └── ts-python.cmd
│   │   └── windows/
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
│       │   └── vscode.py
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── components.py
│       │   └── validation.py
│       ├── __init__.py
│       ├── config.py
│       └── main.py
├── templates/
│   ├── coding/
│   │   ├── .github/
│   │   ├── .vscode/
│   │   ├── NoAgentZone/
│   │   ├── Project/
│   │   ├── .gitignore
│   │   └── README.md
│   └── creative-marketing/
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
│   ├── FIX-065/
│   ├── FIX-066/
│   ├── FIX-067/
│   ├── FIX-068/
│   ├── FIX-069/
│   ├── FIX-070/
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
│   ├── MNT-001/
│   ├── MNT-002/
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
│   ├── shared/
│   ├── __init__.py
│   └── conftest.py
├── launcher.spec
├── pyproject.toml
├── TS-Logo.ico
└── TS-Logo.png
```

## Task Tracking

All work is tracked in [workpackages/workpackages.csv](workpackages/workpackages.csv) (CSV format — open with a table-view extension in VS Code). Do not track tasks in this file.

Each workpackage in active development gets a dedicated folder under `docs/workpackages/<WP-ID>/` containing the developer's log (`dev-log.md`) and the tester's report (`test-report.md`). See [work-rules/workpackage-rules.md](work-rules/workpackage-rules.md) for details.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI) · **FIX** (Fix / Bug Fix) · **DOC** (Documentation)

All rules and workflows are documented in [work-rules/index.md](work-rules/index.md) — the central hub.

## Development Setup

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
- All security-critical code requires both a protection test and a bypass-attempt test.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- See [copilot-instructions.md](../.github/instructions/copilot-instructions.md) for the landing page and [work-rules/index.md](work-rules/index.md) for the complete rule set enforced on all contributors and AI agents.
