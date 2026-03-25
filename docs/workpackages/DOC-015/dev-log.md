# Dev Log — DOC-015

**Developer:** Developer Agent  
**Date started:** 2026-03-25  
**Iteration:** 1

## Objective

Research whether agents can be required to identify themselves (model name,
session ID) in their first tool call. Produce a research report covering:

1. VS Code Copilot hook payload inspection — does it include agent/model metadata?
2. Whether different models (GPT-4, Claude, etc.) include identifying headers or
   context in tool calls
3. Feasibility of a mandatory self-identification protocol (e.g. first tool call
   must include agent ID)
4. Security implications — can agent self-ID be spoofed?
5. Benefit analysis: better audit trails, per-model counter tracking
6. Recommendations: feasible or not, how to implement if feasible

---

## Implementation Summary

This is a **research-only workpackage**. No changes were made to `src/`,
`templates/`, or any existing source files. The deliverables are:

- `docs/workpackages/DOC-015/research-report.md` — full research report on
  agent self-identification feasibility
- `tests/DOC-015/test_doc015_report.py` — structural validation tests confirming
  the report exists and contains all required sections

---

## Research Summary

### Key Findings

1. **The VS Code Copilot hook payload does NOT include any model or agent identity
   metadata.** The `PreToolUse` hook payload delivered via stdin to `security_gate.py`
   contains only: `tool_name`, `tool_input` (the parameters), and workspace context.
   No `model`, `agent_id`, `session_id`, or `correlation_id` field is present at
   the application level. Session identity is inferred externally from the OTel JSONL
   export (`copilot-otel.jsonl`), not from the hook payload itself.

2. **No model distinguishes itself in tool call payloads.** GPT-4o, Claude Sonnet,
   Gemini and other models served via VS Code Copilot all use the same tool call
   schema. There are no model-specific HTTP headers, payload fields, or side-channel
   signals observable at the hook level. The model name is a runtime configuration
   choice that is not surfaced to hook scripts.

3. **A mandatory self-identification protocol based on hook payload content is not
   feasible without a VS Code / GitHub Copilot platform change.** An agent cannot
   inject a field like `agent_id` or `model_name` into the standard tool call
   payload — this is controlled by the tool-calling infrastructure, not the model.

4. **Self-reported agent identity in a `vscode_ask_questions` call can be spoofed
   trivially.** Any protocol that asks the agent to "introduce itself" in its first
   tool call is entirely under the agent's control and can be falsified.

5. **The OTel file provides partial, unreliable identity signal.** `copilot-otel.jsonl`
   carries a `session.id` (or `gen_ai.conversation.id`) from which sessions are
   distinguished. However, the OTel export does not contain the model name — it
   contains span/trace identifiers for telemetry purposes, not agent configuration.

6. **Per-model counter tracking is currently not achievable.** Because model
   identity is not exposed at the hook level, the denial counter cannot be bucketed
   per model. All sessions (regardless of model) share the same `session_id`-keyed
   counter, which is the correct design given available data.

### Files Inspected

- `templates/coding/.github/hooks/scripts/security_gate.py` — `main()`,
  `parse_input()`, `_read_otel_session_id()`, `_get_session_id()`,
  `build_response()`, payload field extraction
- `docs/workpackages/SAF-035/dev-log.md` — denial counter architecture
- `docs/workpackages/SAF-036/dev-log.md` — counter configuration
- `docs/workpackages/DOC-013/` (pending) — multi-agent context
- `docs/workpackages/DOC-014/research-report.md` — audit logging design

---

## Files Changed

| File | Change Type |
|------|-------------|
| `docs/workpackages/DOC-015/research-report.md` | Created (research report) |
| `docs/workpackages/DOC-015/dev-log.md` | Created (this file) |
| `tests/DOC-015/test_doc015_report.py` | Created (structural validation tests) |
| `docs/workpackages/workpackages.csv` | Updated status to In Progress, then Review |
| `docs/test-results/test-results.csv` | Updated via add_test_result.py |
