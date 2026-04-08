# NoAgentZone

This folder is **hard-blocked** from all AI agent access. The PreToolUse hook will deny any tool call targeting files in this directory — no approval dialog is shown, access is simply refused.

## Purpose

Store files that must never be processed, read, or referenced by AI agents:

- Credentials and API keys
- Proprietary algorithms and trade secrets
- HR and personnel documents
- Legal contracts and NDAs
- Any data classified as confidential

## How It Works

The `.github/hooks/scripts/require-approval.sh` hook checks every tool call. If the target path falls inside `NoAgentZone/`, the hook returns a **deny** decision, blocking the action entirely.

## Important

- Do NOT rename this folder — the hook script relies on the name `NoAgentZone`.
- Do NOT move sensitive files to `Project/` — that folder has relaxed agent permissions.
