# DOC-011 — Research Report: Docker/Container Support Feasibility

**WP:** DOC-011  
**Status:** Complete  
**Branch:** `DOC-011/docker-research`  
**User Story:** US-036 — Expand the Allowed Terminal Command Set  
**Date:** 2026-03-25  

---

## Executive Summary

This report assesses whether AI agents should be permitted to run `docker` and
`docker-compose` commands inside the project folder. After evaluating the attack
surface, path-checking feasibility, Docker socket requirements, and safe-subset
options, the recommendation is:

> **DEFER — Do not allow Docker commands in the current security architecture.**
> A conditional allow path is documented in Section 6 for a future workpackage
> to implement if the risk trade-off is accepted.

---

## 1. Attack Surface Analysis

Docker commands executed by an AI agent introduce a qualitatively different threat
profile compared to ordinary shell commands. The threats are grouped into four areas.

### 1.1 Container Escape

A container escape allows a process inside a container to gain access to the host
operating system. The most common vectors are:

- **Privileged containers** (`docker run --privileged`): grants the container all
  host Linux capabilities and access to host devices. A single `--privileged` flag
  nullifies almost every other control. An agent constructing a `docker run` call
  could inject this flag.
- **Capability injection** (`--cap-add`): specific capabilities such as
  `CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, and `CAP_SYS_PTRACE` each enable
  well-documented escape paths. The full set of dangerous capabilities cannot be
  exhaustively enumerated; new kernel-level exploits add to the list over time.
- **Kernel namespace escapes**: cgroup, namespace, and seccomp misconfigurations
  in the Docker daemon itself allow container breakout independently of the flags
  the agent supplies.
- **Runtime vulnerabilities**: `runc` and `containerd` have had critical CVEs
  (e.g. CVE-2019-5736, CVE-2024-21626) that allow container escape regardless of
  image content. The host Docker version cannot be controlled by the safety gate.

**Blocking assessment:** `--privileged` and known dangerous `--cap-add` values
can be blocklisted, but the tail risk of unknown escape vectors is non-zero and
non-enumerable.

### 1.2 Volume Mounts to Host

Volume mounts (`-v` / `--volume` / `--mount`) copy host filesystem paths into the
container. Even with project-folder path-checking (see Section 2), the following
residual risks remain:

- **Sensitive files inside the project folder**: the project folder contains
  `.github/hooks/` scripts, `.vscode/settings.json`, the pre-tool-use hook binary,
  and potentially `.env` variants. A container could read, copy, or exfiltrate these
  even if the volume source is technically inside the project folder.
- **Symlink traversal**: if a symlink inside the project folder points outside it,
  a volume mount targeting the symlink will resolve to the external path,
  bypassing the project-folder check. Resolving and re-checking symlinks at
  hook time adds determinism but not completeness.
- **Built image layers**: a `docker build` step can `COPY` files from the build
  context into a layer, then a subsequent `docker run` can exfiltrate them over
  the network or mount-and-read them from a sibling container.
- **Implicit mounts**: `docker-compose` YAML files can declare `volumes:` entries.
  The agent would need to parse all compose files referenced in the command to
  validate mounts — substantially more complex than CLI flag checking.

### 1.3 Network Access

Docker containers have unrestricted outbound network access by default. An agent
running a container could:

- Exfiltrate project files or secrets to an external endpoint inside a container
  that appears benign from the CLI invocation.
- Pull untrusted image layers from public registries at runtime, importing
  arbitrary code into the execution environment.
- Bridge the project network to external infrastructure (`--network host` gives
  the container the host's full network stack, including access to localhost
  services and cloud metadata endpoints such as `169.254.169.254`).

**Blocking assessment:** `--network host` can be blocked. General outbound access
from containers cannot be controlled at the CLI level without a separate Docker
network policy layer (not present in this project).

### 1.4 Privilege Escalation

- **Docker daemon socket** (`/var/run/docker.sock`): any process with access to
  the socket can create new containers, including privileged ones with arbitrary
  volume mounts. If the socket is exposed inside a container, that container
  effectively gains root on the host. This is one of the most severe and most
  frequently exploited Docker misconfigurations.
- **Rootless Docker**: mitigates many privilege escalation paths but is not the
  default installation mode on Windows or most Linux systems. The safety gate
  cannot rely on the host running rootless Docker.
- **Windows specifics**: on Windows, Docker operates via the WSL 2 VM or through
  Hyper-V isolation. Volume mount paths use a cross-layer translation mechanism
  (`/run/desktop/mnt/host/...`), making path validation significantly more
  complex and fragile than on Linux.

---

## 2. Feasibility of Path-Checking Docker CLI Arguments

The existing security gate (`security_gate.py`) validates file paths supplied to
tool calls to ensure they stay within the project folder. This section assesses
whether the same approach can be applied to Docker CLI arguments.

### 2.1 Arguments That Carry File Paths

| Argument | CLI forms | Validation complexity |
|----------|-----------|----------------------|
| Volume mount source | `-v /host/path:/container/path` | Moderate — split on `:`, validate first segment |
| Build context | `docker build <path>` | Low — positional arg or `--build-arg` path |
| Dockerfile location | `-f <path>` | Low — explicit flag |
| Compose file | `-f <file>`, `--file <file>` | Low — explicit flag, but file contents must also be validated |
| `--mount` syntax | `--mount type=bind,source=<path>,target=<path>` | High — key=value pair parsing |
| `.dockerenv` / `--env-file` | `--env-file <path>` | Moderate |

### 2.2 Arguments That Cannot Be Path-Checked

The following docker/docker-compose arguments have security implications that are
**not** addressable by path-checking alone:

| Argument | Risk | Reason path-checking fails |
|----------|------|----------------------------|
| `--privileged` | Container escape | No path involved |
| `--cap-add <cap>` | Privilege escalation | No path involved |
| `--network host` | Network exposure | No path involved |
| `--pid host` | Process namespace sharing | No path involved |
| `--ipc host` | IPC namespace sharing | No path involved |
| `--userns host` | UID mapping bypass | No path involved |
| `-v /var/run/docker.sock` | Socket exposure | Path is outside project folder but trivially recognizable |
| `--device <dev>` | Device access | No path meaningful |
| Inline `COPY`, `ADD` in Dockerfile | Build context exfil | Require static analysis of Dockerfile content |
| `volumes:` in compose YAML | Host mount | Require YAML parsing of compose file |

**Conclusion:** path-checking covers only the subset of Docker flags that specify
file paths. The most dangerous flags (`--privileged`, `--network host`, capability
flags) carry no paths and require a separate blocklist. Maintaining a complete and
correct blocklist is an ongoing task; new flags are added across Docker, Compose,
and Buildx regularly.

### 2.3 Implementation Complexity

A minimal path-safe Docker argument validator would need to:

1. Parse `docker` / `docker-compose` / `docker buildx` subcommand trees.
2. For each subcommand, define which positional and keyword arguments carry paths.
3. Resolve each path argument to an absolute, symlink-resolved canonical path.
4. Verify membership in the project folder.
5. Blocklist dangerous non-path flags (at minimum: `--privileged`, `--cap-add`,
   `--net host`, `--pid host`, `--ipc host`, `--userns`).
6. For `docker-compose`, additionally parse all referenced YAML files and validate
   every `volumes:` entry.

Compared to the existing path-checker, this is easily 5–10× more code, covering
the CLI grammar of three distinct tools that evolve independently and whose
argument parsers are not document-stable across versions.

---

## 3. Docker Socket Access Requirements and Security Implications

Every Docker CLI command requires communication with the Docker daemon via:

- **Unix socket**: `/var/run/docker.sock` (Linux/macOS)
- **Named pipe**: `//./pipe/docker_engine` (Windows)
- **TCP socket**: `tcp://host:port` (remote daemons)

### 3.1 Socket Exposure Risk

The Docker socket is equivalent to root access on the host. Any process that can
make API calls to the socket can:

- Create containers with `--privileged` and `--volume /:/mnt/host`.
- Read and write any file on the host by mounting it.
- Install kernel modules.
- Access other containers on the same host.

Agents running in a VS Code terminal already have access to the same user permissions
that the Docker socket grants (because both the terminal and Docker CLI run as the
same local user). The socket itself is not an additional escalation path in this
scenario. However, if an agent is running inside a containerized VS Code environment
(e.g., Dev Containers), socket exposure inside the container is a critical risk.

### 3.2 Dev Container Context

The primary use case that motivates Docker support is **Dev Containers**: agents
that run inside a container and need to interact with Docker to build/run sibling
containers. In this context:

- Mounting `/var/run/docker.sock` into the Dev Container (Docker-in-Docker via
  socket forwarding) makes the agent inside the container a full Docker admin.
- True Docker-in-Docker (`--privileged` + `dind` image) is even more dangerous.
- Neither configuration is safe to allow without compensating controls that are
  outside the current project scope.

### 3.3 Windows Socket Behavior

On Windows, the Docker named pipe `//./pipe/docker_engine` is accessible by
members of the `docker-users` group. There is no file-system path that the safety
gate can validate. Windows Docker also supports WSL 2 integration, where the
socket appears inside WSL distributions at Linux paths — making consistent
cross-platform path validation of the socket location impractical.

---

## 4. Safe-Subset Allowlist Assessment

This section evaluates whether a restricted set of Docker commands could be
allowed without unacceptable risk.

### 4.1 Read-Only / Informational Commands

The following commands do not create containers or modify the host filesystem
directly:

| Command | Risk level | Notes |
|---------|------------|-------|
| `docker version` | Very low | Reads daemon version info only |
| `docker info` | Low | Exposes daemon configuration; leaks host details |
| `docker images` | Low | Lists local images; no side effects |
| `docker ps` | Low | Lists running containers |
| `docker inspect <image>` | Low–Medium | Reveals image metadata including exposed secrets in labels |
| `docker logs <container>` | Low–Medium | May expose sensitive output from other containers |

These commands are relatively safe individually but establish that Docker CLI calls
in general are permitted, making it harder to enforce restrictions on higher-risk
subcommands.

### 4.2 Build Commands

| Command | Risk level | Conditions for lower risk |
|---------|------------|--------------------------|
| `docker build -f <file> <context>` | Medium | Context path and `-f` path must both be in project folder; no `--build-arg` values are secrets |
| `docker buildx build` | Medium | Same as above; Buildx adds remote cache/push flags that increase risk |
| `docker-compose build` | Medium–High | Requires YAML validation; multi-service files significantly increase surface |

### 4.3 Run Commands

| Command | Risk level | Conditions for lower risk |
|---------|------------|--------------------------|
| `docker run --rm <image>` | High | Even without volume mounts, pulls arbitrary code and executes it on the host |
| `docker run --rm -v <project>:/work <image>` | High | Path-checkable but image code is untrusted |
| `docker-compose up` | Very high | Orchestrates multiple containers; YAML must be fully validated |

**Key finding:** even the "safest" run-class commands execute arbitrary image
code on the host. Unlike shell commands that operate on local files, `docker run`
imports and executes foreign binaries. The current path-checking model has no
mechanism to audit the code inside container images.

### 4.4 Proposed Minimal Safe Subset (If Deferred WP Approves)

If a future workpackage implements Docker support, the following represents the
**minimal allowable surface** — commands allowed only after all of the listed
preconditions are verified:

```
Allowed commands (subject to conditions):
  docker version
  docker info
  docker images [ls]
  docker ps [--all]
  docker inspect <image-name-or-id>  (not volume/container inspect)
  docker build -f <path> <context>   (path and context inside project folder;
                                      no --privileged, --network host, --cap-add)
  docker-compose build               (compose file in project folder;
                                      all volume sources in project folder;
                                      no privileged service entries)

Blocked unconditionally:
  docker run   (all variants — image-execution risk is non-enumerable)
  docker exec  (arbitrary code in running containers)
  docker-compose up / down / run     (orchestration — too broad)
  docker system prune                (destructive — affects whole daemon)
  docker volume create/rm            (host volume management)
  docker network create/rm           (host network management)
  Any flag: --privileged, --cap-add, --network host, --pid host,
            --ipc host, --userns host, --device, --security-opt
  Any mount of /var/run/docker.sock or //./pipe/docker_engine
```

This allowlist still requires a Docker CLI argument parser that does not currently
exist in this project. Building it is a non-trivial engineering effort (see Section
2.3).

---

## 5. Recommendation

### Decision: DEFER

Docker command support **should not be enabled** in the current security
architecture. The primary reasons are:

1. **Non-enumerable attack surface.** The combination of container escape paths,
   capability flags, network flags, and image execution means no finite blocklist
   can guarantee safety. The model "allow docker unless explicitly blocked" is
   incompatible with the project's fail-closed security mandate.

2. **Image execution has no analogue to path-checking.** The existing safety model
   is built around validating file system paths. Docker's core value proposition —
   running arbitrary container images — introduces code execution that the current
   architecture has no hook to validate.

3. **Docker-compose YAML parsing overhead.** Safely supporting `docker-compose`
   requires a full YAML validator for compose files, substantially increasing code
   complexity and the maintenance burden of keeping up with compose file schema
   evolution.

4. **Platform inconsistency.** Docker behaves differently on Windows (named pipes,
   WSL 2 path translation), Linux, and macOS (VM-based socket), making a single
   cross-platform path-checker impractical to validate exhaustively.

5. **Current project phase.** The project is still hardening the existing
   allow/block rules for shell commands. Adding Docker support at this stage
   increases total attack surface before the baseline is stable.

### Conditions for Future Approval

Docker support MAY be reconsidered in a future workpackage (e.g., `SAF-055` or
similar) if **all** of the following are true:

- [ ] The existing shell-command safety gate has reached a stable, tested state
  (all SAF-04x WPs done).
- [ ] A Docker CLI argument parser is implemented and independently reviewed.
- [ ] The allowlist is restricted to the **informational + build-only subset**
  defined in Section 4.4.
- [ ] `docker run` and `docker-compose up` remain blocked unconditionally.
- [ ] Cross-platform path resolution for volume mounts is implemented and tested
  on Windows, Linux, and macOS.
- [ ] A threat model review is conducted by an agent with security expertise at
  implementation time.

### Impact on US-036

US-036 acceptance criterion 5 states: *"Docker and container support feasibility
is researched and captured for future implementation decisions."* This report
satisfies that criterion. The US-036 implementation workpackages (SAF-040,
SAF-041, SAF-042) are **not blocked** by this finding; they should proceed with
the non-Docker portions of the expanded command set.

---

## 6. References and Related Workpackages

| ID | Relationship |
|----|-------------|
| US-036 | Parent user story — expand allowed terminal command set |
| SAF-040 | Implements additional read-only command allowlist |
| SAF-041 | Implements shell utility command allowlist |
| SAF-042 | Expands git allowlist |
| DOC-013 | Related research — multi-agent counter coordination |
| DOC-012 | Related research — MCP tools extensibility |

### External References (concepts, not URLs)

- Docker security best practices: official Docker documentation on security topics  
- OWASP Container Security Cheat Sheet  
- CVE-2019-5736 (runc container escape)  
- CVE-2024-21626 (runc Leaky Vessels)  
- CIS Docker Benchmark  
