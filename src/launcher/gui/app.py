"""Main application window for the Turbulence Solutions Launcher."""

from __future__ import annotations

import tkinter.filedialog as filedialog

import customtkinter as ctk

from launcher.config import APP_NAME, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, TEMPLATES_DIR, get_display_version
from launcher.core.project_creator import list_templates
from launcher.gui.components import make_browse_row, make_label_entry_row
from launcher.gui.validation import (
    check_duplicate_folder,
    validate_destination_path,
    validate_folder_name,
)

_WINDOW_WIDTH: int = 580
_WINDOW_HEIGHT: int = 440


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

        # Version label — non-editable, always visible, shows installed version.
        # place() is used so it does not disturb the grid layout of other rows.
        self.version_label = ctk.CTkLabel(
            self._window,
            text=f"v{get_display_version()}",
            text_color=COLOR_TEXT,
            anchor="e",
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-8, anchor="se")

    def _browse_destination(self) -> None:
        """Open a native folder browser and populate the destination entry."""
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder:
            self.destination_entry.delete(0, "end")
            self.destination_entry.insert(0, folder)

    def _on_create_project(self) -> None:
        """Handle Create Project button click. Full logic added in GUI-005."""
        pass

    def run(self) -> None:
        """Start the application event loop."""
        self._window.mainloop()
