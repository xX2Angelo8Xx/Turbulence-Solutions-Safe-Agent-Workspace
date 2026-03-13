"""Main application window for the Turbulence Solutions Launcher."""

from __future__ import annotations

import threading
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path

import customtkinter as ctk

from launcher.config import APP_NAME, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, TEMPLATES_DIR, VERSION, get_display_version
from launcher.core.updater import check_for_update
from launcher.core.project_creator import create_project, list_templates
from launcher.core.vscode import find_vscode, open_in_vscode
from launcher.gui.components import make_browse_row, make_label_entry_row
from launcher.gui.validation import (
    check_duplicate_folder,
    validate_destination_path,
    validate_folder_name,
)

_WINDOW_WIDTH: int = 580
_WINDOW_HEIGHT: int = 520


def _format_template_name(raw: str) -> str:
    # Replace separators with spaces and apply title case for display.
    return raw.replace("-", " ").replace("_", " ").title()


class App:
    """Main GUI application window."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._window = ctk.CTk()
        self._window.title(APP_NAME)
        self._window.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")
        self._window.resizable(False, False)
        self._window.configure(fg_color=COLOR_PRIMARY)
        self._build_ui()
        # Silent background update check on launch (GUI-009).
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _get_template_options(self) -> list[str]:
        names = list_templates(TEMPLATES_DIR)
        return [_format_template_name(n) for n in names]

    def _build_ui(self) -> None:
        """Construct and arrange all UI widgets."""
        self._window.grid_columnconfigure(1, weight=1)

        # Project name label + entry
        self.project_name_entry = make_label_entry_row(
            self._window,
            label_text="Project Name:",
            placeholder="my-project",
            row=0,
        )

        # Inline error label for project name validation feedback
        self.project_name_error_label = ctk.CTkLabel(
            self._window,
            text="",
            text_color="red",
            anchor="w",
            height=16,
        )
        self.project_name_error_label.grid(
            row=1, column=1, columnspan=2, padx=(0, 16), pady=(0, 4), sticky="w"
        )

        # Project type label + dropdown
        ctk.CTkLabel(
            self._window, text="Project Type:", anchor="w", text_color=COLOR_TEXT,
        ).grid(row=2, column=0, padx=(20, 8), pady=12, sticky="w")
        self.project_type_dropdown = ctk.CTkOptionMenu(
            self._window,
            values=self._get_template_options(),
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY,
            text_color=COLOR_TEXT,
        )
        self.project_type_dropdown.grid(
            row=2, column=1, columnspan=2, padx=(0, 20), pady=12, sticky="ew"
        )

        # Destination path label + entry + browse button
        self.destination_entry = make_browse_row(
            self._window,
            label_text="Destination:",
            browse_command=self._browse_destination,
            placeholder="Select destination folder",
            row=3,
        )

        # Inline error label for destination validation feedback
        self.destination_error_label = ctk.CTkLabel(
            self._window,
            text="",
            text_color="red",
            anchor="w",
            height=16,
        )
        self.destination_error_label.grid(
            row=4, column=1, columnspan=2, padx=(0, 20), pady=(0, 4), sticky="w"
        )

        # Open in VS Code checkbox
        self.open_in_vscode_var = ctk.BooleanVar(value=True)
        self.open_in_vscode_checkbox = ctk.CTkCheckBox(
            self._window,
            text="Open in VS Code",
            variable=self.open_in_vscode_var,
            text_color=COLOR_TEXT,
            fg_color=COLOR_SECONDARY,
            hover_color="#4AA8D4",
        )
        self.open_in_vscode_checkbox.grid(
            row=5, column=0, columnspan=2, padx=20, pady=10, sticky="w"
        )

        # Create Project button
        self.create_button = ctk.CTkButton(
            self._window,
            text="Create Project",
            command=self._on_create_project,
            fg_color=COLOR_SECONDARY,
            hover_color="#4AA8D4",
            text_color=COLOR_TEXT,
            height=40,
        )
        self.create_button.grid(
            row=6, column=0, columnspan=3, padx=20, pady=(20, 24), sticky="ew"
        )

        # Check for Updates button (GUI-010) -- secondary text-link style button.
        self.check_updates_button = ctk.CTkButton(
            self._window,
            text="Check for Updates",
            command=self._on_check_for_updates,
            fg_color="transparent",
            hover_color=COLOR_PRIMARY,
            text_color=COLOR_SECONDARY,
            height=24,
            border_width=0,
        )
        self.check_updates_button.grid(
            row=7, column=0, columnspan=3, padx=20, pady=(0, 4), sticky="e"
        )

        # Update notification banner (GUI-009) -- hidden until an update is detected.
        self.update_banner = ctk.CTkLabel(
            self._window,
            text="",
            text_color="#FFD700",
            anchor="center",
            height=28,
        )
        self.update_banner.grid(
            row=8, column=0, columnspan=3, padx=20, pady=(0, 8), sticky="ew"
        )
        self.update_banner.grid_remove()

        # Version label -- non-editable, always visible, shows installed version.
        # place() is used so it does not disturb the grid layout of other rows.
        self.version_label = ctk.CTkLabel(
            self._window,
            text=f"v{get_display_version()}",
            text_color=COLOR_TEXT,
            anchor="e",
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-8, anchor="se")

        # Disable the VS Code checkbox if VS Code is not detected on startup (GUI-006).
        if find_vscode() is None:
            self.open_in_vscode_checkbox.configure(state="disabled")
            self.open_in_vscode_var.set(False)

    def _browse_destination(self) -> None:
        """Open a native folder browser and populate the destination entry."""
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.destination_entry.delete(0, "end")
            self.destination_entry.insert(0, folder)

    def _on_create_project(self) -> None:
        """Handle Create Project button click."""
        folder_name = self.project_name_entry.get().strip()
        display_template = self.project_type_dropdown.get()
        destination_str = self.destination_entry.get().strip()

        # Clear previous inline errors before re-validating.
        self.project_name_error_label.configure(text="")
        self.destination_error_label.configure(text="")

        name_valid, name_error = validate_folder_name(folder_name)
        if not name_valid:
            self.project_name_error_label.configure(text=name_error)
            return

        dest_valid, dest_error = validate_destination_path(destination_str)
        if not dest_valid:
            self.destination_error_label.configure(text=dest_error)
            return

        if check_duplicate_folder(folder_name, destination_str):
            self.project_name_error_label.configure(
                text=f'A folder named "{folder_name}" already exists at the destination.'
            )
            return

        # Reverse-map the title-cased display name back to the raw template dir name.
        raw_template = next(
            (t for t in list_templates(TEMPLATES_DIR) if _format_template_name(t) == display_template),
            None,
        )
        if raw_template is None:
            messagebox.showerror(
                "Template Not Found",
                f'Could not find a template matching "{display_template}". '
                "Please restart the application and try again.",
            )
            return

        template_path = TEMPLATES_DIR / raw_template
        try:
            created_path = create_project(template_path, Path(destination_str), folder_name)
        except Exception as exc:
            messagebox.showerror("Project Creation Failed", str(exc))
            return

        messagebox.showinfo(
            "Project Created",
            f'Project "{folder_name}" created successfully at:\n{created_path}',
        )

        # Open the new project in VS Code if the checkbox is checked (GUI-006).
        if self.open_in_vscode_var.get():
            open_in_vscode(created_path)

    def _run_update_check(self) -> None:
        """Run in a background thread; posts the result to the main thread via after()."""
        update_available, latest_version = check_for_update(VERSION)
        self._window.after(0, lambda: self._apply_update_result(update_available, latest_version))

    def _apply_update_result(self, update_available: bool, latest_version: str, manual: bool = False) -> None:
        """Update the banner widget. Must be called on the main Tk thread."""
        if update_available:
            self.update_banner.configure(text=f"Update available: v{latest_version}")
            self.update_banner.grid()
        elif manual:
            self.update_banner.configure(text="You're up to date.")
            self.update_banner.grid()
        else:
            self.update_banner.grid_remove()

    def _on_check_for_updates(self) -> None:
        """Handle Check for Updates button click (GUI-010)."""
        self.check_updates_button.configure(state="disabled", text="Checking...")

        def _check() -> None:
            update_available, latest_version = check_for_update(VERSION)
            self._window.after(0, lambda: self._finish_manual_check(update_available, latest_version))

        threading.Thread(target=_check, daemon=True).start()

    def _finish_manual_check(self, update_available: bool, latest_version: str) -> None:
        """Restore button state and apply the result of a manual update check."""
        self.check_updates_button.configure(state="normal", text="Check for Updates")
        self._apply_update_result(update_available, latest_version, manual=True)

    def run(self) -> None:
        """Start the application event loop."""
        self._window.mainloop()