import math
import tkinter as tk

import customtkinter as ctk

from ui.config import APPLICATION_STATUSES, APPLICATION_STATUS_COLORS
from ui.formatters import format_card_location, format_job_date_text, format_saved_at
from ui.lightweight_widgets import create_fast_action, create_fast_label, get_results_palette
from utils.search_engine import SOURCE_KEY_BY_SITE, SOURCE_SITE_BY_KEY


class PresentationMixin:

    def update_ui(self):

        self.search_button.configure(
            state="normal",
            text="Ara",
            fg_color="#1F6AA5",
            hover_color="#155A8E"
        )

        self.prev_button.configure(
            state="normal"
        )

        self.next_button.configure(
            state="normal"
        )

    def update_pagination_controls(self, total_pages):

        self.page_label.configure(
            text=(
                f"Sayfa "
                f"{self.current_page}"
                f" / "
                f"{total_pages}"
            )
        )

        self.prev_button.configure(
            state=(
                "normal"
                if self.current_page > 1
                else "disabled"
            )
        )

        self.next_button.configure(
            state=(
                "normal"
                if self.current_page < total_pages
                else "disabled"
            )
        )

    def render_list_header(self):

        if self.view_mode not in [
            "results",
            "favorites"
        ]:

            return

        header = ctk.CTkFrame(
            self.results_frame,
            corner_radius=16
        )

        header.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        title_text = (
            "Favoriler"
            if self.view_mode == "favorites"
            else "Arama Sonuçları"
        )

        total_text = (
            f"{len(self.filtered_jobs)} / {len(self.favorite_jobs)} favori"
            if self.view_mode == "favorites"
            else f"{len(self.filtered_jobs)} ilan"
        )

        title_label = ctk.CTkLabel(
            header,
            text=title_text,
            font=(
                "Arial",
                20,
                "bold"
            )
        )

        title_label.pack(
            side="left",
            padx=18,
            pady=14
        )

        count_label = ctk.CTkLabel(
            header,
            text=total_text,
            text_color="gray",
            font=(
                "Arial",
                14
            )
        )

        count_label.pack(
            side="left",
            padx=(0, 12)
        )

        if self.view_mode == "results":

            source_counts = {
                source: 0
                for source in SOURCE_SITE_BY_KEY
            }

            source_labels = {
                "kariyer": "Kariyer.net",
                "jooble": "Jooble",
                "eleman": "Eleman.net"
            }

            for job in self.filtered_jobs:

                source = SOURCE_KEY_BY_SITE.get(
                    getattr(
                        job,
                        "site",
                        ""
                    )
                )

                if source:

                    source_counts[source] += 1

            for source, label in source_labels.items():

                source_count = source_counts.get(
                    source,
                    0
                )

                source_status = ctk.CTkLabel(
                    header,
                    text=f"{label}: {source_count}",
                    fg_color="#2F2F2F",
                    corner_radius=10,
                    font=(
                        "Arial",
                        12,
                        "bold"
                    ),
                    padx=10,
                    pady=5
                )

                source_status.pack(
                    side="left",
                    padx=(0, 8)
                )

        if self.view_mode == "favorites":

            status_counts = {
                status: 0
                for status in APPLICATION_STATUSES
            }

            for favorite in self.favorite_jobs:

                status = favorite.get(
                    "application_status",
                    "Kaydedildi"
                )

                if status in status_counts:

                    status_counts[status] += 1

            for status in APPLICATION_STATUSES:

                if status_counts[status] == 0:

                    continue

                status_summary = ctk.CTkButton(
                    header,
                    text=f"{status}: {status_counts[status]}",
                    fg_color=APPLICATION_STATUS_COLORS.get(
                        status,
                        "#3A3A3A"
                    ),
                    hover_color="#4A4A4A",
                    text_color="white",
                    corner_radius=14,
                    height=34,
                    font=(
                        "Arial",
                        12,
                        "bold"
                    ),
                    command=lambda selected_status=status:
                    self.filter_favorites_by_status(
                        selected_status
                    )
                )

                status_summary.pack(
                    side="left",
                    padx=(0, 8)
                )

        if self.view_mode == "favorites":

            action_button = ctk.CTkButton(
                header,
                text="Tüm Favoriler",
                width=140,
                height=34,
                corner_radius=14,
                command=self.clear_favorite_filters
            )

            action_button.pack(
                side="right",
                padx=14,
                pady=12
            )

            export_button = ctk.CTkButton(
                header,
                text="CSV Dışa Aktar",
                width=140,
                height=34,
                corner_radius=14,
                fg_color="#3A3A3A",
                hover_color="#4A4A4A",
                command=self.export_favorites_csv
            )

            export_button.pack(
                side="right",
                padx=(0, 8),
                pady=12
            )

        if self.view_mode == "results":

            errors = self.last_search_report.get(
                "source_errors",
                {}
            )

            if errors:

                warning_text = " ".join(
                    errors.values()
                )

                warning_label = ctk.CTkLabel(
                    header,
                    text=warning_text,
                    text_color="#F1C40F",
                    font=(
                        "Arial",
                        12,
                        "bold"
                    ),
                    wraplength=520,
                    justify="left"
                )

                warning_label.pack(
                    side="right",
                    padx=(0, 10)
                )

    def render_favorites_dashboard(self):

        if self.view_mode != "favorites":

            return

        status_counts = {
            status: 0
            for status in APPLICATION_STATUSES
        }

        notes_count = 0

        for favorite in self.favorite_jobs:

            status = favorite.get(
                "application_status",
                "Kaydedildi"
            )

            if status in status_counts:

                status_counts[status] += 1

            if str(
                favorite.get(
                    "application_note",
                    ""
                )
            ).strip():

                notes_count += 1

        active_count = (
            status_counts.get(
                "Başvuruldu",
                0
            ) +
            status_counts.get(
                "Görüşme",
                0
            ) +
            status_counts.get(
                "Teklif",
                0
            )
        )

        dashboard_items = [
            (
                "Toplam",
                len(self.favorite_jobs),
                "#3A3A3A"
            ),
            (
                "Aktif Süreç",
                active_count,
                "#1F6AA5"
            ),
            (
                "Görüşme",
                status_counts.get(
                    "Görüşme",
                    0
                ),
                "#8E5A00"
            ),
            (
                "Teklif",
                status_counts.get(
                    "Teklif",
                    0
                ),
                "#2E8B57"
            ),
            (
                "Notlu",
                notes_count,
                "#5A4A7A"
            )
        ]

        dashboard = ctk.CTkFrame(
            self.results_frame,
            corner_radius=16
        )

        dashboard.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        for index in range(len(dashboard_items)):

            dashboard.grid_columnconfigure(
                index,
                weight=1,
                uniform="favorites_dashboard"
            )

        for index, (label_text, value, color) in enumerate(dashboard_items):

            card = ctk.CTkFrame(
                dashboard,
                fg_color=color,
                corner_radius=12,
                height=56
            )

            card.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=5,
                pady=8
            )

            card.grid_propagate(False)
            card.grid_rowconfigure(
                0,
                weight=1
            )
            card.grid_rowconfigure(
                3,
                weight=1
            )
            card.grid_columnconfigure(
                0,
                weight=1
            )

            ctk.CTkLabel(
                card,
                text=label_text,
                text_color="#D8D8D8",
                font=(
                    "Arial",
                    11,
                    "bold"
                )
            ).grid(
                row=1,
                column=0,
                pady=(0, 1)
            )

            ctk.CTkLabel(
                card,
                text=str(value),
                text_color="white",
                font=(
                    "Arial",
                    18,
                    "bold"
                )
            ).grid(
                row=2,
                column=0
            )

    def scroll_results_to_top(self):

        if self.view_mode == "results":

            self.fast_results_view.scroll_to_top()
            return

        try:

            self.results_frame.update_idletasks()

            self.results_frame._parent_canvas.yview_moveto(0)

        except Exception:

            try:

                self.results_frame._parent_canvas.yview(
                    "moveto",
                    0
                )

            except Exception:

                pass

    def display_jobs(self, scroll_to_top=False):

        if self.view_mode != "home":

            self.show_results_layout()

        if self.view_mode == "results":

            self.fast_results_view.clear()

        else:

            for widget in self.results_frame.winfo_children():
                widget.destroy()

        self.logo_labels_by_url = {}

        if scroll_to_top:

            self.after(
                10,
                self.scroll_results_to_top
            )

        total_pages = max(
            1,
            math.ceil(
                len(self.filtered_jobs) / self.jobs_per_page
            )
        )

        if self.current_page > total_pages:

            self.current_page = total_pages

        self.update_pagination_controls(
            total_pages
        )

        start = (
            self.current_page - 1
        ) * self.jobs_per_page

        end = (
            start + self.jobs_per_page
        )

        jobs = self.filtered_jobs[
            start:end
        ]

        if self.view_mode == "results":

            self.fast_results_view.render(
                jobs,
                get_results_palette()
            )

            self.update_pagination_controls(
                total_pages
            )

            return

        self.render_list_header()
        self.render_favorites_dashboard()

        if not jobs:

            empty_text = (
                "Favori iş ilanı bulunamadı."
                if self.view_mode == "favorites"
                else "İlan bulunamadı."
            )

            empty_frame = ctk.CTkFrame(
                self.results_frame,
                fg_color="transparent"
            )

            empty_frame.pack(
                fill="both",
                expand=True,
                pady=70
            )

            empty_label = ctk.CTkLabel(

                empty_frame,

                text=empty_text,

                font=(
                    "Arial",
                    22,
                    "bold"
                )
            )

            empty_label.pack(
                pady=(10, 10)
            )

            hint_text = (
                "Favorilere eklediğiniz ilanlar burada görünecek."
                if self.view_mode == "favorites"
                else "Arama kelimesini genişletmeyi veya filtreleri temizlemeyi deneyin."
            )

            hint_label = ctk.CTkLabel(
                empty_frame,
                text=hint_text,
                text_color="gray",
                font=(
                    "Arial",
                    15
                )
            )

            hint_label.pack(
                pady=(0, 22)
            )

            action_button = ctk.CTkButton(
                empty_frame,
                text=(
                    "Ana Sayfaya Dön"
                    if self.view_mode == "favorites"
                    else "Filtreleri Temizle"
                ),
                width=180,
                height=40,
                corner_radius=12,
                command=(
                    self.show_welcome_screen
                    if self.view_mode == "favorites"
                    else self.clear_filters
                )
            )

            action_button.pack()

            return

        palette = get_results_palette()

        for job in jobs:

            card = tk.Frame(
                self.results_frame,
                bg=palette["card"],
                borderwidth=0,
                highlightthickness=0
            )

            card.pack(
                fill="x",
                padx=10,
                pady=10
            )

            header_frame = tk.Frame(
                card,
                bg=palette["card"],
                borderwidth=0,
                highlightthickness=0
            )

            header_frame.pack(
                fill="x",
                padx=20,
                pady=(18, 5)
            )

            logo_frame = tk.Frame(
                header_frame,
                width=64,
                height=64,
                bg=palette["surface"],
                borderwidth=0,
                highlightthickness=0
            )

            logo_frame.pack(
                side="left"
            )

            logo_frame.pack_propagate(False)

            logo_image = self.get_logo_image(job)
            logo_url = getattr(
                job,
                "logo_url",
                ""
            )

            if logo_image:

                logo_label = tk.Label(
                    logo_frame,
                    text="",
                    image=logo_image,
                    bg=palette["surface"],
                    borderwidth=0,
                    highlightthickness=0
                )

            else:

                logo_label = create_fast_label(
                    logo_frame,
                    text=self.get_company_initials(job.company),
                    background=palette["surface"],
                    foreground=palette["text"],
                    font=("Arial", 18, "bold"),
                    anchor="center",
                    justify="center"
                )

            self.register_logo_label(
                logo_url,
                logo_label
            )

            logo_label.pack(
                fill="both",
                expand=True
            )

            title_frame = tk.Frame(
                header_frame,
                bg=palette["card"],
                borderwidth=0,
                highlightthickness=0
            )

            title_frame.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(14, 0)
            )

            title = create_fast_label(
                title_frame,
                text=job.title,
                background=palette["card"],
                foreground=palette["text"],
                font=("Arial", 22, "bold"),
                anchor="w",
                justify="left",
                wraplength=760
            )

            title.pack(
                fill="x",
                anchor="w"
            )

            company = create_fast_label(
                title_frame,
                text=job.company,
                background=palette["card"],
                foreground=palette["text"],
                font=("Arial", 15),
                anchor="w",
                justify="left",
                wraplength=760
            )

            company.pack(
                fill="x",
                anchor="w",
                pady=(5, 0)
            )

            source_name = getattr(
                job,
                "site",
                "Bilinmiyor"
            )

            source_colors = {
                "Kariyer": "#1F6AA5",
                "Jooble": "#2E8B57",
                "Eleman.net": "#7A4DFF"
            }

            source_badge = create_fast_label(

                card,

                text=source_name,

                background=source_colors.get(
                    source_name,
                    "#555555"
                ),

                foreground="white",

                font=(
                    "Arial",
                    12,
                    "bold"
                ),

                padx=10,

                pady=4
            )

            source_badge.pack(
                anchor="w",
                padx=20,
                pady=(8, 0)
            )

            location = create_fast_label(

                card,

                text=f"📍 {format_card_location(job.location)}",

                background=palette["card"],

                foreground=palette["text"],

                font=(
                    "Arial",
                    14
                ),

                anchor="w",

                justify="left",

                wraplength=820
            )

            location.pack(
                anchor="w",
                padx=20,
                pady=(6, 0)
            )

            job_date_text = getattr(
                job,
                "job_date_text",
                ""
            )

            if job_date_text:

                date_label = create_fast_label(

                    card,

                    text=format_job_date_text(
                        job_date_text
                    ),

                    background=palette["card"],

                    foreground=palette["text"],

                    font=("Arial", 13),

                    anchor="w"
                )

                date_label.pack(
                    anchor="w",
                    padx=20,
                    pady=(4, 0)
                )

            favorite_data = self.get_favorite_data(job)
            is_favorite = favorite_data is not None

            application_status = (
                favorite_data.get(
                    "application_status",
                    "Kaydedildi"
                )
                if favorite_data
                else getattr(
                    job,
                    "application_status",
                    "Kaydedildi"
                )
            )

            if (
                self.view_mode == "results" and
                is_favorite
            ):

                favorite_status_badge = create_fast_label(
                    card,
                    text=f"Favoride · {application_status}",
                    background=APPLICATION_STATUS_COLORS.get(
                        application_status,
                        "#3A3A3A"
                    ),
                    foreground="white",
                    font=(
                        "Arial",
                        12,
                        "bold"
                    ),
                    padx=10,
                    pady=4
                )

                favorite_status_badge.pack(
                    anchor="w",
                    padx=20,
                    pady=(6, 0)
                )

            if self.view_mode == "favorites":

                status_badge = create_fast_label(
                    card,
                    text=f"Durum: {application_status}",
                    background=APPLICATION_STATUS_COLORS.get(
                        application_status,
                        "#3A3A3A"
                    ),
                    foreground="white",
                    font=(
                        "Arial",
                        12,
                        "bold"
                    ),
                    padx=10,
                    pady=4
                )

                status_badge.pack(
                    anchor="w",
                    padx=20,
                    pady=(6, 0)
                )

                saved_at = format_saved_at(
                    getattr(
                        job,
                        "saved_at",
                        ""
                    )
                )

                if saved_at:

                    saved_label = create_fast_label(
                        card,
                        text=f"Favoriye eklenme: {saved_at}",
                        background=palette["card"],
                        foreground=palette["muted"],
                        font=(
                            "Arial",
                            13
                        ),
                        anchor="w"
                    )

                    saved_label.pack(
                        anchor="w",
                        padx=20,
                        pady=(5, 0)
                    )

                status_updated_at = format_saved_at(
                    getattr(
                        job,
                        "status_updated_at",
                        ""
                    )
                )

                if status_updated_at:

                    status_date_label = create_fast_label(
                        card,
                        text=f"Durum güncelleme: {status_updated_at}",
                        background=palette["card"],
                        foreground=palette["muted"],
                        font=(
                            "Arial",
                            13
                        ),
                        anchor="w"
                    )

                    status_date_label.pack(
                        anchor="w",
                        padx=20,
                        pady=(3, 0)
                    )

                application_note = getattr(
                    job,
                    "application_note",
                    ""
                ).strip()

                if application_note:

                    note_preview = (
                        application_note[:120] + "..."
                        if len(application_note) > 120
                        else application_note
                    )

                    note_label = create_fast_label(
                        card,
                        text=f"Not: {note_preview}",
                        background=palette["card"],
                        foreground=palette["muted"],
                        font=(
                            "Arial",
                            13
                        ),
                        anchor="w",
                        justify="left",
                        wraplength=760
                    )

                    note_label.pack(
                        fill="x",
                        anchor="w",
                        padx=20,
                        pady=(6, 0)
                    )

            details = create_fast_label(

                card,

                text=(
                    f"Deneyim: {job.experience}   |   "
                    f"Çalışma: {job.remote}"
                ),

                background=palette["card"],

                foreground=palette["text"],

                font=(
                    "Arial",
                    14
                ),

                anchor="w"
            )

            details.pack(
                anchor="w",
                padx=20,
                pady=(6, 18)
            )

            button_frame = tk.Frame(
                card,
                bg=palette["card"],
                borderwidth=0,
                highlightthickness=0
            )

            button_frame.pack(
                fill="x",
                padx=15,
                pady=(0, 15)
            )

            if self.view_mode == "favorites":

                status_var = ctk.StringVar(
                    value=application_status
                )

                status_menu = ctk.CTkOptionMenu(
                    button_frame,
                    values=APPLICATION_STATUSES,
                    variable=status_var,
                    width=150,
                    height=38,
                    corner_radius=12,
                    fg_color="#3A3A3A",
                    button_color="#4A4A4A",
                    button_hover_color="#555555",
                    command=lambda value, j=job:
                    self.update_application_status(
                        j,
                        value
                    )
                )

                status_menu.pack(
                    side="left",
                    padx=5
                )

            if self.view_mode == "favorites":
                open_button = ctk.CTkButton(
                    button_frame,
                    text="Başvuruya Git",
                    command=lambda j=job: self.open_job_link(j),
                    width=150,
                    height=38,
                    corner_radius=12,
                    fg_color="#2E8B57",
                    hover_color="#247348",
                    font=("Arial", 13, "bold")
                )
            else:
                open_button = create_fast_action(
                    button_frame,
                    "Başvuruya Git",
                    lambda j=job: self.open_job_link(j),
                    background="#2E8B57",
                    hover_background="#247348",
                    font=("Arial", 13, "bold"),
                    width=16
                )

            open_button.pack(
                side="right",
                padx=5
            )

            if self.view_mode == "favorites":
                detail_button = ctk.CTkButton(
                    button_frame,
                    text="Detayları Gör",
                    command=lambda j=job: self.show_job_details(j),
                    width=140,
                    height=38,
                    corner_radius=12,
                    fg_color="#3A3A3A",
                    hover_color="#4A4A4A",
                    font=("Arial", 13)
                )
            else:
                detail_button = create_fast_action(
                    button_frame,
                    "Detayları Gör",
                    lambda j=job: self.show_job_details(j),
                    background="#3A3A3A",
                    hover_background="#4A4A4A",
                    width=14
                )

            detail_button.pack(
                side="right",
                padx=5
            )

            if self.view_mode == "favorites":
                favorite_button = ctk.CTkButton(
                    button_frame,
                    text="★ Favoriden Çıkar",
                    command=lambda j=job: self.toggle_favorite(j),
                    width=180,
                    height=38,
                    corner_radius=12,
                    fg_color="#5B3F00",
                    hover_color="#AA3333",
                    font=("Arial", 13)
                )
            else:
                favorite_button = create_fast_action(
                    button_frame,
                    (
                        "★ Favoriden Çıkar"
                        if is_favorite
                        else "★ Favoriye Ekle"
                    ),
                    lambda j=job: self.toggle_favorite(j),
                    background=(
                        "#5B3F00"
                        if is_favorite
                        else "#2F2F2F"
                    ),
                    hover_background=(
                        "#AA3333"
                        if is_favorite
                        else "#4A4A4A"
                    ),
                    font=("Arial", 13),
                    width=20
                )

            favorite_button.pack(
                side="left",
                padx=5
            )

            if (
                self.view_mode == "results" and
                not is_favorite
            ):

                hide_button = create_fast_action(
                    button_frame,
                    "Gizle",
                    lambda j=job: self.hide_job(j),
                    background="#2F2F2F",
                    hover_background="#5A2F2F",
                    width=8
                )

                hide_button.pack(
                    side="left",
                    padx=5
                )

        self.update_pagination_controls(
            total_pages
        )

    def next_page(self):

        total_pages = max(

            1,

            math.ceil(
                len(self.filtered_jobs)
                / self.jobs_per_page
            )
        )

        if self.current_page < total_pages:

            self.push_navigation_state()

            self.current_page += 1

            self.display_jobs(
                scroll_to_top=True
            )

    def prev_page(self):

        if self.current_page > 1:

            self.push_navigation_state()

            self.current_page -= 1

            self.display_jobs(
                scroll_to_top=True
            )
