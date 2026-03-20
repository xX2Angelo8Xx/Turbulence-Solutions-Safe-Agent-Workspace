#!/usr/bin/env python3
"""One-time CSV repair script for 2026-03-20b maintenance findings.

Fixes:
  - workpackages.csv: FIX-036/037 merged row, FIX-040 embedded data, FIX-047 unescaped comma
  - user-stories.csv: US-024 unescaped commas, US-026 escaped-quote artefacts
  - bugs.csv: BUG-084 status, BUG-088/089/090 status and Fixed In WP

Delete this script after use.
"""

import csv
import sys
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WP_CSV = REPO / "docs" / "workpackages" / "workpackages.csv"
US_CSV = REPO / "docs" / "user-stories" / "user-stories.csv"
BUG_CSV = REPO / "docs" / "bugs" / "bugs.csv"


def repair_workpackages():
    with open(WP_CSV, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"workpackages.csv: {len(lines)} lines before repair")

    # --- Fix 1: FIX-036 merged with FIX-037 ---
    idx036 = None
    for i, line in enumerate(lines):
        if line.startswith('"FIX-036"'):
            idx036 = i
            break
    assert idx036 is not None, "FIX-036 line not found"
    assert "FIX-037" in lines[idx036], "FIX-037 not embedded in FIX-036 line"

    fix036 = (
        '"FIX-036","Fix","Bump version to 2.1.0","Done","Developer Agent",'
        '"Update version from 2.0.1 to 2.1.0 in all 5 locations: config.py, '
        "pyproject.toml, setup.iss, build_dmg.sh, build_appimage.sh. "
        'Update docs/architecture.md with security model changes.",'
        '"All version references show 2.1.0. Architecture doc reflects current state.",'
        '"V2.1.0 release. Tester PASS: 7/7 tests.","US-030","",""\n'
    )
    fix037 = (
        '"FIX-037","Fix","Remove .dist-info dirs from macOS bundle before signing",'
        '"Done","Developer Agent",'
        '"Add a step to src/installer/macos/build_dmg.sh (between Step 2 Create .app '
        "bundle and Step 3.5 Code signing) that removes all .dist-info directories "
        "from the _internal/ folder. These are Python package metadata not needed at "
        'runtime for PyInstaller bundles and cause codesign to fail.",'
        '"macOS CI build completes without codesign errors. No .dist-info directories '
        'remain in the .app bundle.","BUG-070","US-026","",""\n'
    )

    # Replace the merged line with two separate lines
    new_lines = []
    for i, line in enumerate(lines):
        if i == idx036:
            new_lines.append(fix036)
            new_lines.append(fix037)
        else:
            new_lines.append(line)
    lines = new_lines

    # --- Fix 2: FIX-040 embedded FIX-039 data ---
    idx040 = None
    for i, line in enumerate(lines):
        if line.startswith('"FIX-040"'):
            idx040 = i
            break
    assert idx040 is not None, "FIX-040 line not found"
    assert "Developer Agent,In build_dmg.sh" in lines[idx040], \
        "Expected embedded FIX-039 data in FIX-040"

    fix040 = (
        '"FIX-040","Fix","Fix Windows update restart and stale version label",'
        '"Done","Developer Agent",'
        '"Fix two related bugs in the Windows in-app update flow: '
        "(1) In src/launcher/core/applier.py _apply_windows(): replace sys.exit(0) "
        "with os._exit(0) to force-terminate from daemon thread \u2014 sys.exit() "
        "from a non-main thread does not terminate the main process. "
        "(2) In src/installer/windows/setup.iss [Run] section: remove the skipifsilent "
        "flag so the app relaunches after a /SILENT install. "
        "(3) In src/launcher/gui/app.py: update the UI before exit to show "
        "'Installing update... App will restart.' so the user knows what is happening.\","
        '"After clicking Download & Install Update the old launcher process terminates '
        "and the new version launches automatically. The version label in the new "
        'instance shows the correct new version.",'
        '"BUG-073 BUG-074. Tested on Windows 11.","US-031","",""\n'
    )
    lines[idx040] = fix040

    # --- Fix 3: FIX-047 unescaped comma in Comments ---
    idx047 = None
    for i, line in enumerate(lines):
        if line.startswith('"FIX-047"'):
            idx047 = i
            break
    assert idx047 is not None, "FIX-047 line not found"

    fix047 = (
        '"FIX-047","Fix","Bump version to 3.0.0","Done","Developer Agent",'
        '"Update the version string from 2.1.3 to 3.0.0 in all locations: '
        "(1) src/launcher/config.py VERSION constant, "
        "(2) pyproject.toml version field, "
        "(3) src/installer/windows/setup.iss MyAppVersion, "
        "(4) src/installer/macos/build_dmg.sh APP_VERSION, "
        "(5) src/installer/linux/build_appimage.sh APP_VERSION. "
        'Update docs/architecture.md with V3.0.0 security changes.",'
        '"All version references consistently show 3.0.0.",'
        '"V3.0.0 release \u2014 security hardening, Default-Project removal, '
        'audit documentation.","Enabler","",""\n'
    )
    lines[idx047] = fix047

    # Verify
    buf = StringIO("".join(lines))
    reader = csv.DictReader(buf)
    rows = list(reader)

    overflow_ids = []
    buf2 = StringIO("".join(lines))
    reader2 = csv.DictReader(buf2)
    for row in reader2:
        if None in row:
            overflow_ids.append(row.get("ID", "?"))

    ids_present = {r["ID"] for r in rows}
    for wp in ("FIX-036", "FIX-037", "FIX-040", "FIX-047"):
        assert wp in ids_present, f"{wp} not found after repair"

    print(f"  After repair: {len(lines)} lines, {len(rows)} data rows")
    print(f"  FIX-036/037/040/047 all parseable: True")
    print(f"  Overflow rows: {overflow_ids or 'none'}")

    with open(WP_CSV, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print("  workpackages.csv REPAIRED")


def repair_user_stories():
    with open(US_CSV, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"user-stories.csv: {len(lines)} lines before repair")

    # --- Fix US-024: unescaped commas in "I want" field ---
    idx024 = None
    for i, line in enumerate(lines):
        if line.startswith('"US-024"'):
            idx024 = i
            break
    assert idx024 is not None, "US-024 line not found"

    fix024 = (
        '"US-024","Fix Agent Workflow Restrictions in Project Folder","developer",'
        '"AI agents to perform all standard development operations (search, edit, run, '
        'test) inside the project folder without security gate interference",'
        '"the security gate protects restricted zones without impeding normal '
        'development workflow",'
        '"1. grep_search file_search and semantic_search work for project folder scope. '
        "2. python pip and venv commands execute inside project folder. "
        "3. .venv directory creation is allowed. "
        "4. All file tools work with absolute project paths consistently. "
        "5. cat type and other read commands work in project folder. "
        "6. get_errors works for project folder paths. "
        '7. Terminal commands with absolute project paths work.",'
        '"Done",'
        '"FIX-021, FIX-022, FIX-023, FIX-024, FIX-025, FIX-026, FIX-027",'
        '"All 7 WPs completed and merged to main."\n'
    )
    lines[idx024] = fix024

    # --- Fix US-026: escaped-quote artefacts ---
    idx026 = None
    for i, line in enumerate(lines):
        if line.startswith('"US-026"'):
            idx026 = i
            break
    assert idx026 is not None, "US-026 line not found"

    fix026 = (
        '"US-026","Fix macOS Code Signing Build Failure","macOS developer",'
        '"the macOS CI build to produce a properly signed application bundle",'
        '"the application can be distributed and launched on macOS 14+",'
        '"1. build_dmg.sh signs individual .dylib and .so files before signing the .app '
        "bundle. 2. Python.framework is signed with --deep as a valid nested bundle. "
        "3. The .app bundle is signed WITHOUT --deep to avoid failing on the python3.11 "
        "stdlib directory. 4. codesign --verify --deep --strict passes after signing. "
        '5. CI build completes without codesign errors.",'
        '"Done",'
        '"FIX-031, FIX-037, FIX-038, FIX-039",'
        '"V2.1.0 \u2014 FIX-031 completed. Bottom-up signing implemented and tested. '
        "FIX-037 removes .dist-info dirs before codesign. "
        "FIX-038 removes bundle-level signing entirely \u2014 component-level signing only. "
        'FIX-039 skips launcher re-sign inside .app \u2014 verify pre-bundle binary."\n'
    )
    lines[idx026] = fix026

    # Verify
    buf = StringIO("".join(lines))
    reader = csv.DictReader(buf)
    rows = list(reader)
    overflow_ids = []
    buf2 = StringIO("".join(lines))
    reader2 = csv.DictReader(buf2)
    for row in reader2:
        if None in row:
            overflow_ids.append(row.get("ID", "?"))

    print(f"  After repair: {len(lines)} lines, {len(rows)} data rows")
    print(f"  Overflow rows: {overflow_ids or 'none'}")

    with open(US_CSV, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print("  user-stories.csv REPAIRED")


def repair_bugs():
    # Use csv_utils for proper locked operations
    sys.path.insert(0, str(REPO / "scripts"))
    from csv_utils import read_csv, update_cell

    _, rows = read_csv(BUG_CSV)
    print(f"bugs.csv: {len(rows)} data rows")

    updates = [
        ("BUG-084", "Status", "Closed"),
        ("BUG-088", "Status", "Closed"),
        ("BUG-088", "Fixed In WP", "FIX-062"),
        ("BUG-089", "Status", "Closed"),
        ("BUG-089", "Fixed In WP", "FIX-063"),
        ("BUG-090", "Status", "Closed"),
        ("BUG-090", "Fixed In WP", "FIX-063"),
    ]

    for bug_id, col, val in updates:
        update_cell(BUG_CSV, "ID", bug_id, col, val)
        print(f"  {bug_id}.{col} = {val}")

    print("  bugs.csv REPAIRED")


if __name__ == "__main__":
    print("=" * 60)
    print("CSV Repair Script — 2026-03-20b Maintenance")
    print("=" * 60)

    repair_workpackages()
    print()
    repair_user_stories()
    print()
    repair_bugs()

    print()
    print("ALL CSV REPAIRS COMPLETE")
