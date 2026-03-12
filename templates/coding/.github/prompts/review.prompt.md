---
agent: TestingAgent
model: GPT-5 mini (copilot)
description: Perform a structured review of a file with actionable feedback.
---

Review the file at `$input` and provide structured feedback.

## Review Structure

1. **Summary** — What does this file do?
2. **Strengths** — What is done well?
3. **Issues** — Problems found (severity: high / medium / low)
4. **Suggestions** — Concrete improvements with code examples where applicable
5. **Verdict** — Overall assessment (Approve / Needs Changes / Reject)
