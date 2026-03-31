---
description: "Traces an error or problem back to its root cause through systematic elimination. Forces depth over surface-level fixes."
---

# Root Cause Analysis

You are performing a **root cause analysis**. Your goal is to trace the problem to its single deepest cause — not to patch the symptom.

## Phase 1 — Describe the Symptom

1. State the observable problem precisely: what happens, when, and under what conditions.
2. Distinguish the symptom from the error. The symptom is what the user sees. The error may be elsewhere.
3. Reproduce or confirm the symptom if possible.

## Phase 2 — Trace the Chain

1. Start at the symptom and work backwards.
2. At each step, ask: **"Why does this happen?"** and answer with evidence, not speculation.
3. Eliminate surface causes:
   - Is it a configuration issue? → Check configs.
   - Is it a dependency issue? → Check versions and imports.
   - Is it a data issue? → Check inputs and state.
   - Is it a logic issue? → Read the code path.
4. Continue until you reach a cause that **cannot be explained by a deeper cause**.

## Phase 3 — Confirm the Root Cause

1. State the root cause in one sentence.
2. Draw the **causal chain**: `root cause → intermediate effect → ... → symptom`.
3. Rate your confidence: High (verified) / Medium (strong evidence) / Low (hypothesis).
4. Propose the **minimal fix** that addresses the root cause, not the symptom.

## Output Format

```
### Root Cause Analysis: [Problem Title]

**Symptom:** [What was observed]

**Causal Chain:**
root cause → [step] → [step] → symptom

| Step | Cause | Evidence |
|------|-------|----------|
| 1 (root) | ... | ... |
| 2 | ... | ... |
| ... | ... | ... |
| N (symptom) | ... | ... |

**Root Cause:** [One sentence]
**Confidence:** [High / Medium / Low]
**Recommended Fix:** [Minimal fix targeting the root cause]
```
