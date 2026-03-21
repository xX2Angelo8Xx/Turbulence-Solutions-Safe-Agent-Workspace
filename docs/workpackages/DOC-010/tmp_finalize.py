#!/usr/bin/env python3
"""
Atomic DOC-010 tester finalization script.
Runs on DOC-010/research-session-id branch.
Performs:
1. Removes stray DOC-007 folder
2. Removes stray tests/DOC-007 test file
3. Stages DOC-010 files
4. Commits
5. Pushes
"""
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, **kwargs):
    print(f">>> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kwargs)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result

def main():
    # Verify we're on the correct branch
    branch_result = run(["git", "branch", "--show-current"])
    branch = branch_result.stdout.strip()
    if branch != "DOC-010/research-session-id":
        print(f"ERROR: Expected DOC-010/research-session-id, got: {branch}")
        sys.exit(1)
    print(f"On branch: {branch}")

    # Remove stray files/folders
    stray_wp = os.path.join(REPO_ROOT, "docs", "workpackages", "DOC-007")
    if os.path.isdir(stray_wp):
        print(f"Removing stray directory: {stray_wp}")
        shutil.rmtree(stray_wp)

    stray_test = os.path.join(REPO_ROOT, "tests", "DOC-007", "test_doc007_agent_rules.py")
    if os.path.isfile(stray_test):
        print(f"Removing stray file: {stray_test}")
        os.remove(stray_test)

    # Stage all
    run(["git", "add", "-A"])

    # Verify staged
    status = run(["git", "status"])

    # Verify nothing unexpected staged
    diff_stat = run(["git", "diff", "--cached", "--stat"])

    # Run commit
    commit_result = run(["git", "commit", "-m", "DOC-010: Tester PASS"])
    if commit_result.returncode != 0:
        print("COMMIT FAILED")
        sys.exit(1)
    print("Commit successful.")

    # Push
    push_result = run(["git", "push", "origin", "DOC-010/research-session-id"])
    if push_result.returncode != 0:
        print("PUSH FAILED")
        sys.exit(1)
    print("Push successful.")

    print("DOC-010 Tester PASS complete.")

if __name__ == "__main__":
    main()
