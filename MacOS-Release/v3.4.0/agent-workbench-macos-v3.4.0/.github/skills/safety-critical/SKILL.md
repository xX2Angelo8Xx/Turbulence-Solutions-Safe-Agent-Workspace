---
name: safety-critical
description: "Checklist and mindset for safety-relevant tasks — motor control, web auth, hardware interfaces, data integrity. Load this when the task has real-world consequences."
---

# Safety-Critical Development Skill

Load this skill when the task involves safety-relevant functionality: physical systems (motor shutdown, valve control, propulsion), authentication/authorization, financial transactions, medical data, or any domain where a bug causes harm beyond inconvenience.

## Before You Start — Hazard Identification

Before writing any code, answer these questions and document the answers in `AgentDocs/decisions.md`:

1. **What is the worst thing that can happen if this code fails?**
2. **What inputs or states could trigger that failure?**
3. **Who or what is at risk?** (users, hardware, data, third parties)

If you cannot answer these questions, stop and ask the user or `@Planner` before proceeding.

## Development Rules

### 1. Fail Safe, Never Fail Open
- Default state must be the **safe state** (motor off, access denied, transaction rolled back).
- If any part of the system is uncertain, unknown, or erroring — choose the safe default.
- Never silently swallow exceptions in safety paths. Log, alert, or halt.

### 2. Validate at Every Boundary
- All external inputs: user input, sensor readings, API responses, config values.
- Apply **physical limits** where applicable (e.g., max RPM, temperature ceiling, timeout ceiling).
- Reject invalid input explicitly — do not coerce or guess.

### 3. No Silent Failures
- Every error in a safety path must be **observable**: logged, surfaced in UI, or returned as an error.
- If a safety check fails, the system must **actively communicate** the failure — not just skip the operation.

### 4. Document Safety Assumptions
Write all safety assumptions to `AgentDocs/decisions.md` with the tag `[SAFETY]`:
- What conditions must be true for this code to be safe?
- What happens if those conditions are violated?
- What is the fallback behavior?

### 5. Mandatory Test Cases
For each hazard identified in step 1, create at least one test that:
- Simulates the failure condition
- Verifies the system reaches the safe state
- Confirms the failure is observable (logged or raised)

## Checklist — Before Marking Done

| # | Check | Status |
|---|-------|--------|
| 1 | Hazards identified and documented in decisions.md | |
| 2 | Default state is the safe state in all code paths | |
| 3 | All external inputs validated with explicit rejection | |
| 4 | No silent exception swallowing in safety paths | |
| 5 | Safety assumptions documented with `[SAFETY]` tag | |
| 6 | At least one failure-mode test per identified hazard | |
| 7 | Timeout/watchdog exists for operations that can hang | |

## When in Doubt

If you are unsure whether something qualifies as safety-critical, treat it as safety-critical. The overhead of being cautious is a checklist. The cost of being wrong is harm.
