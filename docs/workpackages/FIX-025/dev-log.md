# FIX-025 Dev Log — Add cat and type to Terminal Allowlist
**Date:** 2026-03-18  
**Author:** Developer Agent  
## Summary
Fixed BUG-058: `cat` and `type` commands were missing from the terminal
allowlist in security_gate.py. Added both to Category G (Read-only File
Inspection) and _PROJECT_FALLBACK_VERBS. Covers R5, R15 from Security
Verification Report.
## Tests
Tests in `tests/FIX-025/`: `test_fix025_cat_type_in_allowlist.py`
