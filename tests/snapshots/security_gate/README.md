# Security Gate Golden-File Snapshots

This directory contains golden-file test vectors for the security gate decision engine.

## Purpose

Each `.json` file contains an input (tool call) and the expected decision (allow/deny) from `security_gate.py`. If a code change causes a decision to flip (allow→deny or deny→allow), the corresponding snapshot test will fail explicitly.

## Structure

Each snapshot file:
```json
{
  "description": "Human-readable description of what this tests",
  "input": { ... },
  "expected_decision": "allow" | "deny",
  "expected_reason": "optional substring of reason message"
}
```

## Updating Snapshots

If a decision change is intentional (e.g., a new SAF workpackage changes security policy):
1. Run the snapshot tests to see which ones fail
2. Update the affected `.json` files with the new expected decision
3. Document the change in the relevant WP's dev-log.md
4. Reference the ADR that justifies the decision change
