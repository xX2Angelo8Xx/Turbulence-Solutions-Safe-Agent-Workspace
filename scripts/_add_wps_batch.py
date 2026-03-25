"""One-shot script to add all 17 new workpackages and update US cross-references."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import read_csv, write_csv, REPO_ROOT

WP_CSV = REPO_ROOT / "docs" / "workpackages" / "workpackages.csv"
US_CSV = REPO_ROOT / "docs" / "user-stories" / "user-stories.csv"


def main():
    # Read current workpackages
    wp_fields, wp_rows = read_csv(WP_CSV, strict=False)

    # Find next IDs for each category
    def next_id(prefix, rows):
        max_num = 0
        for r in rows:
            rid = r.get("ID", "")
            if rid.startswith(prefix + "-"):
                try:
                    num = int(rid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass
        return max_num + 1

    # Remove the incorrectly assigned DOC-016 if it has wrong content
    wp_rows = [r for r in wp_rows if not (r.get("ID") == "DOC-016" and "template rename" in r.get("Name", "").lower())]

    # Calculate next IDs
    counters = {
        "DOC": next_id("DOC", wp_rows),
        "INS": next_id("INS", wp_rows),
        "GUI": next_id("GUI", wp_rows),
        "FIX": next_id("FIX", wp_rows),
    }

    print(f"Next IDs: DOC-{counters['DOC']:03d}, INS-{counters['INS']:03d}, GUI-{counters['GUI']:03d}, FIX-{counters['FIX']:03d}")

    new_wps = []

    def add_wp(prefix, name, desc, goal, us, comments="", depends_on="", blockers=""):
        num = counters[prefix]
        wp_id = f"{prefix}-{num:03d}"
        counters[prefix] = num + 1
        new_wps.append({
            "ID": wp_id,
            "Category": prefix,
            "Name": name,
            "Status": "Open",
            "Assigned To": "",
            "Description": desc,
            "Goal": goal,
            "Comments": comments,
            "User Story": us,
            "Depends On": depends_on,
            "Blockers": blockers,
        })
        return wp_id

    # --- Phase 1: Windows Code Signing ---
    doc016 = add_wp("DOC",
        "Research free Windows code signing for OSS",
        "Evaluate SignPath.io (free for GitHub OSS), Azure Trusted Signing, SSL.com OSS program. Document setup requirements, CI integration steps, certificate management. Recommend approach with step-by-step implementation plan. Produce research report in docs/plans/.",
        "A research report documenting the recommended free Windows Authenticode signing service, setup instructions, and CI integration plan.",
        "US-040",
        "Phase 1 - Windows code signing research. macOS signing exists but Windows has zero signing.")

    ins024 = add_wp("INS",
        "Integrate Authenticode signing into CI/CD pipeline",
        "Set up the chosen signing service (likely SignPath.io). Add signing step to release.yml windows-build job after Inno Setup compiles the installer. Sign both the launcher .exe (PyInstaller output) and the installer .exe (Inno Setup output). Store signing credentials as GitHub repository secrets.",
        "Windows CI build job produces signed .exe installer and launcher binary. Signing step is automated and repeatable.",
        "US-040",
        "Phase 1 - Windows code signing CI integration.",
        depends_on=doc016)

    ins025 = add_wp("INS",
        "Verify signed installer passes SmartScreen",
        "Test signed installer on a fresh Windows 11 machine or VM. Verify signtool verify /pa passes on both .exe files. Verify Windows SmartScreen does not trigger on download and run. Document verification results and screenshots.",
        "Signed installer verified to pass SmartScreen on fresh Windows 11. signtool verify /pa passes. Verification documented.",
        "US-040",
        "Phase 1 - Windows code signing verification. Final validation step.",
        depends_on=ins024)

    # --- Phase 2: Template Renaming ---
    gui023 = add_wp("GUI",
        "Rename template directories and update launcher code",
        "Rename templates/coding/ to templates/agent-workbench/. Rename templates/creative-marketing/ to templates/certification-pipeline/. Update _format_template_name() in src/launcher/gui/app.py for new names. Update list_templates() and is_template_ready() in src/launcher/core/project_creator.py. Update TEMPLATES_DIR references in src/launcher/config.py if needed. Update launcher.spec datas if template paths are referenced. Update certification-pipeline/README.md content to say Certification Pipeline - Coming Soon.",
        "Template directories renamed. GUI dropdown shows Agent Workbench (selectable) and Certification Pipeline ...coming soon (greyed out). Project creation works with new template name.",
        "US-041",
        "Phase 2 - Template renaming. Core rename and launcher code update.")

    fix071 = add_wp("FIX",
        "Update all test references for template rename",
        "Grep all test files for templates/coding and creative-marketing references. Update paths in all affected test files to use templates/agent-workbench and templates/certification-pipeline respectively. Run full test suite to verify no regressions.",
        "All test files reference new template directory names. Full pytest suite passes with zero new failures.",
        "US-041",
        "Phase 2 - Template renaming. Test reference updates after directory rename.",
        depends_on=gui023)

    doc017 = add_wp("DOC",
        "Update documentation for template rename",
        "Update docs/architecture.md template structure diagrams and references. Update docs/project-scope.md template type descriptions. Update any work-rules files referencing template paths. Update repo-level copilot-instructions.md template references. Ensure all documentation reflects Agent Workbench and Certification Pipeline naming.",
        "All documentation files reference new template names. No stale references to coding or creative-marketing remain in docs.",
        "US-041",
        "Phase 2 - Template renaming. Documentation updates parallel with FIX-071.",
        depends_on=gui023)

    # --- Phase 3: Agent Workbench Infrastructure ---
    doc028 = add_wp("DOC",
        "Create agents/ directory in Agent Workbench template",
        "Create templates/agent-workbench/.github/agents/ directory. Add a README.md explaining the agent roster and how to customize agents. Update templates/agent-workbench/.github/instructions/copilot-instructions.md to reference available agents. Update templates/agent-workbench/Project/AGENT-RULES.md to document available agent personas.",
        "agents/ directory exists in template with README. copilot-instructions.md and AGENT-RULES.md reference the agent roster.",
        "US-042",
        "Phase 3 - Agent infra. Must complete BEFORE individual agent WPs. Depends on template rename.",
        depends_on=gui023)

    # --- Phase 3: Individual Agent WPs ---
    agent_wps = [
        ("Programmer", "US-042", "practical coder focused on implementation and refactoring", "read, edit, search, execute", "Follows project conventions, writes clean code, refactors when asked"),
        ("Brainstormer", "US-043", "creative thinker that generates multiple approaches and explores trade-offs", "read, search", "Ideation only - no edit tools. Explores options without premature commitment"),
        ("Tester", "US-044", "quality-focused test writer that finds edge cases", "read, edit, search, execute", "Writes unit and integration tests, validates behavior, finds edge cases"),
        ("Researcher", "US-045", "investigator that evaluates technologies and compares solutions", "read, search, fetch_webpage", "Produces structured summaries with pros and cons"),
        ("Scientist", "US-046", "analytical mind that is hypothesis-driven and evidence-based", "read, edit, search, execute", "Runs benchmarks, experiments, documents findings with data"),
        ("Criticist", "US-047", "critical reviewer that identifies issues without fixing them", "read, search", "Finds bugs, security issues, design flaws. Does NOT fix - only identifies"),
        ("Planner", "US-048", "organizer that creates structured plans and identifies dependencies", "read, search", "Planning only - no implementation. Produces actionable task lists"),
        ("Fixer", "US-049", "debugger and root cause analyst", "read, edit, search, execute", "Reads errors, traces execution, proposes and implements fixes"),
        ("Writer", "US-050", "technical writer that creates documentation", "read, edit, search", "Creates READMEs, API docs, comments, changelogs. Adapts to project style"),
        ("Prototyper", "US-051", "speed-focused MVP builder that validates ideas quickly", "read, edit, search, execute", "Builds quick-and-dirty POCs, trades perfection for speed"),
    ]

    for agent_name, us_id, persona, tools, notes in agent_wps:
        fname = agent_name.lower()
        add_wp("DOC",
            f"Create {fname}.agent.md for Agent Workbench",
            f"Create templates/agent-workbench/.github/agents/{fname}.agent.md with YAML frontmatter (name, description, tools: [{tools}], model). Persona: {persona}. {notes}. Agent must follow AGENT-RULES.md conventions. Write tests verifying the file exists and has valid YAML frontmatter.",
            f"{fname}.agent.md exists in template agents/ with valid YAML frontmatter, clear persona description, and correct tool list. Tests pass.",
            us_id,
            f"Phase 3 - Agent Workbench agents. Creates the {agent_name} agent.",
            depends_on=doc028)

    # Add all new WPs to the existing rows
    existing_ids = {r.get("ID") for r in wp_rows}
    added = []
    for wp in new_wps:
        if wp["ID"] in existing_ids:
            print(f"  SKIP {wp['ID']} (already exists)")
            continue
        wp_rows.append(wp)
        added.append(wp["ID"])

    # Write workpackages
    write_csv(WP_CSV, wp_fields, wp_rows)
    print(f"\nAdded {len(added)} workpackages: {added}")

    # --- Update User Stories' Linked WPs ---
    us_fields, us_rows = read_csv(US_CSV, strict=False)

    # Build mapping: US-ID -> list of new WP IDs
    us_to_wps: dict[str, list[str]] = {}
    for wp in new_wps:
        us = wp["User Story"]
        if us != "Enabler":
            us_to_wps.setdefault(us, []).append(wp["ID"])

    for row in us_rows:
        us_id = row.get("ID", "")
        if us_id in us_to_wps:
            existing = row.get("Linked WPs", "").strip()
            wp_list = [w.strip() for w in existing.split(",") if w.strip()]
            for new_wp in us_to_wps[us_id]:
                if new_wp not in wp_list:
                    wp_list.append(new_wp)
            row["Linked WPs"] = ", ".join(wp_list)

    write_csv(US_CSV, us_fields, us_rows)
    print("Updated User Story cross-references.")
    print("Done!")


if __name__ == "__main__":
    main()
