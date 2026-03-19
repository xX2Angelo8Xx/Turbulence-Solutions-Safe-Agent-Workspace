---
name: developer
description: "Use when implementing a single workpackage. Reads requirements, writes code, writes tests, documents changes in a dev-log, then hands off to Tester for review. Follows the standard WP execution workflow. Use for: coding, implementation, development, feature work, bug fixes."
handoffs:
  - label: "Hand off to Tester"
    agent: tester
    prompt: "Developer Agent has completed implementation. The workpackage has been set to Review status. Please review the code, run the full test suite, check for edge cases and attack vectors, and write your test-report.md per docs/work-rules/testing-protocol.md."
    send: true
---
