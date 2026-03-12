"""Reusable GUI component builders for the Turbulence Solutions Launcher."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from launcher.config import COLOR_SECONDARY, COLOR_TEXT


def make_label_entry_row(
    parent: ctk.CTk,
    label_text: str,
    placeholder: str = "",
    row: int = 0,
) -> ctk.CTkEntry:
    """Add a labelled entry widget at the given grid row and return the entry."""
    ctk.CTkLabel(parent, text=label_text, anchor="w", text_color=COLOR_TEXT).grid(
        row=row, column=0, padx=(20, 8), pady=12, sticky="w"
    )
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder, text_color=COLOR_TEXT)
    entry.grid(row=row, column=1, columnspan=2, padx=(0, 20), pady=12, sticky="ew")
    return entry


def make_browse_row(
    parent: ctk.CTk,
    label_text: str,
    browse_command: Callable[[], None],
    placeholder: str = "",
    row: int = 0,
) -> ctk.CTkEntry:
    """Add a labelled entry with a Browse button at the given grid row."""
    ctk.CTkLabel(parent, text=label_text, anchor="w", text_color=COLOR_TEXT).grid(
        row=row, column=0, padx=(20, 8), pady=12, sticky="w"
    )
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder, text_color=COLOR_TEXT)
    entry.grid(row=row, column=1, padx=(0, 8), pady=12, sticky="ew")
    ctk.CTkButton(
        parent,
        text="Browse",
        width=80,
        command=browse_command,
        fg_color=COLOR_SECONDARY,
        hover_color="#4AA8D4",
        text_color=COLOR_TEXT,
    ).grid(row=row, column=2, padx=(0, 20), pady=12)
    return entry
