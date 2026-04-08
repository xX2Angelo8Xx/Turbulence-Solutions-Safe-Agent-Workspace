---
description: "Fast implementation of a runnable skeleton. Architecture over completeness — expansion points clearly marked."
---

# Prototype

You are building a **fast, runnable prototype**. The goal is a working skeleton with solid architecture that can be expanded later — not a finished product.

## Phase 1 — Extract Requirements

1. Identify the **minimal set of requirements** needed for a working demonstrator.
2. Separate must-haves from nice-to-haves. Nice-to-haves become `# TODO` markers.
3. Identify the entry point — what does the user run to see it work?

## Phase 2 — Define the Skeleton

1. Define the **entry points, interfaces, and data flow** before writing code.
2. Choose the simplest tech that gets the job done. No over-engineering.
3. Map the file/module structure. Keep it flat unless complexity demands otherwise.
4. Identify expansion points — where would features be added later?

## Phase 3 — Implement

1. Build the runnable skeleton. Every file must contribute to the demo working end-to-end.
2. Mark non-critical parts with `# TODO: [what goes here]` — do not implement them.
3. Include a minimal `README.md` or usage comment showing how to run the prototype.
4. Verify it runs. A prototype that does not execute is not a prototype.

## Principles

- **Architecture > completeness.** Get the structure right. Skip the polish.
- **Runnable > theoretical.** If it does not run, it is not done.
- **Expansion points > dead ends.** Make it obvious where features plug in later.
- **Fast > perfect.** Skip non-crucial validation, logging, and error handling. Mark them as TODOs.

## Output Format

```
### Prototype: [Name]

**Entry point:** `[command to run]`

**Structure:**
[file tree]

**Expansion points:**
- [ ] [TODO description and location]
- [ ] ...

**Known shortcuts:**
- [What was skipped and why]
```
