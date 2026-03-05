---
name: ts-code-review
description: Structured code review following Turbulence Solutions standards.
---

# Code Review Skill

Perform a code review following the Turbulence Solutions checklist.

## Checklist

- [ ] Code compiles/runs without errors
- [ ] Variable and function names are descriptive
- [ ] No hardcoded secrets, keys, or credentials
- [ ] Error handling is present and meaningful
- [ ] Comments explain "why", not "what"
- [ ] No unused imports or dead code
- [ ] Input validation is in place where applicable

## Output Format

For each checklist item, report:
- **Status**: Pass / Fail / N/A
- **Details**: Specific findings or evidence
- **Line(s)**: Reference to relevant code location

End with an overall score: X/7 items passed.
