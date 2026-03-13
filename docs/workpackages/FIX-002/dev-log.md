# Dev Log - FIX-002

## Workpackage
**ID:** FIX-002
**Title:** Fix SAF-010 hook config to reference Python security_gate.py
**Branch:** fix/FIX-002
**Date:** 2026-03-13
**Status:** Review

## Summary

Updated require-approval.json in both locations to replace legacy bash/PowerShell script references with the Python-based security_gate.py script.

## Problem

Default-Project/.github/hooks/require-approval.json (and its mirror in templates/coding/) referenced legacy scripts:
- command: bash .github/hooks/scripts/require-approval.sh
- windows: powershell -NoProfile -ExecutionPolicy Bypass -File .github/hooks/scripts/require-approval.ps1

The 8 SAF-010 tests expected both fields to reference security_gate.py and start with python.

## Changes Made

| File | Change |
|------|--------|
| Default-Project/.github/hooks/require-approval.json | Replaced bash/PS1 commands with python .github/hooks/scripts/security_gate.py |
| templates/coding/.github/hooks/require-approval.json | Same change (kept in sync per INS-004 requirements) |

## Tests

- SAF-010 suite: tests/SAF-010/test_saf010_hook_config.py - 29 tests, all pass
- SAF-008 suite: 23 tests, all pass (no hash regression)