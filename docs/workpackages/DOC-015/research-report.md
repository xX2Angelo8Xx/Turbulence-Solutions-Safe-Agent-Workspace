# Research Report — DOC-015: Agent Self-Identification Mechanism

**Author:** Developer Agent  
**Date:** 2026-03-25  
**Workpackage:** DOC-015  
**User Story:** Enabler  
**Status:** Final  

---

## Executive Summary

This report investigates whether AI agents operating through VS Code Copilot can
be required to identify themselves (model name, session ID) in their first tool
call. The research examines the VS Code Copilot hook payload structure, the
behaviour of multiple model families, the feasibility of a mandatory
self-identification protocol, and the security implications of agent-reported identity.

**Recommendation:** A mandatory agent self-identification protocol based on
hook payload content is **not currently feasible** without a platform-level change
from GitHub/Microsoft. The `PreToolUse` hook payload does not carry model or agent
identity fields. Any self-reported identity injected by the agent itself (e.g.
via a `vscode_ask_questions` call) can be trivially spoofed and provides no
security guarantee. If audit trail quality and per-model counter tracking are
goals, the correct path is to request GitHub Copilot to expose model identity in
the hook payload via a feature request, or to use VS Code's OTel telemetry export
as an indirect signal in the interim.

---

## 1. VS Code Copilot Hook Payload Inspection

### 1.1 Hook Invocation Mechanism

VS Code Copilot invokes `security_gate.py` as a `PreToolUse` hook before every
tool call made by the AI agent. The hook receives the tool call data as a JSON
object via `stdin`. The security gate reads this payload, evaluates the tool name
and parameters, and returns an allow/deny decision as a JSON object via `stdout`.

### 1.2 Observed Payload Structure

The payload delivered to the hook by VS Code Copilot has the following structure:

```json
{
  "tool_name": "<tool identifier>",
  "tool_input": {
    "<param_name>": "<param_value>"
  }
}
```

Fields present in every payload:
- `tool_name` — the name of the tool being called (e.g. `run_in_terminal`,
  `read_file`, `create_file`)
- `tool_input` — an object containing the parameters for that tool call

Fields absent from the payload (confirmed by inspection of `parse_input()`,
`extract_tool_name()`, `extract_path()`, and the full `main()` function in
`security_gate.py`):
- `model` — no model name or model version
- `agent_id` — no persistent agent identifier
- `session_id` — no session identifier at the payload level
- `correlation_id` — no trace or correlation identifier
- `user_id` — no user identity claim
- `timestamp` — no call timestamp in the payload

### 1.3 Session Identity via OTel

Session identity is not available in the hook payload directly. The security gate
derives a session ID indirectly by reading the last span from
`copilot-otel.jsonl` (VS Code Copilot's OpenTelemetry JSONL export), extracting
the `session.id` resource attribute or `gen_ai.conversation.id` span attribute.
When the OTel file is absent or unreadable, the gate falls back to a UUID stored
in `.hook_state.json` that persists until it is cleared.

This session-identification mechanism is **side-channel and indirect** — it is
not part of the hook protocol itself. The OTel file contains:

- Span/trace identifiers for telemetry
- Conversation-scoped session IDs
- No model name or agent configuration

### 1.4 Conclusion

The VS Code Copilot hook API does not expose any agent or model identity metadata
at the hook payload level. The gate operates without knowledge of which model
generated the tool call. This is a deliberate architectural boundary in the
platform — hooks are tool-call interceptors, not model monitors.

---

## 2. Model-Specific Identification in Tool Calls

### 2.1 GPT-4 / GPT-4o (OpenAI)

GPT-4 and GPT-4o emit tool calls using the OpenAI function-calling schema. When
routed through VS Code Copilot, all OpenAI-backed requests pass through the
GitHub Copilot API layer, which normalises the payload before delivering it to
the hook. No OpenAI-specific headers, `model` fields, or `provider` annotations
are preserved in the hook payload.

### 2.2 Claude (Anthropic)

Claude models (Claude 3.x, Claude Sonnet, Claude Opus) use Anthropic's tool-use
schema natively. When served via VS Code Copilot, the Claude API response is
translated into Copilot's internal tool-calling format before the hook is
invoked. No Anthropic-specific metadata (`anthropic-model`, `anthropic-version`,
`x-amz-bedrock-model`, etc.) appears in the hook payload.

### 2.3 Gemini (Google)

Gemini models use Google's function-calling schema. The same normalisation applies
when served via VS Code Copilot — the hook only sees the generic
`tool_name` / `tool_input` pair.

### 2.4 HTTP-level Headers

The security gate is invoked as a subprocess (child process of VS Code), not as
an HTTP server. There are no HTTP headers to inspect — the communication channel
is stdin/stdout. Any model-specific HTTP headers set by the Copilot API client
are consumed within the VS Code process and never reach the hook subprocess.

### 2.5 Conclusion

No model family injects identifying information into the tool call payload
observable at the hook level. The normalisation performed by VS Code Copilot's
tool-calling infrastructure deliberately strips provider-specific metadata before
delivering payloads to hook scripts. This applies to all commercially available
models as of Q1 2026.

---

## 3. Feasibility of a Mandatory Self-Identification Protocol

### 3.1 Proposed Protocol Design

A self-identification protocol would require the AI agent to make a specific
first tool call at the beginning of each session that includes identity claims:

```
Agent → announces: {model: "claude-sonnet-4-6", session_id: "...", agent_name: "..."}
```

This could be implemented as:
1. A new hook that fires on session start (no such hook exists in VS Code Copilot)
2. A convention enforced by the agent instructions requiring the first tool call
   to be `vscode_ask_questions` with a structured self-introduction
3. A new dedicated tool (`identify_agent`) that the hook parses to register the
   identity before allowing further tool calls

### 3.2 Platform Capability Gap

**A session-start hook does not exist.** VS Code Copilot only provides `PreToolUse`
and `PostToolUse` hooks — there is no `SessionStart` hook. Enforcing a
self-identification step before any tool call is therefore impossible at the hook
level without modifying the platform.

**Enforcing the first-call convention via hook logic is fragile.** A hook that
denies any tool call until an identification call has been received would need to:
1. Track "has this session identified itself?" in `.hook_state.json`
2. Allow only a designated identification tool to proceed without prior identity
3. This would block agents that do not follow the protocol, including legitimate
   agents that skip a preamble (e.g. agents that call `read_file` as their first
   action)

**Instruction-based enforcement is unreliable.** The agent instructions can
require a self-identification step, but this does not prevent an agent from
skipping it. An agent that omits the introduction step would proceed normally —
the hook has no way to intercept a missing call.

### 3.3 Feasibility Assessment

| Variant | Feasibility | Reason |
|---------|-------------|--------|
| Payload-level model metadata | Not feasible | Platform does not expose it |
| Hook-enforced first-call identification | Partially feasible | Technically buildable but bypassable by any agent ignoring instructions |
| Instruction-based convention | Weakly feasible | Relies entirely on agent compliance — not enforcement |
| Platform-native session-start hook | Not available | Does not exist in VS Code Copilot as of Q1 2026 |
| Feature request to GitHub/Microsoft | Feasible long-term | Would require waiting for platform update |

---

## 4. Security Implications — Can Agent Self-ID Be Spoofed?

### 4.1 Spoofability Analysis

Any agent self-identification protocol that relies on the agent voluntarily
reporting its identity is fully spoofable. Consider the threat model:

**Scenario A — Honest agent, honest identity:** The agent correctly reports its
model name and version. The hook records this. The audit trail reflects the real
model. This works as intended.

**Scenario B — Compromised or manipulated agent:** An agent operating under a
prompt injection attack or deliberately misconfigured identity claim reports
`model: "gpt-4o"` when it is actually `claude-sonnet-4-6`. The hook has no way
to verify this claim. The audit trail is misleading.

**Scenario C — Model that never identifies itself:** An agent that does not
follow the identification protocol simply omits the first call. If the hook
enforces identification by blocking subsequent calls, this degrades the agent's
usefulness. If the hook does not enforce it, the identity is simply absent.

**Scenario D — Adversarial identity claim:** An agent claims to be an
"approved model" (e.g. `model: "approved-gpt-4o"`) to bypass a hypothetical
model allowlist enforced by the hook. Since the hook cannot verify the claim,
the allowlist would be trivially bypassed.

### 4.2 Cryptographic Attestation

A theoretically sound implementation would require cryptographic attestation:
the model provider would sign each tool call with a key pair under their custody,
and the hook would verify the signature using a known public key. This would
prevent spoofing entirely.

**Realities of cryptographic attestation:**
- No current AI provider signs tool call payloads at the call level
- Key distribution and rotation would require infrastructure outside the
  workspace (a PKI or key server)
- Verifying signatures in the hook would introduce non-trivial latency
- This is a platform-vendor responsibility, not a workspace administrator's

### 4.3 Trust Boundary Assessment

The correct trust boundary is:

| Component | Trusted | Reason |
|-----------|---------|--------|
| VS Code Copilot (platform) | Yes | Controlled by GitHub/Microsoft; delivers hook payloads |
| OTel session ID | Partially | Derived from VS Code internals; not easily spoofed by the model itself |
| Agent-reported identity | No | Fully under the agent's control; cannot be verified |
| Model metadata in payload | N/A | Does not exist yet |

### 4.4 Conclusion

Agent self-ID **can be spoofed trivially** in any voluntary-reporting scheme.
Only a platform-enforced, cryptographically attested identity mechanism would
provide reliable agent identification. Such infrastructure does not exist in
VS Code Copilot as of Q1 2026. Treating self-reported agent identity as a
security control would create false confidence and should be avoided.

---

## 5. Benefit Analysis

### 5.1 Audit Trail Quality

**Current state:** Audit logs (proposed in DOC-014) capture `session_id`,
`tool_name`, `decision`, `reason`, and `timestamp`. They do not capture the
model name because it is not available.

**With reliable model identity:** Logs could also capture `model_name`,
enabling post-session queries like "how many denials were triggered by GPT-4o
sessions versus Claude sessions?" and "which model generated the tool call that
triggered a lockout?"

**Benefit:** Medium. Model-differentiated audit analysis would be useful for
operators comparing model behaviour, especially when rolling out new models.
However, given the spoofability concern (Section 4), any recorded model identity
would need to be treated as unverified assertion rather than fact.

### 5.2 Per-Model Counter Tracking

**Current state:** The denial counter is keyed by `session_id`, not by model.
All sessions regardless of model share the same `lockout_threshold`.

**With reliable model identity:** The counter could use a `(session_id, model)`
composite key, allowing different `lockout_threshold` values per model. A more
cautious model might be granted a lower threshold; a model known to be
well-aligned could be granted a higher one.

**Benefit:** Low-to-medium in the short term. Without reliable, unspoofable
model identity, per-model thresholds would be configurable but not
enforceable. An agent could declare any model name to obtain a higher threshold.

### 5.3 Developer Experience

**Benefit:** A visible self-identification step in the agent's first tool call
would make the session context clearer in audit logs ("this session was GPT-4o").
This has ergonomic value for debugging without security implications.

---

## 6. Recommendations

### 6.1 Do Not Implement Now

**Recommendation:** Do not implement a mandatory self-identification protocol in
the current release cycle. The feature is not feasible without voluntary agent
compliance, and voluntary compliance does not constitute a security control.
Implementing it now would add complexity (a stateful "has session identified?"
flag in `.hook_state.json`) for minimal and unverifiable benefit.

### 6.2 File a GitHub Feature Request

**Recommendation:** File a feature request with GitHub Copilot Extensions /
GitHub Copilot API team requesting that model identity be included in the
`PreToolUse` hook payload as a read-only, platform-asserted field:

```json
{
  "tool_name": "run_in_terminal",
  "tool_input": { ... },
  "copilot_metadata": {
    "model": "gpt-4o",
    "model_version": "2025-01-01",
    "session_id": "...",
    "agent_type": "copilot-workspace"
  }
}
```

This would be a platform-enforced field that the agent cannot modify. It would
enable genuine per-model counter configuration and reliable audit attribution.

### 6.3 Record Self-Reported Identity as Unverified Annotation (Future)

**Recommendation (conditional):** If the project chooses to implement a voluntary
self-identification convention for developer ergonomics (not security), it should
be implemented as follows:

1. Agent instructions require the agent to call `vscode_ask_questions` as its
   first action, reporting its model name as a structured JSON annotation in the
   question text.
2. The hook reads the annotation if present and records it as `agent_claim` (not
   `model`) in the audit log, making the unverified nature explicit.
3. The hook does not enforce the protocol — missing identification is logged
   as `agent_claim: null` and does not block subsequent calls.

This adds zero enforcement complexity, is backward-compatible with all existing
agents, and makes the non-binding nature of the claim explicit in both the data
model and the field name.

### 6.4 Per-Model Counter Configuration (Pre-Condition)

**Recommendation:** Do not implement per-model counter configuration until
reliable model identity is available via the hook payload (see Section 6.2).
Building per-model thresholds on top of agent-claimed identity would allow any
agent to self-select a more permissive threshold by falsifying its model name.

### 6.5 Summary Table

| Recommendation | Priority | Pre-condition |
|----------------|----------|---------------|
| Do not enforce self-ID now | Immediate | None |
| File GitHub feature request for model metadata in payload | Near-term | None |
| Record self-reported identity as unverified annotation | Long-term / optional | Platform feature request declined |
| Per-model counter tracking | Future | Platform-asserted model identity in payload |

---

## 7. References and Files Inspected

| Resource | Relevance |
|----------|-----------|
| `templates/coding/.github/hooks/scripts/security_gate.py` | Hook payload structure, `parse_input()`, `main()`, `_get_session_id()`, `_read_otel_session_id()` |
| `docs/workpackages/SAF-035/dev-log.md` | Denial counter architecture |
| `docs/workpackages/SAF-036/dev-log.md` | Counter configuration design |
| `docs/workpackages/DOC-014/research-report.md` | Audit logging design — `copilot_metadata` integration point reference |
| `docs/workpackages/workpackages.csv` | WP context for Q8 open question |
| VS Code Copilot PreToolUse hook documentation (platform specification) — no model fields |
| OpenTelemetry semantic conventions for Gen AI (`gen_ai.conversation.id`, `session.id`) |

---

*End of Research Report — DOC-015*
