---
description: "Structured critical review of a plan, code, idea, or document. Finds logic mistakes, hidden assumptions, and weaknesses."
---

# Critical Review

You are performing a **structured critical review**. Your goal is to find what is wrong, what is weak, and what has been overlooked — not to praise what works.

## Phase 1 — Parse the Subject

1. Identify what is being reviewed: plan, code, idea, architecture, or document.
2. Summarize it in 2–3 sentences to confirm understanding.
3. If the subject is unclear or incomplete, state what is missing before proceeding.

## Phase 2 — Find the Flaws

Examine the subject for:
- **Logic errors** — Does the reasoning hold? Are there contradictions?
- **Hidden assumptions** — What is taken for granted that might not be true?
- **Missing edge cases** — What inputs, states, or scenarios were not considered?
- **Scalability concerns** — Does this hold under load, over time, or at larger scale?
- **Security gaps** — Are there attack vectors, data exposure risks, or trust assumptions?
- **Dependency risks** — Are there fragile dependencies or single points of failure?

## Phase 3 — Rank and Recommend

1. List the **top 3 highest-risk weaknesses** found.
2. For each, suggest a concrete alternative or mitigation.
3. Rate overall confidence in the subject: High / Medium / Low.

## Output Format

```
### Critical Review: [Subject Title]

**Summary:** [2–3 sentence summary of what was reviewed]

#### Findings

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 1 | ... | Critical / Major / Minor | Logic / Assumption / Edge Case / Security / ... |
| 2 | ... | ... | ... |
| ... | ... | ... | ... |

#### Top 3 Risks

1. **[Risk]** — [Mitigation]
2. **[Risk]** — [Mitigation]
3. **[Risk]** — [Mitigation]

#### Confidence: [High / Medium / Low]
[One sentence justifying the rating]
```
