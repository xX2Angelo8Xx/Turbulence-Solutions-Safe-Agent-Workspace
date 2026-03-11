"""Main application window for the Turbulence Solutions Launcher."""

from __future__ import annotations

import tkinter.filedialog as filedialog

import customtkinter as ctk

from launcher.config import APP_NAME
from launcher.gui.components import make_browse_row, make_label_entry_row

_WINDOW_WIDTH: int = 580
_WINDOW_HEIGHT: int = 340


class App:
    """Main GUI application window."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._window = ctk.CTk()
        self._window.title(APP_NAME)
        self._window.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")
        self._window.resizable(False, False)
        self._build_ui()

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

        # Project type label + dropdown
        ctk.CTkLabel(self._window, text="Project Type:", anchor="w").grid(
            row=1, column=0, padx=(16, 8), pady=8, sticky="w"
        )
        self.project_type_dropdown = ctk.CTkOptionMenu(
            self._window,
            values=["Coding"],
        )
        self.project_type_dropdown.grid(
            row=1, column=1, columnspan=2, padx=(0, 16), pady=8, sticky="ew"
        )

        # Destination path label + entry + browse button
        self.destination_entry = make_browse_row(
            self._window,
            label_text="Destination:",
            browse_command=self._browse_destination,
            placeholder="Select destination folder",
            row=2,
        )

        # Open in VS Code checkbox
        self.open_in_vscode_var = ctk.BooleanVar(value=True)
        self.open_in_vscode_checkbox = ctk.CTkCheckBox(
            self._window,
            text="Open in VS Code",
            variable=self.open_in_vscode_var,
        )
        self.open_in_vscode_checkbox.grid(
            row=3, column=0, columnspan=2, padx=16, pady=8, sticky="w"
        )

        # Create Project button
        self.create_button = ctk.CTkButton(
            self._window,
            text="Create Project",
            command=self._on_create_project,
        )
        self.create_button.grid(
            row=4, column=0, columnspan=3, padx=16, pady=(16, 20)
        )

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
