"""Reusable GUI component builders for the Turbulence Solutions Launcher."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


def make_label_entry_row(
    parent: ctk.CTk,
    label_text: str,
    placeholder: str = "",
    row: int = 0,
) -> ctk.CTkEntry:
    """Add a labelled entry widget at the given grid row and return the entry."""
    ctk.CTkLabel(parent, text=label_text, anchor="w").grid(
        row=row, column=0, padx=(16, 8), pady=8, sticky="w"
    )
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
    entry.grid(row=row, column=1, columnspan=2, padx=(0, 16), pady=8, sticky="ew")
    return entry


def make_browse_row(
    parent: ctk.CTk,
    label_text: str,
    browse_command: Callable[[], None],
    placeholder: str = "",
    row: int = 0,
) -> ctk.CTkEntry:
    """Add a labelled entry with a Browse button at the given grid row."""
    ctk.CTkLabel(parent, text=label_text, anchor="w").grid(
        row=row, column=0, padx=(16, 8), pady=8, sticky="w"
    )
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
    entry.grid(row=row, column=1, padx=(0, 8), pady=8, sticky="ew")
    ctk.CTkButton(parent, text="Browse", width=80, command=browse_command).grid(
        row=row, column=2, padx=(0, 16), pady=8
    )
    return entry
