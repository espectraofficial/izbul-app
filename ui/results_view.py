import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from ui.formatters import format_card_location, format_job_date_text
from utils.search_engine import SOURCE_KEY_BY_SITE


class TreeLogoTarget:
    def __init__(self, view, item_id):
        self.view = view
        self.item_id = item_id

    def winfo_exists(self):
        return bool(
            self.view.winfo_exists() and
            self.view.tree.exists(self.item_id)
        )

    def configure(self, **kwargs):
        image = kwargs.get("image")

        if image is None or not self.winfo_exists():
            return

        self.view.image_references.append(image)
        self.view.tree.item(
            self.item_id,
            image=image,
            text=""
        )


class ResultsView(tk.Frame):
    COLUMNS = (
        "title",
        "company",
        "source",
        "location",
        "experience",
        "remote",
        "date"
    )

    def __init__(self, master, owner):
        super().__init__(
            master,
            borderwidth=0,
            highlightthickness=0
        )
        self.owner = owner
        self.jobs = []
        self.palette = {}
        self.jobs_by_item = {}
        self.image_references = []

        self.header = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="transparent"
        )
        self.header.pack(fill="x", pady=(0, 8))

        self.table_header = ctk.CTkFrame(
            self,
            corner_radius=0,
            height=30
        )
        self.table_header.pack(
            fill="x",
            padx=(0, 12)
        )

        self.list_frame = tk.Frame(
            self,
            borderwidth=0,
            highlightthickness=0
        )
        self.list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            self.list_frame,
            columns=self.COLUMNS,
            show="tree",
            selectmode="browse",
            style="Results.Treeview"
        )
        self.scrollbar = ctk.CTkScrollbar(
            self.list_frame,
            orientation="vertical",
            width=12,
            corner_radius=8,
            button_color="#555555",
            button_hover_color="#6A6A6A",
            command=self.tree.yview
        )
        self.tree.configure(
            yscrollcommand=self.scrollbar.set
        )
        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )
        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.action_bar = ctk.CTkFrame(
            self,
            height=54,
            corner_radius=12,
            fg_color="transparent"
        )
        self.action_bar.pack(fill="x")
        self.action_bar.pack_propagate(False)

        self.favorite_button = ctk.CTkButton(
            self.action_bar,
            text="★ Favoriye Ekle",
            command=self.toggle_selected_favorite,
            fg_color="#2F2F2F",
            hover_color="#4A4A4A",
            width=170,
            height=36,
            corner_radius=12
        )
        self.favorite_button.pack(
            side="left",
            padx=(14, 5),
            pady=9
        )
        self.hide_button = ctk.CTkButton(
            self.action_bar,
            text="Gizle",
            command=self.hide_selected,
            fg_color="#2F2F2F",
            hover_color="#5A2F2F",
            width=80,
            height=36,
            corner_radius=12
        )
        self.hide_button.pack(
            side="left",
            padx=5,
            pady=9
        )
        self.apply_button = ctk.CTkButton(
            self.action_bar,
            text="Başvuruya Git",
            command=self.open_selected,
            fg_color="#2E8B57",
            hover_color="#247348",
            font=("Arial", 13, "bold"),
            width=142,
            height=36,
            corner_radius=12
        )
        self.apply_button.pack(
            side="right",
            padx=(5, 14),
            pady=9
        )
        self.detail_button = ctk.CTkButton(
            self.action_bar,
            text="Detayları Gör",
            command=self.show_selected_details,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            width=126,
            height=36,
            corner_radius=12
        )
        self.detail_button.pack(
            side="right",
            padx=5,
            pady=9
        )

        self.configure_columns()
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_changed)
        self.tree.bind("<Double-1>", self.show_selected_details)
        self.tree.bind("<Return>", self.show_selected_details)

        self.action_bar.pack_forget()
        self.action_bar.pack(side="bottom", fill="x")
        self.list_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)

    def configure_columns(self):
        widths = self.get_column_widths()
        logo_width = widths.pop("logo")
        self.tree.column(
            "#0",
            width=logo_width,
            minwidth=logo_width,
            stretch=False
        )

        for column in self.COLUMNS:
            self.tree.column(
                column,
                width=widths[column],
                minwidth=70,
                stretch=column in {"title", "company", "location"},
                anchor="w"
            )

    def get_column_widths(self):
        compact = bool(
            getattr(self.owner, "compact_layout", False)
        )
        if compact:
            return {
                "logo": 96,
                "title": 180,
                "company": 150,
                "source": 74,
                "location": 120,
                "experience": 76,
                "remote": 68,
                "date": 90
            }

        return {
            "logo": 100,
            "title": 245,
            "company": 210,
            "source": 90,
            "location": 175,
            "experience": 90,
            "remote": 82,
            "date": 115
        }

    def render(self, jobs, palette):
        self.jobs = list(jobs)
        self.palette = dict(palette)
        self.apply_palette()
        self.draw_header()
        self.draw_table_header()
        self.clear_rows()
        self.owner.logo_labels_by_url = {}

        for index, job in enumerate(self.jobs):
            logo_image = self.owner.get_logo_image(job)
            display_image = logo_image or self.owner.get_logo_placeholder(
                getattr(job, "company", ""),
                size=50
            )
            item_id = self.tree.insert(
                "",
                "end",
                image=display_image,
                text="",
                values=(
                    self.trim(getattr(job, "title", ""), 54),
                    self.trim(getattr(job, "company", ""), 42),
                    getattr(job, "site", "Bilinmiyor"),
                    self.trim(format_card_location(job.location), 34),
                    getattr(job, "experience", "Belirtilmemiş"),
                    getattr(job, "remote", "Belirtilmemiş"),
                    self.format_table_date(
                        getattr(job, "job_date_text", "")
                    )
                ),
                tags=("even" if index % 2 == 0 else "odd",)
            )
            self.jobs_by_item[item_id] = job

            self.image_references.append(display_image)

            logo_url = getattr(job, "logo_url", "")
            if logo_url:
                self.owner.register_logo_label(
                    logo_url,
                    TreeLogoTarget(self, item_id)
                )

        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

        self.on_selection_changed()

    def apply_palette(self):
        palette = self.palette
        compact = bool(
            getattr(self.owner, "compact_layout", False)
        )
        outer = (
            "#F2F2F2"
            if palette["text"] == "#1A1A1A"
            else "#242424"
        )
        alternate = (
            "#DCDCDC"
            if palette["text"] == "#1A1A1A"
            else "#303030"
        )
        selection = (
            "#3979A6"
            if palette["text"] == "#1A1A1A"
            else "#285F86"
        )
        self.configure(bg=outer)
        self.header.configure(fg_color=palette["card"])
        self.list_frame.configure(bg=outer)
        self.action_bar.configure(fg_color=palette["card"])
        self.scrollbar.configure(
            fg_color=palette["card"],
            button_color=("#A8A8A8", "#555555"),
            button_hover_color=("#909090", "#6A6A6A")
        )

        style = ttk.Style(self)
        style.configure(
            "Results.Treeview",
            background=palette["card"],
            fieldbackground=palette["card"],
            foreground=palette["text"],
            borderwidth=0,
            relief="flat",
            rowheight=56 if compact else 62,
            font=("Arial", 11 if compact else 12)
        )
        style.configure(
            "Results.Treeview.Heading",
            background=palette["surface"],
            foreground=palette["text"],
            relief="flat",
            borderwidth=0,
            padding=(6, 5) if compact else (8, 7),
            font=("Arial", 11 if compact else 12, "bold")
        )
        style.map(
            "Results.Treeview",
            background=[("selected", selection)],
            foreground=[("selected", "white")]
        )
        self.tree.tag_configure("even", background=palette["card"])
        self.tree.tag_configure("odd", background=alternate)

    def draw_table_header(self):
        for widget in self.table_header.winfo_children():
            widget.destroy()

        compact = bool(
            getattr(self.owner, "compact_layout", False)
        )
        headings = (
            ("", "logo"),
            ("Pozisyon", "title"),
            ("Firma", "company"),
            ("Kaynak", "source"),
            ("Konum", "location"),
            ("Deneyim", "experience"),
            ("Çalışma", "remote"),
            ("Yayın tarihi", "date")
        )
        widths = self.get_column_widths()
        self.table_header.configure(
            fg_color=self.palette["surface"]
        )

        for index, (text, column) in enumerate(headings):
            self.table_header.grid_columnconfigure(
                index,
                weight=widths[column],
                uniform="results_columns"
            )
            ctk.CTkLabel(
                self.table_header,
                text=text,
                text_color=self.palette["text"],
                font=(
                    "Arial",
                    10 if compact else 12,
                    "bold"
                ),
                height=27 if compact else 31,
                anchor="w"
            ).grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(5, 2)
            )

    def draw_header(self):
        for widget in self.header.winfo_children():
            widget.destroy()

        palette = self.palette
        compact = bool(
            getattr(self.owner, "compact_layout", False)
        )
        counts = {"kariyer": 0, "jooble": 0, "eleman": 0}
        for job in self.owner.filtered_jobs:
            source = SOURCE_KEY_BY_SITE.get(getattr(job, "site", ""))
            if source:
                counts[source] += 1

        ctk.CTkLabel(
            self.header,
            text="Arama Sonuçları",
            text_color=palette["text"],
            font=("Arial", 17 if compact else 20, "bold")
        ).pack(
            side="left",
            padx=(12, 7) if compact else (18, 10),
            pady=7 if compact else 10
        )
        ctk.CTkLabel(
            self.header,
            text=f"{len(self.owner.filtered_jobs)} ilan",
            text_color=palette["muted"],
            font=("Arial", 12 if compact else 14)
        ).pack(
            side="left",
            padx=(0, 7) if compact else (0, 12)
        )

        for source, label in (
            ("kariyer", "Kariyer.net"),
            ("jooble", "Jooble"),
            ("eleman", "Eleman.net")
        ):
            ctk.CTkLabel(
                self.header,
                text=(
                    f"{label.replace('.net', '')}: {counts[source]}"
                    if compact
                    else f"{label}: {counts[source]}"
                ),
                fg_color=palette["surface"],
                text_color=palette["text"],
                corner_radius=9,
                height=26 if compact else 30,
                padx=7 if compact else 10,
                font=("Arial", 11 if compact else 12, "bold")
            ).pack(side="left", padx=2 if compact else 4)

    def clear(self):
        self.clear_rows()

    def clear_rows(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        self.jobs_by_item.clear()
        self.image_references.clear()

    def scroll_to_top(self):
        self.tree.yview_moveto(0)

    def get_selected_job(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.jobs_by_item.get(selection[0])

    def on_selection_changed(self, _event=None):
        job = self.get_selected_job()
        is_favorite = bool(job and self.owner.get_favorite_data(job))
        self.favorite_button.configure(
            text="★ Favoriden Çıkar" if is_favorite else "★ Favoriye Ekle",
            fg_color="#5B3F00" if is_favorite else "#2F2F2F",
            hover_color="#AA3333" if is_favorite else "#4A4A4A"
        )

    def toggle_selected_favorite(self):
        job = self.get_selected_job()
        if job:
            self.owner.toggle_favorite(job)

    def hide_selected(self):
        job = self.get_selected_job()
        if job:
            self.owner.hide_job(job)

    def show_selected_details(self, _event=None):
        job = self.get_selected_job()
        if job:
            self.owner.show_job_details(job)
        return "break"

    def open_selected(self):
        job = self.get_selected_job()
        if job:
            self.owner.open_job_link(job)

    @staticmethod
    def trim(value, limit):
        text = str(value or "")
        return text if len(text) <= limit else text[:limit - 3].rstrip() + "..."

    @staticmethod
    def format_table_date(value):
        return format_job_date_text(value).removeprefix(
            "Yayınlandığı tarih: "
        )
