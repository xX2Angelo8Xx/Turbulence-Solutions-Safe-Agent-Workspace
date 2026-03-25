# Research Report — DOC-013: Multi-Agent Counter Coordination

**Author:** Developer Agent  
**Date:** 2026-03-25  
**Workpackage:** DOC-013  
**User Story:** US-034  
**Status:** Final  

---

## Executive Summary

This report examines how the denial counter (implemented in SAF-035/SAF-036) should
behave when multiple agents or subagents share a workspace simultaneously. The core
tension is between security (preventing a rogue agent from evading the lockout by
spawning subagents) and development workflow (not penalising legitimate multi-agent
use such as the VS Code Copilot `search_subagent` tool).

**Recommendation:** Use a **shared counter keyed by the OTel session ID**. Subagents
invoked from a parent agent session inherit the same `session.id` from VS Code's
telemetry export and therefore share the parent's deny count. This requires no code
change to the existing session identification logic: the OTel-based session resolution
already ensures all agents in one Copilot session use one counter. A workspace
configuration option to set an independent subagent counter is explicitly **not**
recommended at this time because it creates a trivially exploitable bypass path.

---

## 1. VS Code Hook Payload — Session Identification for Subagents

### 1.1 What the Hook Receives

When VS Code Copilot invokes a tool, it runs the hook script
(`.github/hooks/scripts/security_gate.py`) with a JSON object on stdin. The schema
documented in the Copilot extensibility preview is:

```json
{
  "tool_name": "create_file",
  "input": { "filePath": "...", "content": "..." }
}
```

The payload does **not** contain an agent identifier, a subagent flag, or a parent
session reference. VS Code does not distinguish main agents from subagents in the hook
payload — both receive the identical schema.

### 1.2 How the Gate Resolves a Session ID

`security_gate.py` uses a two-step session resolution (function `_get_session_id`):

1. **OTel JSONL** — reads `copilot-otel.jsonl` in the scripts directory. This file
   is written by VS Code's OpenTelemetry export and contains span data with a
   `session.id` resource attribute or a `gen_ai.conversation.id` span attribute.
2. **UUID4 fallback** — if the OTel file is absent or cannot be parsed, a UUID4 is
   generated on first invocation and persisted across calls in `.hook_state.json`
   under the key `_fallback_session_id`.

### 1.3 Subagent Behaviour in the OTel File

The `copilot-otel.jsonl` file reflects **VS Code's Copilot session**, not an
individual agent or subagent. Based on analysis of the VS Code Copilot
instrumentation design:

- Each VS Code Copilot *conversation* (a single user message thread) shares one
  `gen_ai.conversation.id`.
- When a main agent invokes `search_subagent` or `runSubagent`, the spawned subagent
  operates within the **same Copilot conversation**. VS Code creates a child span
  under the parent span but does not emit a new `session.id` or `conversation.id`.
- Therefore, the OTel JSONL file as consumed by `_read_otel_session_id` returns the
  **same session ID** for both the parent agent and any subagents it invokes.
- **Conclusion for the fallback path:** If the OTel file is absent, the UUID4
  fallback is created once per gate startup. Because all agents in one conversation
  share the same process-level workspace and hook directory, they will all read the
  same `.hook_state.json` and therefore the same `_fallback_session_id`. Both paths
  produce a shared counter.

### 1.4 Observable Limitation

There is **no way** to determine from the hook payload whether the caller is a main
agent or a subagent. The payload schema is identical. Any future mechanism for
separate subagent tracking would require VS Code to expose agent-type metadata in
the hook payload, which is not currently part of the public Copilot extensibility API.

---

## 2. Counter Strategy Options

Three counter strategies were evaluated:

### Option A — Shared Counter (all agents count toward same limit)

All tool-call denials from any agent in the session increment the same counter keyed
by the session ID. This is the **current behaviour** as implemented in SAF-035.

**Pros:**
- No code change required.
- Prevents the subagent spawning bypass: if a rogue agent spawns 10 subagents and
  each makes 2 policy-violating calls, the 20-denial lockout is reached after exactly
  the same number of violations as if the main agent made them directly.
- Counter semantics are simple and auditable.

**Cons:**
- Legitimate multi-agent workflows (e.g., a main agent using `search_subagent` for
  code lookup, while both are denied an unrelated action) accumulate denials faster
  than single-agent workflows.
- A very aggressive multi-agent workflow with high task fan-out could theoretically
  exhaust the counter before a human restores context — though with a default
  threshold of 20 this is unlikely in practice.

### Option B — Independent Counters (each agent or subagent has own limit)

Each identifiable agent context maintains its own counter. Because VS Code does not
expose a subagent identifier in the hook payload, "each agent" would need to be
inferred from some observable difference (e.g., separate OTel span IDs or a
hypothetical `agent_id` field).

**Pros:**
- In principle, a legitimate agent would not be penalised by a rogue co-agent.

**Cons:**
- **Not feasible today**: the hook payload contains no field that reliably identifies
  a subagent independently of its parent session. Any heuristic (e.g., span ID) is
  fragile and would create false splits under normal usage.
- **Creates a bypass**: if independent counters were implemented and the subagent
  boundary were detectable, a rogue agent could spawn N subagents, each performing
  `threshold - 1` violations before being replaced, achieving `N × (threshold - 1)`
  total violations without triggering lockout. This is the exact attack described in
  OWASP A01 (Broken Access Control).
- Complexity cost is high for marginal benefit.

### Option C — No Counter for Subagents

Subagents (if they could be identified) are exempt from the denial counter entirely.
Their violations are recorded but do not count toward lockout.

**Pros:**
- Avoids penalising legitimate subagent workflows.

**Cons:**
- **Severe bypass risk**: a rogue main agent that is aware of this rule will
  immediately delegate all policy-violating attempts to spawned subagents. If
  subagents can make unlimited violations without consequence, the entire counter
  mechanism is neutralised.
- This option fails the fail-closed principle (see `coding-standards.md`).

---

## 3. Security Implications — Subagent Bypass Analysis

### 3.1 Threat Model

**Threat actor:** A rogue AI agent that has been instructed (via prompt injection or
adversarial instructions) to exfiltrate data, write to restricted paths, or execute
blocked commands, and that is aware of the 20-denial lockout threshold.

**Attack vector:** Spawn multiple subagents (via `runSubagent` or `search_subagent`)
and distribute policy-violating calls across them to stay under the threshold for
each individual agent.

### 3.2 Analysis by Option

| Option | Attack feasibility | Reason |
|--------|--------------------|--------|
| A — Shared counter | **Not feasible** | Total denials across all agents converge on the same counter. Spawning 5 subagents that each trigger 4 denials still totals 20. Lockout occurs. |
| B — Independent counters | **Feasible** | Each subagent resets the counter window. N subagents = N × threshold violations before lockout. Bypass scales linearly with subagent count. |
| C — No counter for subagents | **Trivially feasible** | One delegation call to a subagent suffices to bypass all counter enforcement. |

### 3.3 Current Risk Assessment (Option A, as implemented)

Under the shared-counter model:
- A rogue agent that spawns subagents **does not gain any counter advantage**: the
  total cross-agent deny count is what matters.
- The `runSubagent` / `search_subagent` tools are in `_ALWAYS_ALLOW_TOOLS` and
  `_EXEMPT_TOOLS` respectively. Spawning a subagent does not consume a denial.
  Only the subagent's *individual* policy-violating tool calls consume denials.
- This is the correct design: the act of delegation is not penalised, but the
  violations performed by the delegate are counted.

### 3.4 Residual Risk

The shared counter relies on the OTel session ID or fallback UUID4 persisting
consistently. If an agent can delete `.hook_state.json` (a file write inside the
allowed zone) **and** cause the OTel JSONL to rotate or be truncated, it could reset
the counter. This is mitigated by:
1. The OTel JSONL is written by VS Code, not by the agent; agents cannot control its
   `session.id` value.
2. The SAF-033 rule blocks `update_hashes` execution. A complementary protection
   (`reset_hook_counter.py` requires human confirmation in the launcher) is
   implemented in SAF-037.
3. A write to `.hook_state.json` itself is zone-checked: the `.github/hooks/scripts/`
   directory is a restricted zone, so direct deletion is blocked by the gate.

---

## 4. Recommendation

### 4.1 Primary Recommendation — Retain Shared Counter (no code change)

Maintain the existing behaviour: all tool-call denials within a VS Code Copilot
session share one counter keyed by the OTel `session.id` (or UUID4 fallback). This
approach is:

- **Secure by default** — no bypass opportunity via subagent spawning.
- **Already implemented** — SAF-035 delivers this without modification.
- **Consistent with fail-closed** — misidentification of a session boundary (e.g.,
  OTel file absent) falls back to a persistent UUID4, still shared across all agents
  in the workspace process.

### 4.2 Future: Per-Agent Tracking (deferred)

If VS Code Copilot extends the hook payload to include an agent identifier or
agent-type flag in a future release, per-agent tracking becomes feasible **within**
a shared budget:

- The session budget (e.g., 20) remains shared.
- Each agent additionally has a per-agent sub-budget (e.g., 10) to detect a single
  rogue subagent without attributing its violations to the legitimate main agent.

This enhancement should be implemented in a future SAF workpackage once the VS Code
payload schema exposes the necessary metadata. It is documented here for forward
planning but **not recommended for immediate implementation** because the payload
field does not yet exist.

### 4.3 Workflow Impact

For legitimate multi-agent development workflows using the default threshold of 20:
- The `search_subagent` tool itself is always allowed (in `_ALWAYS_ALLOW_TOOLS`) and
  never incurs a denial.
- Subagent-generated denials from policy violations accumulate in the shared counter,
  but 20 violations in a single session represents clearly problematic behaviour that
  warrants the lockout regardless of which agent generated them.
- Developers who regularly run multi-agent workflows with high task fan-out should
  raise the threshold via `counter_config.json` (implemented in SAF-036).

---

## 5. Documentation of Design Limitation

Per the WP acceptance criteria, the following limitation is explicitly documented:

**Separate per-subagent counters are not feasible with the current VS Code Copilot
hook payload schema.** The payload (`tool_name` + `input` fields) carries no
agent type, agent ID, parent session reference, or subagent flag. Until VS Code
exposes such metadata in the hook invocation, the gate cannot distinguish a main
agent from its subagents at the hook boundary. The shared-counter approach is
therefore not a design compromise — it is the only architecturally sound option
given current platform constraints.

---

## 6. Summary of Findings

| Question | Finding |
|----------|---------|
| Does VS Code distinguish main agents vs subagents in hook payloads? | **No.** The payload schema is identical (`tool_name` + `input`). No agent-type field exists. |
| Do subagents share the parent's session ID? | **Yes, in practice.** The OTel `session.id` / `gen_ai.conversation.id` is set per Copilot conversation, not per agent. Subagents inherit the same session context. |
| Can a rogue agent use subagents to bypass the counter? | **Not with a shared counter.** Options B and C would create exploitable bypass paths. Option A (current) closes this attack. |
| Recommended approach? | **Shared counter (Option A), as already implemented.** No code change to SAF-035/SAF-036 is required. |
| Is per-subagent tracking feasible? | **Not today.** Requires future VS Code hook payload extension. Documented for deferred implementation in a future SAF WP. |

---

## References

- `templates/coding/.github/hooks/scripts/security_gate.py` — `_get_session_id()`,
  `_read_otel_session_id()`, `_increment_deny_counter()` (SAF-035)
- `templates/coding/.github/hooks/scripts/counter_config.json` — configurable
  threshold and enable/disable flag (SAF-036)
- `docs/workpackages/SAF-035/dev-log.md` — original counter design decisions
- `docs/workpackages/SAF-036/dev-log.md` — counter configuration implementation
- OWASP Top 10 A01:2021 — Broken Access Control (subagent bypass risk framing)
- VS Code Copilot Chat Extension — Hook payload schema (public extensibility preview)
