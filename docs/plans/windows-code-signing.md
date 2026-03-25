# Windows Authenticode Code Signing — Research Report

**Workpackage:** DOC-016  
**Date:** 2026-03-25  
**Status:** Final  
**Author:** Developer Agent

---

## Executive Summary

Windows SmartScreen flags unsigned executables with a "Windows protected your PC" warning,
which damages user trust for any distributed application. This report evaluates three
free-for-OSS signing options — **SignPath.io**, **Azure Trusted Signing**, and **SSL.com OSS program** —
and recommends **SignPath.io** (free OSS tier) as the primary path for this project.

> **Key finding:** A fully automated, zero-human-intervention signing pipeline is achievable
> with SignPath.io's free OSS plan. All three services require a one-time human setup step
> (account creation + organisation/project verification), but after that the CI pipeline
> can sign without further human approval.

---

## 1. Requirements Overview

The goal (from US-040) is:

1. Both `AgentEnvironmentLauncher.exe` (PyInstaller output) and
   `AgentEnvironmentLauncher-Setup.exe` (Inno Setup output) are signed.
2. `signtool verify /pa` passes on both artefacts.
3. Windows SmartScreen does not show the "Windows protected your PC" warning.
4. Signing is automated in GitHub Actions — no manual intervention per release.
5. Service is **free** for open-source GitHub projects.

---

## 2. Options Evaluated

### 2.1 SignPath.io — Free OSS Plan

**URL:** <https://signpath.io>

#### What it is

SignPath is a cloud-based code signing platform. It provides a **free tier specifically for
open-source projects** hosted on GitHub with a public repository. The free OSS tier includes
Authenticode signing (EV-grade certificate managed by SignPath), unlimited signing requests,
and a native GitHub Actions integration.

#### Free OSS programme eligibility

| Requirement | This Project |
|---|---|
| Public GitHub repository | ✅ `xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace` |
| OSS licence (MIT, Apache, GPL, etc.) | ✅ check `LICENSE` file |
| No commercial distribution | Verify — if the software is free to download and use, this is met |
| Signing only the build artefact (no executable that itself signs) | ✅ |

**Important caveat:** SignPath reviews applications manually before granting free OSS access.
This one-time human step (filling out an application form) is unavoidable. After approval the
pipeline is fully automated.

#### Certificate type

SignPath provides an **Extended Validation (EV) Authenticode certificate** under their shared
chain. EV certificates bypass SmartScreen reputation building — a freshly signed file with an
EV cert does not need to accumulate download counts before SmartScreen trusts it.

#### Setup requirements (one-time)

1. Create a SignPath.io account (sign up at <https://signpath.io>).
2. Apply for the Free OSS Programme — fill in the application at
   <https://about.signpath.io/product/open-source>. Review takes 1–5 business days.
3. Once approved, log in and configure:
   - **Organisation** — created automatically on approval.
   - **Certificate** — "Authenticode" certificate type is pre-provisioned.
   - **Signing policy** — create policy e.g. `release-signing` with EV cert.
   - **Project** — e.g. `agent-environment-launcher`.
   - **Artefact configuration** — configure two signing requests:
     - `launcher.exe` (the PyInstaller output)
     - `AgentEnvironmentLauncher-Setup.exe` (the Inno Setup output)
4. Generate an **API token** under Organisation → Users → API tokens.
5. Add the token to GitHub: Settings → Secrets and variables → Actions →
   `SIGNPATH_API_TOKEN`.

#### CI integration

SignPath supplies an official GitHub Actions action: `signpath/github-action-submit-signing-request`.

```yaml
# Excerpt — add after the "Build installer" step in windows-build job
- name: Sign launcher executable
  uses: signpath/github-action-submit-signing-request@v1
  with:
    api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
    organization-id: '<your-org-id>'         # from SignPath dashboard
    project-slug: 'agent-environment-launcher'
    signing-policy-slug: 'release-signing'
    artifact-configuration-slug: 'launcher-exe'
    github-artifact-name: 'windows-build-unsigned'
    wait-for-completion: true
    output-artifact-name: 'windows-build-signed'

- name: Sign setup installer
  uses: signpath/github-action-submit-signing-request@v1
  with:
    api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
    organization-id: '<your-org-id>'
    project-slug: 'agent-environment-launcher'
    signing-policy-slug: 'release-signing'
    artifact-configuration-slug: 'installer-exe'
    github-artifact-name: 'windows-installer-unsigned'
    wait-for-completion: true
    output-artifact-name: 'windows-installer-signed'
```

> The action uploads the artefact to SignPath, waits for the signing service to process and
> sign it, then downloads the signed artefact back as a new GitHub Actions artefact.

#### Limitations / caveats

- Manual application and review (1–5 days, one-time).
- OSS policy review — SignPath may audit that the signed binaries correspond to the
  public source code. Builds must be reproducible or at least traceable to a tagged commit.
- Organisation ID and project slug must be hardcoded in the workflow (not secrets) or stored
  as non-secret variables.

---

### 2.2 Azure Trusted Signing

**URL:** <https://azure.microsoft.com/en-us/products/trusted-signing>

#### What it is

Azure Trusted Signing (formerly Azure Code Signing) is Microsoft's own cloud signing service.
It supports Authenticode and provides SmartScreen reputation benefits because it is owned by
Microsoft.

#### Free OSS programme

There is **no dedicated free OSS tier.** Azure Trusted Signing uses a pay-per-use pricing model:

- **Basic tier:** ~$9.99/month (2025 pricing; subject to change).
- **Premium tier:** ~$99.99/month.
- No free tier for OSS projects as of 2026.

Additionally, it requires an Azure subscription and a verified identity (organisation or
individual) — a human must complete identity verification with Microsoft.

#### Certificate type

Uses **trusted signing certificates** that are part of Microsoft's certificate chain. SmartScreen
trust is built through reputation, not EV status. A freshly signed file still needs download
count before SmartScreen fully trusts it (unlike EV).

**Verdict:** Not free for OSS. Excluded as a primary recommendation.

---

### 2.3 SSL.com OSS Code Signing Programme

**URL:** <https://www.ssl.com/certificates/code-signing/>

#### What it is

SSL.com is a commercial CA that offers Authenticode code signing certificates. They have
historically offered discounted or free certificates for open-source projects on a
case-by-case basis.

#### Free OSS programme

SSL.com does **not** maintain a public, structured free-for-OSS programme as of 2026. Their
OSS discount policy is informal — they may offer free certificates to well-known OSS projects
upon request, but:

- There is no documented automated CI integration path.
- Certificates are issued as PKCS#12 files that must be managed as secrets.
- Private keys must be stored as encrypted GitHub Secrets and passed to `signtool.exe`.
- SSL.com moved to **hardware-based key storage requirement** (HSM or cloud HSM) for EV
  certificates per CA/Browser Forum Baseline Requirements (effective June 2023). Software-based
  EV key storage is no longer permitted.
- This means signing with an SSL.com EV cert now requires either a physical HSM token
  (impractical for CI) or an HSM cloud service (additional cost).

**Verdict:** No structured free OSS programme; HSM requirement makes CI integration
complex and costly. Excluded.

---

## 3. Comparison Matrix

| Criterion | SignPath.io (OSS) | Azure Trusted Signing | SSL.com OSS |
|---|---|---|---|
| **Free for OSS** | ✅ Yes (dedicated programme) | ❌ No (~$10/month) | ⚠️ Informal, case-by-case |
| **Certificate type** | EV Authenticode | Trusted Signing (non-EV) | OV or EV Authenticode |
| **SmartScreen bypass** | ✅ EV = instant trust | ⚠️ Reputation-based | ✅ EV (if obtained) |
| **Automated CI** | ✅ Official GitHub Action | ✅ Azure CLI / GitHub Action | ⚠️ Complex — HSM required |
| **Human setup required** | ✅ One-time application | ✅ Azure account + identity | ✅ Account + certificate request |
| **Key management** | ✅ Managed by SignPath | ✅ Managed by Azure | ❌ Developer manages key (HSM) |
| **No paid tier needed** | ✅ | ❌ | ❌ |
| **Recommended** | ✅ **Yes** | ❌ | ❌ |

---

## 4. Recommendation

**Recommended service: SignPath.io Free OSS Plan**

Reasons:
1. Only option that is genuinely free for public OSS GitHub repositories.
2. Provides EV-grade certificate → SmartScreen trusts the file immediately on first download.
3. Official GitHub Actions integration makes CI setup straightforward.
4. Key management is fully handled by SignPath — no private keys stored in GitHub Secrets.
5. Active platform with documented support for open-source projects.

---

## 5. Step-by-Step Implementation Plan

This plan is for workpackage **INS-024** (Integrate Authenticode signing into CI/CD pipeline),
which depends on this research. Steps 1–6 are one-time human setup. Steps 7 onwards are
developer/agent tasks.

### Phase A — Account Setup (Human, one-time)

**Step 1 — Apply for the SignPath Free OSS Programme**

1. Go to <https://about.signpath.io/product/open-source>.
2. Click "Apply now" and fill in the form:
   - Repository URL: `https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace`
   - Project name: `Turbulence Solutions Safe Agent Workspace`
   - Licence: (your project licence)
   - Contact email: (project maintainer email)
3. Wait for approval email (typically 1–5 business days).

**Step 2 — Configure SignPath after approval**

Once the approval email arrives and you can log in to <https://app.signpath.io>:

1. Note your **Organisation ID** from the dashboard URL or Organisation Settings.
2. Navigate to **Projects** → **Add Project**:
   - Project slug: `agent-environment-launcher`
3. Navigate to **Code Signing Certificates** → verify the Authenticode certificate is provisioned.
4. Navigate to **Signing Policies** → **Add Policy**:
   - Slug: `release-signing`
   - Certificate: select the provisioned Authenticode cert
   - Authorised signers: your account
5. Navigate to **Projects** → `agent-environment-launcher` → **Artefact Configurations**:
   - Add config `launcher-exe`: path pattern `dist/AgentEnvironmentLauncher/*.exe` (or the
     exact path from PyInstaller output)
   - Add config `installer-exe`: path pattern `src/installer/windows/Output/*.exe`
6. Navigate to **Organisation** → **Users** → **API Tokens** → **Create API Token**.
   - Scope: Signing requests (submit + read)
   - Copy the token value immediately (shown only once).

**Step 3 — Add GitHub Secret**

In the GitHub repository settings:
1. Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Name: `SIGNPATH_API_TOKEN`
3. Value: the API token copied in Step 2.

### Phase B — Workflow Integration (Developer Agent, INS-024)

**Step 4 — Update `.github/workflows/release.yml`**

In the `windows-build` job, after the "Build installer" step:

```yaml
      - name: Upload unsigned launcher for signing
        uses: actions/upload-artifact@v4
        with:
          name: windows-build-unsigned
          path: dist/AgentEnvironmentLauncher/AgentEnvironmentLauncher.exe

      - name: Upload unsigned installer for signing
        uses: actions/upload-artifact@v4
        with:
          name: windows-installer-unsigned
          path: src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe

      - name: Sign launcher executable
        uses: signpath/github-action-submit-signing-request@v1
        with:
          api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
          organization-id: '<SIGNPATH_ORG_ID>'
          project-slug: 'agent-environment-launcher'
          signing-policy-slug: 'release-signing'
          artifact-configuration-slug: 'launcher-exe'
          github-artifact-name: 'windows-build-unsigned'
          wait-for-completion: true
          output-artifact-name: 'windows-launcher-signed'

      - name: Sign setup installer
        uses: signpath/github-action-submit-signing-request@v1
        with:
          api-token: ${{ secrets.SIGNPATH_API_TOKEN }}
          organization-id: '<SIGNPATH_ORG_ID>'
          project-slug: 'agent-environment-launcher'
          signing-policy-slug: 'release-signing'
          artifact-configuration-slug: 'installer-exe'
          github-artifact-name: 'windows-installer-unsigned'
          wait-for-completion: true
          output-artifact-name: 'windows-installer-signed'

      - name: Upload signed Windows installer
        uses: actions/upload-artifact@v4
        with:
          name: windows-installer
          path: src/installer/windows/Output/AgentEnvironmentLauncher-Setup.exe
```

> Replace `<SIGNPATH_ORG_ID>` with the actual Organisation ID from the SignPath dashboard.
> This value is not secret and can be stored in the workflow file directly.

**Step 5 — Update the release job artefact references**

In the `release` job (which runs after `windows-build`), update the artefact download step
to use `windows-installer-signed` instead of `windows-installer` if the naming changes.

**Step 6 — Verify the signed artefact**

After the first successful signed build, verify locally:

```powershell
# Download the signed installer from GitHub Actions artefacts, then:
signtool verify /pa AgentEnvironmentLauncher-Setup.exe
```

Expected output:
```
Successfully verified: AgentEnvironmentLauncher-Setup.exe
```

### Phase C — Verification (INS-025)

See workpackage INS-025 for the full SmartScreen verification procedure on a fresh Windows 11
machine.

---

## 6. Certificate Management

With SignPath.io (OSS):

- **Private key:** Never leaves SignPath's HSM infrastructure. Developers never hold the key.
- **Certificate rotation:** SignPath manages certificate renewal automatically.
- **Revocation:** If a signing policy is misconfigured or a release is found malicious,
  SignPath allows per-signing-request auditing and supports revocation requests.
- **Secrets in CI:** Only the `SIGNPATH_API_TOKEN` is stored as a GitHub Secret. This is a
  short-lived, revocable API token — not the signing key itself.

---

## 7. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| SignPath rejects OSS application | Low | Application is reviewed — ensure repository is truly public OSS. If rejected, escalate to project owner to appeal or explore SSL.com manual request. |
| SignPath delays approval (>1 week) | Medium | Pipeline can continue releasing unsigned builds in the interim. SmartScreen warning is tolerable during the transition period. |
| SignPath changes OSS pricing | Low | Monitor SignPath's OSS programme page. Alternative: investigate SSL.com direct request or Azure Trusted Signing if budget becomes available. |
| Signing step adds CI latency | Low | SignPath typically signs within 1–3 minutes. Acceptable for release workflows. |
| API token leaked | Low | Rotate token immediately via SignPath dashboard. Token only authorises signing requests — cannot access the private key. |

---

## 8. Alternative: No-Cost Transition Period

If SignPath OSS approval is delayed or denied, the recommended interim approach is:

1. Continue publishing unsigned binaries with a prominent README note explaining the
   SmartScreen warning and how to bypass it (`More info` → `Run anyway`).
2. Do not attempt to generate or purchase a self-signed certificate — self-signed certs
   produce a "unknown publisher" warning just as bad as unsigned.

---

## 9. References

- SignPath Free OSS Programme: <https://about.signpath.io/product/open-source>
- SignPath GitHub Action: <https://github.com/SignPath/github-action-submit-signing-request>
- Azure Trusted Signing pricing: <https://azure.microsoft.com/en-us/pricing/details/trusted-signing/>
- CA/B Forum Baseline Requirements (HSM mandate): <https://cabforum.org/working-groups/code-signing/requirements/>
- Microsoft SmartScreen reputation docs: <https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/>
- signtool CLI reference: <https://learn.microsoft.com/en-us/dotnet/framework/tools/signtool-exe>
