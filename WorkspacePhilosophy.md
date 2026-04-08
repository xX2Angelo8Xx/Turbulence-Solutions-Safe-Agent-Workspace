# Safe Agent Environment — Security Philosophy

**Turbulence Solutions | April 2026**

---

## 1. Premise

This document is the north star for security design decisions in the Safe Agent
Environment (SAE). It does not describe current implementation state — it describes
what the design *should* aim for and why. Read this before opening any workpackage
that touches security policy, the security gate, or template configuration.

---

## 2. The Honest Threat Model

Security design must start with an honest picture of what can and cannot be
prevented.

### 2.1 The Primary Risk: Script Bypass

An agent that can **write a file** and then **execute it** can bypass every
tool-level restriction. Once a Python script exists inside the project folder, the
agent can run it — and that script has the same OS permissions as the VS Code
process itself. No pattern matching, no zone classifier, and no denial counter
prevents this.

This is not a theoretical edge case. Any agent mode session that needs to run tests,
build scripts, or debug tooling will write and execute scripts. **This is normal and
necessary.** The bypass is inherent to the capability.

**Conclusion:** Tool-call restrictions alone cannot prevent a determined or
compromised agent from acting outside the project folder. Accepting this is the
foundation of sound security design.

### 2.2 OS-Level Sandboxing: Not Available on Windows

VS Code's built-in terminal sandbox (`chat.tools.terminal.sandbox`) restricts file
system access at the OS level via `macFileSystem`. This works only on macOS. On
Windows — the platform used by approximately 95% of the target user base —
**no OS-level containment exists**. The setting has no meaningful effect on Windows.

**Conclusion:** The security gate (PreToolUse hook) is the only technical barrier on
Windows. Its limits must be understood and designed around, not papered over.

### 2.3 What Agents Actually Do

Normal agents, including those affected by prompt injection:

- Do not spontaneously explore the host file system for personal data.
- Do not randomly delete files outside context.
- Do follow instructions given in the prompt — including injected ones.
- Can be confused by bad prompts into taking unintended but plausible actions.

The realistic failure modes are therefore:

| Failure mode | Likelihood | Severity |
|---|---|---|
| Accidental damage from bad/ambiguous prompt | High | Medium |
| Prompt injection → targeted destructive action | Low | High |
| Prompt injection → data exfiltration via script | Very low | Very high |
| Fully autonomous rogue agent ignoring all context | Negligible | Extreme |

Security controls should be sized to the realistic distribution, not the extreme tail.

---

## 3. What Security Controls Are Worth Having

### Genuine value

| Control                                           | What it actually prevents                                                           |
|---------------------------------------------------|-------------------------------------------------------------------------------------|
| Zone enforcement (deny writes outside `Project/`) | Accidental writes to `.github/`, `.vscode/`, and system paths via direct tool calls |
| Protecting `.github/hooks/` from read/write       | Prevents the security gate from being silently replaced via tool calls              |
| Audit log of every tool call                      | Forensic trail; detects patterns of suspicious behaviour after the fact             |
| Denial counter (session lock after N denials)     | Limits the blast radius of a looping or misbehaving agent                           |
| Blocking obfuscated terminal commands             | Friction against low-sophistication injection attempts; not a hard wall             |
| `vscode_askQuestions` for destructive operations  | The most cost-effective control — stops accidental irreversible actions             |

### Limited or no value on Windows

| Control | Why it is limited |
|---|---|
| `chat.tools.terminal.sandbox` | No effect on Windows (macOS-only) |
| Obfuscation regex patterns (28+) | Bypassed trivially by writing a script; maintenance cost exceeds benefit |
| Self-integrity hash of `security_gate.py` | Verification runs inside the file being verified; a bypass script need not call it |
| `NoAgentZone` + `search.exclude` | Useful convention, not hard enforcement |

---

## 4. Decision Framework: BLOCK / ASK / ALLOW

This is the policy specification. Implementation must conform to it.

### BLOCK — Hard deny, no override

These actions are blocked unconditionally by the security gate, always.

- **Write to any path outside the workspace root** — via any direct file tool
- **Write to `.github/`** — including `.github/hooks/` (the gate itself)
- **Write to `.vscode/`**
- **Write to `NoAgentZone/`**
- **Read from `.github/hooks/`** — the security gate code is not agent-readable
- **Obfuscated terminal commands** — Base64-encoded PowerShell, `invoke-expression`,
  pipe-to-interpreter patterns. These are obvious attack vectors with no legitimate use.
- **Command-line interpreters invoked inline** (e.g. `perl -e`, `ruby -e`, `php -r`,
  `bash -c` with embedded payloads) — no legitimate workflow requires these

**Rationale:** These blocks have near-zero false positive rate and meaningful
deterrent value even accounting for the script bypass.

### ASK — Require explicit user confirmation

These actions pause execution and require the user to approve via chat before
continuing. They are not blocked by default because they have legitimate uses —
but they are irreversible or high-impact enough that an accidental or injected
invocation could cause significant damage.

- **File deletion** — any `rm`, `Remove-Item`, `del`, or equivalent targeting
  files outside the current project. Deletion inside `Project/` may be
  auto-approved but should be logged.
- **`git reset --hard`** — discards uncommitted work irreversibly
- **`git push --force` / `--force-with-lease`** — rewrites remote history
- **Dropping or truncating database tables**
- **Any terminal command whose resolved working directory is outside the workspace**
- **Network calls that write data to external services** (e.g. webhook POST with payload)

**Implementation note:** "ASK" is implemented via hook triggering "Ask" directly in the Vs Code Chat. This is the highest-ROI security control in the system.

### ALLOW — Auto-approve

These actions are permitted without interruption. Speed matters; unnecessary
friction kills productivity.

- All file reads anywhere within the workspace
- File writes within `Project/`
- Standard terminal commands within the workspace (`python`, `pytest`, `pip install`,
  `git add`, `git commit`, `git status`, `git log`, `git diff`, `git checkout`,
  `git stash`, `npm`, `cargo`, etc.)
- Script creation and execution within `Project/` — **this is an explicit allow**,
  acknowledging that the script bypass exists and that blocking it would break all
  productive workflows
- Reading agent-facing `.github/` subdirectories (`.github/agents`, `.github/skills`,
  `.github/prompts`, `.github/instructions`)

---

## 5. Template Philosophy

All three templates ship the same security gate and the same core VS Code settings.
**Security is not a differentiator between templates.** What differs is workflow
structure and available agent scaffolding.

| | clean-workspace | agent-workbench | certification-pipeline |
|---|---|---|---|
| Security gate | Same | Same | Same |
| VS Code settings | Same | Same | Same |
| Agent scaffolding | None | Full | Full + structured process |
| Custom agents | None | Yes | Yes |
| Workflow rules | None | Minimal | Spec-driven (strict) |
| Intended use | Exploration / quick tasks | General development | Production software |

**Do not create template-specific security variants.** A user in `clean-workspace`
is not intrinsically safer than one in `certification-pipeline`. The risk comes from
the operator and the prompts, not the template.

---

## 6. Design Principles for Future Work

These principles resolve ambiguity in security workpackage design.

**P1 — Be honest about what is blocked.**
Documentation and instruction files must accurately describe what the gate prevents.
Do not claim a control prevents something it cannot prevent.

**P2 — Prefer human approval over hard blocks for reversible situations.**
A hard block that fires frequently trains users to disable or circumvent the gate.
An ASK that fires rarely is taken seriously.

**P3 — Keep the gate small and auditable.**
Every line of `security_gate.py` is a line that can break, drift, or be exploited.
Prefer fewer, cleaner rules over comprehensive pattern libraries.

**P4 — The audit log is the long-term safety net.**
Even if an agent bypasses restrictions via a script, the audit log records every
tool call that led there. Invest in log quality and retention.

**P5 — Do not design for the extreme tail.**
A fully autonomous rogue agent with adversarial intent is outside the scope of what
a workspace-level hook can prevent. Design for the realistic failure modes (P2.3).
Accept residual risk for the tail and document it.

**P6 — Windows is the primary platform.**
Every security control must be evaluated against its Windows behavior. macOS-only
features are supplemental, not foundational.

**P7 — Script execution is a legitimate capability, not a threat.**
Do not add complexity attempting to inspect or restrict script content. This does not
scale and breaks legitimate workflows. Trust the operator's choice to deploy the SAE;
inspect outputs via the audit log.

---

## 7. Open Questions (to be resolved in future workpackages)

- **Windows containment gap:** Is there a viable Windows-compatible containment
  mechanism (e.g. AppContainer, Job Objects, Windows Sandbox) that can be integrated
  as an optional layer without requiring admin privileges? This is the highest-priority
  unresolved security gap.
- **Simplification of obfuscation patterns:** Which of the 28 patterns catch real
  attack attempts in practice (evidenced by audit log data)? The rest should be
  removed.
- **ASK implementation:** The current gate can only BLOCK or ALLOW. Implementing ASK
  requires a mechanism to pause execution and resume after user input. This is a
  non-trivial infrastructure requirement that needs a dedicated workpackage.
- **Scope of the denial counter:** Is the session lock providing measurable value, or
  is it primarily friction for power users? Review audit data before next iteration.
