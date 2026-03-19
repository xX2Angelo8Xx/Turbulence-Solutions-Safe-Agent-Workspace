"""Main application window for the Turbulence Solutions Launcher."""

from __future__ import annotations

import sys
import threading
import time
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path

import customtkinter as ctk

from launcher.config import APP_NAME, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, LOGO_ICO_PATH, LOGO_PATH, TEMPLATES_DIR, VERSION, get_display_version
from launcher.core.updater import check_for_update
from launcher.core.downloader import download_update
from launcher.core.applier import apply_update
from launcher.core.project_creator import create_project, is_template_ready, list_templates
from launcher.core.shim_config import read_python_path, write_python_path
from launcher.core.vscode import find_vscode, open_in_vscode
from launcher.gui.components import make_browse_row, make_label_entry_row
from launcher.gui.validation import (
    check_duplicate_folder,
    validate_destination_path,
    validate_folder_name,
)

_WINDOW_WIDTH: int = 580
_WINDOW_HEIGHT: int = 590


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
        # Tracks the latest available version so the install handler can use it.
        self._latest_version: str = VERSION
        # Initialized before _build_ui so the dropdown builder can populate them.
        self._coming_soon_options: set[str] = set()
        self._current_template: str = ""
        self._build_ui()
        # Set window icon from TS-Logo (GUI-013 / FIX-016).
        # Windows: use wm_iconbitmap with .ico for correct taskbar icon.
        # Other platforms: use iconphoto with .png.
        try:
            if sys.platform == "win32":
                self._window.wm_iconbitmap(str(LOGO_ICO_PATH))
            else:
                from PIL import Image, ImageTk
                _icon_img = Image.open(str(LOGO_PATH))
                self._icon_photo = ImageTk.PhotoImage(_icon_img)
                self._window.iconphoto(True, self._icon_photo)
        except Exception:
            pass
        # Silent background update check on launch (GUI-009).
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _get_template_options(self) -> list[str]:
        names = list_templates(TEMPLATES_DIR)
        all_options: list[str] = []
        coming_soon: set[str] = set()
        for name in names:
            display = _format_template_name(name)
            if not is_template_ready(TEMPLATES_DIR, name):
                display = f"{display} ...coming soon"
                coming_soon.add(display)
            all_options.append(display)
        # Store coming-soon set as a side effect so _build_ui and _on_template_selected
        # can access it without a second scan.
        self._coming_soon_options = coming_soon
        return all_options

    def _build_ui(self) -> None:
        """Construct and arrange all UI widgets."""
        self._window.grid_columnconfigure(1, weight=1)

        # Logo header (GUI-013) -- brand logo at the top of the window.
        try:
            from PIL import Image
            _logo_img = Image.open(str(LOGO_PATH))
            _target_height = 50
            _target_width = int(_logo_img.width * (_target_height / _logo_img.height))
            self._logo_ctk = ctk.CTkImage(
                light_image=_logo_img, dark_image=_logo_img, size=(_target_width, _target_height)
            )
            self.logo_label = ctk.CTkLabel(
                self._window,
                image=self._logo_ctk,
                text="",
            )
            self.logo_label.grid(
                row=0, column=0, columnspan=3, padx=20, pady=(12, 4)
            )
        except Exception:
            pass

        # Project name label + entry
        self.project_name_entry = make_label_entry_row(
            self._window,
            label_text="Project Name:",
            placeholder="MatlabDemo",
            row=1,
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
            row=2, column=1, columnspan=2, padx=(0, 16), pady=(0, 4), sticky="w"
        )

        # Project type label + dropdown
        ctk.CTkLabel(
            self._window, text="Project Type:", anchor="w", text_color=COLOR_TEXT,
        ).grid(row=3, column=0, padx=(20, 8), pady=12, sticky="w")
        options = self._get_template_options()  # also populates self._coming_soon_options
        ready_options = [o for o in options if o not in self._coming_soon_options]
        # Default to the first ready template so coming-soon items are never pre-selected.
        self._current_template = ready_options[0] if ready_options else (options[0] if options else "")
        self.project_type_dropdown = ctk.CTkOptionMenu(
            self._window,
            values=options if options else [""],
            command=self._on_template_selected,
            fg_color=COLOR_SECONDARY,
            button_color=COLOR_SECONDARY,
            text_color=COLOR_TEXT,
        )
        if self._current_template:
            self.project_type_dropdown.set(self._current_template)
        self.project_type_dropdown.grid(
            row=3, column=1, columnspan=2, padx=(0, 20), pady=12, sticky="ew"
        )

        # Destination path label + entry + browse button
        self.destination_entry = make_browse_row(
            self._window,
            label_text="Destination:",
            browse_command=self._browse_destination,
            placeholder="Select destination folder",
            row=4,
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
            row=5, column=1, columnspan=2, padx=(0, 20), pady=(0, 4), sticky="w"
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
            row=6, column=0, columnspan=2, padx=20, pady=10, sticky="w"
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
            row=7, column=0, columnspan=3, padx=20, pady=(20, 24), sticky="ew"
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
            row=8, column=0, columnspan=3, padx=20, pady=(0, 4), sticky="e"
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
            row=9, column=0, columnspan=3, padx=20, pady=(0, 8), sticky="ew"
        )
        self.update_banner.grid_remove()

        # Download & Install Update button (INS-011) -- shown only when update available.
        self.download_install_button = ctk.CTkButton(
            self._window,
            text="Download & Install Update",
            command=self._on_install_update,
            fg_color=COLOR_SECONDARY,
            hover_color="#4AA8D4",
            text_color=COLOR_TEXT,
            height=32,
        )
        self.download_install_button.grid(
            row=10, column=0, columnspan=3, padx=20, pady=(0, 8), sticky="ew"
        )
        self.download_install_button.grid_remove()

        # Version label -- non-editable, always visible, shows installed version.
        # place() is used so it does not disturb the grid layout of other rows.
        self.version_label = ctk.CTkLabel(
            self._window,
            text=f"v{get_display_version()}",
            text_color=COLOR_TEXT,
            anchor="e",
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-8, anchor="se")

        # Settings gear button (GUI-018) -- top-right corner, opens settings dialog.
        self.settings_button = ctk.CTkButton(
            self._window,
            text="⚙",
            command=self._open_settings_dialog,
            fg_color="transparent",
            hover_color=COLOR_PRIMARY,
            text_color=COLOR_SECONDARY,
            width=32,
            height=32,
            border_width=0,
        )
        self.settings_button.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")

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

    def _on_template_selected(self, value: str) -> None:
        """Prevent selection of coming-soon templates by reverting to the previous valid choice."""
        if value in self._coming_soon_options:
            self.project_type_dropdown.set(self._current_template)
            return
        self._current_template = value

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

        if check_duplicate_folder(f"TS-SAE-{folder_name}", destination_str):
            self.project_name_error_label.configure(
                text=f'A folder named "TS-SAE-{folder_name}" already exists at the destination.'
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
            f'Project "TS-SAE-{folder_name}" created successfully at:\n{created_path}',
        )

        # Open the new project in VS Code if the checkbox is checked (GUI-006).
        if self.open_in_vscode_var.get():
            open_in_vscode(created_path)

    def _run_update_check(self) -> None:
        """Run in a background thread; posts the result to the main thread via after()."""
        update_available, latest_version = check_for_update(VERSION)
        self._window.after(0, lambda: self._apply_update_result(update_available, latest_version))

    def _apply_update_result(self, update_available: bool, latest_version: str, manual: bool = False) -> None:
        """Update the banner and install button. Must be called on the main Tk thread."""
        if update_available:
            self._latest_version = latest_version
            self.update_banner.configure(text=f"Update available: v{latest_version}")
            self.update_banner.grid()
            self.download_install_button.grid()
        elif manual:
            self.update_banner.configure(text="You're up to date.")
            self.update_banner.grid()
            self.download_install_button.grid_remove()
        else:
            self.update_banner.grid_remove()
            self.download_install_button.grid_remove()

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

    def _on_install_update(self) -> None:
        """Handle Download & Install Update button click (INS-011).

        Runs the download in a background thread to keep the UI responsive,
        then calls apply_update() on success.  Errors are surfaced to the user
        via a messagebox rather than crashing silently.
        """
        version = self._latest_version
        self.download_install_button.configure(
            state="disabled", text="Downloading..."
        )

        def _download_and_apply() -> None:
            try:
                installer_path = download_update(version)
            except Exception as exc:  # noqa: BLE001
                self._window.after(
                    0,
                    lambda: self._on_install_error(f"Download failed: {exc}"),
                )
                return
            # Update UI to inform the user before os._exit() terminates the process.
            self._window.after(0, self._on_install_starting)
            time.sleep(0.5)
            try:
                apply_update(installer_path)
            except Exception as exc:  # noqa: BLE001
                self._window.after(
                    0,
                    lambda: self._on_install_error(f"Install failed: {exc}"),
                )

        threading.Thread(target=_download_and_apply, daemon=True).start()

    def _on_install_starting(self) -> None:
        """Update UI to indicate the installer is launching."""
        self.download_install_button.configure(state="disabled", text="Installing...")
        self.update_banner.configure(text="Installing update... App will restart.")
        self.update_banner.grid()

    def _on_install_error(self, message: str) -> None:
        """Restore the install button and show an error dialog."""
        self.download_install_button.configure(
            state="normal", text="Download & Install Update"
        )
        messagebox.showerror("Update Failed", message)

    def _open_settings_dialog(self) -> None:
        """Open the Settings dialog (GUI-018)."""
        SettingsDialog(self._window)

    def run(self) -> None:
        """Start the application event loop."""
        self._window.mainloop()


class SettingsDialog:
    """Settings dialog for the launcher (GUI-018).

    Opens a CTkToplevel window with a 'Relocate Python Runtime' section
    that lets the user auto-detect or manually browse to the Python executable
    and persists the path via shim_config.write_python_path().
    """

    def __init__(self, parent: ctk.CTk) -> None:
        self._dialog = ctk.CTkToplevel(parent)
        self._dialog.title("Settings")
        self._dialog.geometry("480x280")
        self._dialog.resizable(False, False)
        self._dialog.configure(fg_color=COLOR_PRIMARY)
        self._dialog.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the settings dialog widgets."""
        # Section title
        ctk.CTkLabel(
            self._dialog,
            text="Relocate Python Runtime",
            text_color=COLOR_TEXT,
            font=("", 14, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(16, 4), sticky="w")

        # Current path read-out
        ctk.CTkLabel(
            self._dialog,
            text="Current path:",
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=1, column=0, padx=(20, 8), pady=4, sticky="w")

        current = read_python_path()
        current_text = str(current) if current is not None else "Not configured"
        self._current_path_label = ctk.CTkLabel(
            self._dialog,
            text=current_text,
            text_color=COLOR_SECONDARY,
            anchor="w",
            wraplength=300,
        )
        self._current_path_label.grid(row=1, column=1, columnspan=2, padx=(0, 20), pady=4, sticky="w")

        # Auto-detect button
        self._auto_detect_button = ctk.CTkButton(
            self._dialog,
            text="Auto-detect",
            command=self._on_auto_detect,
            fg_color=COLOR_SECONDARY,
            hover_color="#4AA8D4",
            text_color=COLOR_TEXT,
            height=36,
        )
        self._auto_detect_button.grid(row=2, column=0, padx=(20, 8), pady=(12, 4), sticky="ew")

        # Browse button
        self._browse_button = ctk.CTkButton(
            self._dialog,
            text="Browse...",
            command=self._on_browse,
            fg_color=COLOR_SECONDARY,
            hover_color="#4AA8D4",
            text_color=COLOR_TEXT,
            height=36,
        )
        self._browse_button.grid(row=2, column=1, padx=(0, 8), pady=(12, 4), sticky="ew")

        # Close button
        self._close_button = ctk.CTkButton(
            self._dialog,
            text="Close",
            command=self._dialog.destroy,
            fg_color="transparent",
            hover_color=COLOR_PRIMARY,
            text_color=COLOR_SECONDARY,
            height=36,
            border_width=1,
            border_color=COLOR_SECONDARY,
        )
        self._close_button.grid(row=3, column=0, columnspan=3, padx=20, pady=(16, 12), sticky="ew")

    def _on_auto_detect(self) -> None:
        """Auto-detect the python-embed directory from the launcher's install location."""
        python_exe = self._find_bundled_python()
        if python_exe is None or not python_exe.exists():
            messagebox.showerror(
                "Auto-detect Failed",
                "Could not find a bundled Python runtime at the expected location.\n"
                "Please use 'Browse...' to locate python.exe manually.",
                parent=self._dialog,
            )
            return
        write_python_path(python_exe)
        self._current_path_label.configure(text=str(python_exe))
        messagebox.showinfo(
            "Python Runtime Updated",
            f"Python runtime path updated to:\n{python_exe}",
            parent=self._dialog,
        )

    def _find_bundled_python(self) -> "Path | None":
        """Return the expected bundled Python executable path.

        Checks sys._MEIPASS first (PyInstaller bundle), then falls back to
        the grandparent of sys.executable (development layout).
        """
        if hasattr(sys, "_MEIPASS"):
            # Running from a PyInstaller bundle: MEIPASS is the _internal dir.
            # The python-embed folder sits next to the launcher executable.
            exe_dir = Path(sys.executable).parent
        else:
            # Development: sys.executable is .venv/Scripts/python.exe –
            # go up two levels to the repo root, mirroring the install layout.
            exe_dir = Path(sys.executable).parent.parent

        if sys.platform == "win32":
            return exe_dir / "python-embed" / "python.exe"
        else:
            return exe_dir / "python-embed" / "python3"

    def _on_browse(self) -> None:
        """Open a file browser to locate the Python executable."""
        if sys.platform == "win32":
            filetypes = [("Python executable", "python.exe"), ("All files", "*.*")]
        else:
            filetypes = [("Python executable", "python python3"), ("All files", "*")]

        path_str = filedialog.askopenfilename(
            title="Select Python Executable",
            filetypes=filetypes,
            parent=self._dialog,
        )
        if not path_str:
            return
        python_exe = Path(path_str)
        write_python_path(python_exe)
        self._current_path_label.configure(text=str(python_exe))
        messagebox.showinfo(
            "Python Runtime Updated",
            f"Python runtime path updated to:\n{python_exe}",
            parent=self._dialog,
        )