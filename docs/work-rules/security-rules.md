# Security Rules

Non-negotiable security requirements for all contributors and agents.

---

## Absolute Rules

1. **No secrets, credentials, or API keys in source code — ever.** Use environment variables or secure vaults.
2. **Validate all external inputs at system boundaries** — user input, file paths, JSON from VS Code hooks, CLI arguments.
3. **Never disable, bypass, or weaken safety controls**, even temporarily.
4. **Never use absolute paths in code or documentation.** Use relative paths only.
5. **Never reference documents outside this repository** that may be altered independently.

## Safety-First Mandate

This project has the highest security classification. Every decision — code, config, architecture — must prioritize safety over convenience. When in doubt, choose the more restrictive option.

## Secure Coding Practices

- Prefer failing **closed** (deny) over failing **open** (allow) in all security decisions.
- Sanitize all file paths — normalize, resolve symlinks, and reject path traversal attempts.
- Never trust tool call parameters without validation.
- Do not log sensitive data (credentials, tokens, personal information).
- Do not use `eval()`, `exec()`, or equivalent dynamic code execution unless explicitly approved and sandboxed.

## Restricted Zones

Within `templates/agent-workbench/`, the following directories are off-limits:

| Zone | Access | Reason |
|------|--------|--------|
| `.github/` | Blocked | Hook scripts, Copilot config — administrator only |
| `.vscode/` | Blocked | VS Code security settings — administrator only |
| `NoAgentZone/` | Blocked | Sensitive files — hard-denied by PreToolUse hook |

Only access these zones if explicitly required by your assigned workpackage.

## Security Testing

- All security-critical code requires both a **protection test** (validates the control works) and a **bypass-attempt test** (verifies the control cannot be circumvented).
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
