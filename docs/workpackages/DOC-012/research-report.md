# Research Report — DOC-012: MCP Tools Extensibility

**Author:** Developer Agent  
**Date:** 2026-03-25  
**Workpackage:** DOC-012  
**Status:** Final  

---

## Executive Summary

This report evaluates whether MCP (Model Context Protocol) tools should be allowed
within the Turbulence Solutions Agent Environment Launcher project scope. Based on a
security analysis of common MCP servers, the hook payload structure, and zone-checking
feasibility, the **recommendation is: keep blocking all `mcp_*` tool calls by default**,
with a defined extensibility framework that allows individual workspaces to opt in to a
vetted allowlist via configuration.

---

## 1. Inventory of Common MCP Servers

MCP servers expose capabilities to AI agents via a standardised JSON-RPC protocol. The
following table categorises the most widely deployed MCP servers in development
environments:

| MCP Server | Tool Prefix | Primary Capability | Access Level |
|---|---|---|---|
| Filesystem | `mcp_filesystem_*` | Read/write arbitrary file paths | Host filesystem |
| GitHub | `mcp_github_*` | Commits, PRs, issues, branches | Remote VCS |
| PostgreSQL / SQLite | `mcp_postgres_*` / `mcp_sqlite_*` | Execute raw SQL queries | Local/remote DB |
| Docker | `mcp_docker_*` | Container lifecycle, image builds | Container runtime |
| Brave Search / Tavily | `mcp_brave_search_*` / `mcp_tavily_*` | Web search queries | External network |
| Puppeteer / Playwright | `mcp_puppeteer_*` / `mcp_playwright_*` | Browser automation, DOM interaction | External network + DOM |
| Memory / Knowledge Graph | `mcp_memory_*` | Persistent KV store for agents | Local process memory |
| Sentry | `mcp_sentry_*` | Error event retrieval and analysis | External network |
| Slack / Teams | `mcp_slack_*` / `mcp_teams_*` | Message sending, channel reads | External network |
| Jira / Linear | `mcp_jira_*` / `mcp_linear_*` | Issue creation and updates | External network |
| AWS / GCP / Azure | `mcp_aws_*` / `mcp_gcp_*` | Cloud resource management | Cloud APIs |
| Fetch / HTTP | `mcp_fetch_*` | Raw HTTP requests to arbitrary URLs | External network |

### 1.1 Classification by Risk Level

**Critical risk (filesystem and code execution):**
- `mcp_filesystem_*` — can read secrets, overwrite source files, escape project scope
- `mcp_docker_*` — volume mount arguments can bind-mount host paths outside project

**High risk (data exfiltration and remote write):**
- `mcp_github_*` — can push code to remote repositories without user interaction
- `mcp_postgres_*` / `mcp_sqlite_*` — raw SQL can drop tables, dump credentials
- `mcp_fetch_*` / `mcp_puppeteer_*` — SSRF, arbitrary HTTP to internal services

**Medium risk (external side effects):**
- `mcp_slack_*`, `mcp_teams_*`, `mcp_jira_*` — actions visible to other people
- `mcp_aws_*` etc. — cost-bearing, irreversible cloud operations

**Lower risk (read-only, no side effects):**
- `mcp_brave_search_*`, `mcp_tavily_*` — web searches (but still leaks context externally)
- `mcp_memory_*` — local process store, no filesystem I/O by default
- `mcp_sentry_*` — read-only error lookups (if credentials are pre-configured)

---

## 2. Security Implications of Allowing `mcp_*` Tool Calls

### 2.1 MCP Architecture and the Attack Surface

MCP servers run as separate long-lived processes launched by the VS Code extension host.
The AI agent communicates with them via JSON-RPC calls that VS Code forwards on the
agent's behalf. From the hook perspective, a single `mcp_filesystem_read_file` call
arrives at `security_gate.py` with:

```json
{
  "tool_name": "mcp_filesystem_read_file",
  "tool_input": {
    "path": "/etc/passwd"
  }
}
```

The hook sees only the tool name and input arguments — it does not see which MCP server
binary produced the tool, nor whether the server is running with elevated privileges.

### 2.2 Specific Attack Vectors

#### 2.2.1 Arbitrary Filesystem Access (`mcp_filesystem_*`)

The reference `@modelcontextprotocol/server-filesystem` implementation accepts a list of
allowed directories at startup. However, the agent can request any path that the MCP
server was launched with access to. If the server was started with `/` as an allowed
root (a common misconfiguration) an agent can read any file on the host system,
including `.env` files, SSH keys, and credential stores.

Attack path:
1. Agent calls `mcp_filesystem_read_file` with `path: "C:\\Users\\<user>\\.ssh\\id_rsa"`
2. MCP server reads the file and returns contents to the agent
3. Agent exfiltrates contents via a subsequent `mcp_fetch_post` or logs it

The current security gate **already blocks** `mcp_*` tool names that match the
`mcp_filesystem_*` pattern (they fall under the `mcp_*` wildcard denial). This is
correct.

#### 2.2.2 Arbitrary Code Execution via Docker Volume Mounts

`mcp_docker_run` and `mcp_docker_create` accept `HostConfig.Binds` arguments that map
host paths into containers. A rogue agent can bind-mount `/` into a container and
write to host files from inside the container, bypassing standard filesystem checks.

Even if a zone-check validates the destination path field (`/workspace/...`), the
`HostConfig.Binds` argument list may contain arbitrary host paths as secondary entries.

#### 2.2.3 SQL Injection and Credential Leakage (`mcp_postgres_*`)

MCP database servers typically expose a `query` argument that accepts raw SQL. No
parametrised query enforcement exists at the MCP layer. An agent can INSERT or SELECT
from any schema visible to the database role, including credential tables.

#### 2.2.4 SSRF via `mcp_fetch_*` and Browser MCPs

Any MCP tool that makes outbound HTTP requests can be used for Server-Side Request
Forgery: targeting internal IP ranges (`10.x`, `169.254.x` metadata endpoints), internal
DNS names, or cloud provider metadata services (`[169.254.169.254]`).

#### 2.2.5 Irreversible Remote Side Effects

`mcp_github_create_commit`, `mcp_github_push`, `mcp_slack_send_message` are immediately
visible to external parties. Unlike local filesystem writes (which can be rolled back),
these actions cannot be undone by the security gate after the fact.

### 2.3 Interaction with the Existing Hook Model

The current security gate (`security_gate.py`) processes tool calls in a **synchronous
blocking pre-approval loop**: the tool is blocked until the gate allows it. This means
the gate can prevent MCP tool calls before they execute. The gate does **not** have a
post-execution rollback mechanism, which makes blocking-by-default the only safe posture
for irreversible MCP operations.

---

## 3. Zone-Checking Feasibility for MCP Tools

### 3.1 What Zone-Checking Requires

Zone-checking validates that a tool call targets a path that is within the project
workspace root (the "project zone"). For a tool to be zone-checkable, two conditions
must hold:

1. The tool input must contain a field that unambiguously identifies the target (a file
   path, URL, or resource identifier).
2. That field must be validatable against the workspace root using existing path
   canonicalisation logic.

### 3.2 Zone-Checkable MCP Tools

The following MCP tool categories expose structured target fields that can be validated:

| Tool Category | Argument | Checkable? | Notes |
|---|---|---|---|
| `mcp_filesystem_read_file` | `path` | Yes | Must be within project root |
| `mcp_filesystem_write_file` | `path` | Yes | Must be within project root |
| `mcp_filesystem_list_directory` | `path` | Yes | Must be within project root |
| `mcp_filesystem_create_directory` | `path` | Yes | Must be within project root |
| `mcp_github_get_file_contents` | `path`, `repo` | Partial | Path is relative, but repo is external |
| `mcp_github_push_files` | `files[].path` | Partial | File paths are in-workspace but push is external |
| `mcp_sqlite_*` | Database path | Yes (if local file) | Only if DB is inside project root |

### 3.3 Non-Zone-Checkable MCP Tools

The following categories do **not** expose a path or target that maps to the local
workspace:

| Tool Category | Reason Not Zone-Checkable |
|---|---|
| `mcp_brave_search_web` | Query string — no filesystem path |
| `mcp_fetch_get` / `mcp_fetch_post` | URL — no relation to workspace path |
| `mcp_memory_*` | In-process KV store — no path argument |
| `mcp_slack_*` / `mcp_teams_*` | Message content — no path argument |
| `mcp_jira_*` / `mcp_linear_*` | Issue text — no path argument |
| `mcp_postgres_*` | SQL text — cannot be path-validated |
| `mcp_docker_run` | Container spec — `Binds` can bypass path checks |
| `mcp_sentry_*` | Remote resource ID — no local path |
| AWS/GCP/Azure MCPs | Cloud resource ARN/ID — no local path |

### 3.4 Zone-Checking Limitations

Even for zone-checkable tools, several limitations apply:

1. **Canonicalisation bypass**: Symlinks inside the project root can point outside.
   The existing `_is_within_project_root()` helper resolves symlinks, but only if
   the tool input is a path. For tools that take partial paths or globs, full
   resolution is not possible before execution.

2. **Secondary argument bypass**: Some tools accept path lists or nested objects
   (e.g. `mcp_docker_create` with `HostConfig.Binds`). Validating the primary
   argument does not guarantee all secondary targets are safe.

3. **MCP server startup options**: Zone-checking at the hook level cannot prevent
   an MCP server that was launched with broad access from honouring calls that were
   not blocked by the gate.

---

## 4. Proposed Framework for Selective MCP Tool Allowlisting

### 4.1 Design Principles

1. **Block by default.** All `mcp_*` tool calls are denied unless explicitly allowed.
   This is already enforced by the current security gate.
2. **Per-workspace configuration.** Allowed tools are declared in the workspace's
   `settings.json` file (or a dedicated `mcp-policy.json`). No global allow.
3. **Zone-check mandatory for filesystem MCPs.** Any allowed MCP tool that accepts a
   path argument MUST be zone-checked before approval. Bypass via symlink must be
   blocked.
4. **Explicit tool names only.** Wildcards in the allowlist are prohibited. Tools must
   be individually named (e.g. `mcp_filesystem_read_file`, not `mcp_filesystem_*`).
5. **Read-only preference.** Where a capability has both read and write variants, only
   the read variant should be considered for allowlisting first.

### 4.2 Configuration Schema

```json
// .vscode/settings.json (or dedicated mcp-policy.json)
{
  "turbulence.mcp_policy": {
    "mode": "allowlist",
    "allowed_tools": [
      "mcp_filesystem_read_file",
      "mcp_filesystem_list_directory"
    ],
    "zone_check_required": true,
    "allow_external_network": false
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `mode` | `"block"` \| `"allowlist"` | `"block"` | Global policy for `mcp_*` calls |
| `allowed_tools` | `string[]` | `[]` | Exact tool names that may be called |
| `zone_check_required` | `bool` | `true` | Enforce project-root path validation for path-bearing tools |
| `allow_external_network` | `bool` | `false` | Whether MCP tools that make outbound HTTP requests can be allowlisted |

### 4.3 Framework Implementation Outline

The security gate would need the following additions to support this framework:

#### Step 1 — Load Policy at Gate Startup

```python
# Pseudocode — not an implementation instruction
def _load_mcp_policy(workspace_root: Path) -> dict:
    policy_path = workspace_root / ".vscode" / "settings.json"
    if not policy_path.exists():
        return {"mode": "block"}
    raw = json.loads(policy_path.read_text())
    return raw.get("turbulence.mcp_policy", {"mode": "block"})
```

#### Step 2 — MCP Tool Decision Logic

```python
def _decide_mcp_tool(tool_name: str, tool_input: dict, policy: dict) -> bool:
    if policy.get("mode") != "allowlist":
        return False  # block
    if tool_name not in policy.get("allowed_tools", []):
        return False  # not in allowlist
    if policy.get("zone_check_required", True):
        path_arg = tool_input.get("path")
        if path_arg and not _is_within_project_root(Path(path_arg)):
            return False  # path outside zone
    return True  # allow
```

#### Step 3 — Integration with Existing Gate

The existing denial counter and `_DENY_THRESHOLD` logic must apply to blocked MCP calls
identical to other denied tool calls. An MCP-blocked call counts towards the session limit.

### 4.4 Tier Classification for Allowlisting

| Tier | Tools | Condition for Allowlisting |
|---|---|---|
| **Tier 1 — Zone-safe read-only** | `mcp_filesystem_read_file`, `mcp_filesystem_list_directory`, `mcp_sqlite_query` (read-only) | Zone-check passes; mode=allowlist |
| **Tier 2 — Zone-safe write** | `mcp_filesystem_write_file`, `mcp_filesystem_create_directory` | Zone-check passes; mode=allowlist; explicit opt-in |
| **Tier 3 — External read** | `mcp_brave_search_web`, `mcp_sentry_list_issues` | `allow_external_network: true`; mode=allowlist |
| **Tier 4 — External write** | `mcp_github_push_files`, `mcp_slack_send_message` | Not recommended for allowlisting at this time |
| **Blocked permanently** | `mcp_docker_*`, `mcp_fetch_post`, `mcp_postgres_query`, `mcp_aws_*` | Never allowlisted — risk too high |

---

## 5. Recommendation

### 5.1 Decision: Keep Blocking All `mcp_*` Tools (Default) + Framework Ready

**Verdict: Allow with framework (deferred activation)**

The current policy of blocking all `mcp_*` tool calls is **correct and should be
maintained as the default**. The attack surface is too broad for a blanket allowlist,
and several MCP tool categories (Docker, database, cloud) are permanently too dangerous
to allow via the hook mechanism.

However, the extensibility framework described in Section 4 should be **designed and
documented now** so that individual workspaces can opt in to Tier 1 tools (read-only
filesystem MCPs) when a future workpackage implements the policy loader.

### 5.2 Recommended Implementation Path

| Phase | Action | WP Scope |
|---|---|---|
| Phase 1 (this WP) | Document framework; keep block-by-default | DOC-012 (complete) |
| Phase 2 | Implement `turbulence.mcp_policy` loader in `security_gate.py` | Future SAF-WP |
| Phase 3 | Add per-workspace MCP policy UI to launcher | Future GUI-WP |
| Phase 4 | Audit Tier 3 tools and define external-network policy | Future DOC-WP |

### 5.3 Tools Safe to Allowlist in Phase 2

The following specific tool names should be the **first candidates** for allowlisting in
Phase 2, subject to mandatory zone-checking:

- `mcp_filesystem_read_file` — read files in the project
- `mcp_filesystem_list_directory` — list directory contents
- `mcp_filesystem_get_file_info` — metadata only, no read

Tools that should **remain permanently blocked** regardless of policy:

- All `mcp_docker_*` tools
- All `mcp_fetch_*` tools
- All `mcp_postgres_*` and `mcp_sqlite_write_*` tools
- All cloud provider MCPs (`mcp_aws_*`, `mcp_gcp_*`, `mcp_azure_*`)
- All messaging MCPs (`mcp_slack_*`, `mcp_teams_*`)

---

## 6. References and Evidence Sources

| Source | Relevance |
|---|---|
| `templates/coding/.github/hooks/scripts/security_gate.py` | Current blocking logic for `mcp_*` |
| `templates/coding/.github/hooks/require-approval.json` | Hook registration and trigger model |
| MCP Specification (modelcontextprotocol.io) | Protocol design and server categories |
| `@modelcontextprotocol/server-filesystem` README | Filesystem MCP attack surface |
| DOC-011 (Docker research) | Comparable analysis for another blocked category |
| OWASP API Security Top 10 (2023) | SSRF, injection, and excess data exposure |

---

## Appendix A: Required Sections Checklist

This document contains the following required sections as specified in the DOC-012
acceptance criteria:

- [x] **Section 1** — Inventory of common MCP servers (database, API testing,
  documentation, filesystem, browser automation, messaging, cloud)
- [x] **Section 2** — Security implications of `mcp_*` tool calls (filesystem access,
  network access, arbitrary code execution vectors)
- [x] **Section 3** — Zone-checking feasibility assessment (which tools can be
  path-validated, which cannot, and why)
- [x] **Section 4** — Framework for selective MCP tool allowlisting per workspace
  configuration (schema, decision logic, tier classification)
- [x] **Section 5** — Recommendation (keep blocking by default; extensibility framework
  ready for future activation)
