import tkinter as tk

import customtkinter as ctk


def get_results_palette():
    if ctk.get_appearance_mode() == "Light":
        return {
            "card": "#E5E5E5",
            "surface": "#D5D5D5",
            "text": "#1A1A1A",
            "muted": "#666666"
        }

    return {
        "card": "#2B2B2B",
        "surface": "#333333",
        "text": "#DCE4EE",
        "muted": "#8F8F8F"
    }


def create_fast_label(
    parent,
    text,
    *,
    background,
    foreground,
    font,
    anchor="w",
    justify="left",
    wraplength=0,
    padx=0,
    pady=0
):
    return tk.Label(
        parent,
        text=text,
        bg=background,
        fg=foreground,
        font=font,
        anchor=anchor,
        justify=justify,
        wraplength=wraplength,
        padx=padx,
        pady=pady,
        borderwidth=0,
        highlightthickness=0
    )


def create_fast_action(
    parent,
    text,
    command,
    *,
    background,
    hover_background,
    foreground="white",
    font=("Arial", 13),
    width=14
):
    label = tk.Label(
        parent,
        text=text,
        width=width,
        height=2,
        bg=background,
        fg=foreground,
        activebackground=hover_background,
        activeforeground=foreground,
        font=font,
        anchor="center",
        cursor="hand2",
        takefocus=True,
        borderwidth=0,
        highlightthickness=0
    )
    label.normal_background = background
    label.hover_background = hover_background

    def run_command(_event=None):
        command()
        return "break"

    label.bind("<Button-1>", run_command)
    label.bind("<Return>", run_command)
    label.bind("<space>", run_command)
    label.bind(
        "<Enter>",
        lambda _event: label.configure(bg=label.hover_background)
    )
    label.bind(
        "<Leave>",
        lambda _event: label.configure(bg=label.normal_background)
    )
    label.bind(
        "<FocusIn>",
        lambda _event: label.configure(bg=label.hover_background)
    )
    label.bind(
        "<FocusOut>",
        lambda _event: label.configure(bg=label.normal_background)
    )

    return label
