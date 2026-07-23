import customtkinter as ctk

from scrapers.jooble import get_jooble_api_key


class HomeViewMixin:

    def show_home_layout(self):

        for widget in [
            self.status_label,
            self.source_progress_frame,
            self.results_frame,
            self.fast_results_container,
            self.pagination_frame
        ]:

            widget.pack_forget()

        self.home_frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )

    def show_results_layout(self):

        self.home_frame.pack_forget()

        for widget in [
            self.status_label,
            self.source_progress_frame,
            self.results_frame,
            self.fast_results_container,
            self.pagination_frame
        ]:

            widget.pack_forget()

        self.status_label.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        if (
            self.view_mode == "results" and
            self.source_progress_frame.winfo_children()
        ):

            self.source_progress_frame.pack(
                fill="x",
                padx=10,
                pady=(0, 8)
            )

        results_widget = (
            self.fast_results_container
            if self.view_mode == "results"
            else self.results_frame
        )

        self.pagination_frame.pack(
            side="bottom",
            fill="x"
        )

        results_widget.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )

    def show_welcome_screen(self):

        self.view_mode = "home"
        self.show_home_layout()
        compact = bool(
            getattr(self, "compact_layout", False)
        )

        self.filtered_jobs = []
        self.current_page = 1

        self.page_label.configure(
            text="Ana Sayfa"
        )

        self.prev_button.configure(
            state="disabled"
        )

        self.next_button.configure(
            state="disabled"
        )

        for widget in self.home_frame.winfo_children():
            widget.destroy()

        container = ctk.CTkFrame(
            self.home_frame,
            corner_radius=20
        )

        container.pack(
            fill="both",
            expand=True,
            padx=8 if compact else 16,
            pady=8 if compact else 16
        )

        title = ctk.CTkLabel(

            container,

            text="🔍 İzbul",

            font=(
                "Arial",
                30 if compact else 42,
                "bold"
            )
        )

        title.pack(
            pady=(8, 4) if compact else (18, 8)
        )

        active_sources = [
            source
            for source, var in self.source_vars.items()
            if var.get()
        ]

        jooble_ready = bool(get_jooble_api_key())
        default_city = self.settings.get(
            "default_city",
            ""
        ).strip()

        subtitle = ctk.CTkLabel(

            container,

            text=(
                "Kariyer.net, Jooble ve Eleman.net ilanlarını\n"
                "tek ekranda arayın, filtreleyin ve favorileyin."

            ),

            justify="center",

            font=(
                "Arial",
                14 if compact else 18
            )
        )

        subtitle.pack(
            pady=(0, 8) if compact else (0, 16)
        )

        status_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        status_frame.pack(
            anchor="center",
            pady=(0, 8) if compact else (0, 12),
            expand=True
        )

        status_items = [
            (
                "Kaynak",
                f"{len(active_sources)} aktif"
            ),
            (
                "Jooble",
                "Hazır" if jooble_ready else "API anahtarı gerekli"
            ),
            (
                "Favoriler",
                str(len(self.favorite_jobs))
            ),
            (
                "Varsayılan şehir",
                default_city if default_city else "Seçilmedi"
            )
        ]

        for index, (label_text, value_text) in enumerate(status_items):

            status_frame.grid_columnconfigure(
                index,
                weight=1,
                uniform="home_status"
            )

            status_card = ctk.CTkFrame(
                status_frame,
                width=142 if compact else 168,
                height=58 if compact else 74,
                corner_radius=12 if compact else 14
            )

            status_card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=6
            )

            status_card.pack_propagate(False)
            status_card.grid_propagate(False)
            status_card.grid_rowconfigure(
                0,
                weight=1
            )
            status_card.grid_rowconfigure(
                3,
                weight=1
            )
            status_card.grid_columnconfigure(
                0,
                weight=1
            )

            ctk.CTkLabel(
                status_card,
                text=label_text,
                text_color="gray",
                wraplength=116 if compact else 132,
                font=(
                    "Arial",
                    10 if compact else 12
                ),
                anchor="center",
                justify="center"
            ).grid(
                row=1,
                column=0,
                pady=(0, 2) if compact else (0, 4)
            )

            ctk.CTkLabel(
                status_card,
                text=value_text,
                wraplength=120 if compact else 140,
                font=(
                    "Arial",
                    12 if compact else 14,
                    "bold"
                ),
                anchor="center",
                justify="center"
            ).grid(
                row=2,
                column=0
            )

        if not jooble_ready:

            setup_button = ctk.CTkButton(
                container,
                text="Jooble API Anahtarını Ekle",
                width=205 if compact else 230,
                height=32 if compact else 38,
                corner_radius=10,
                command=self.show_settings
            )

            setup_button.pack(
                pady=(0, 8) if compact else (0, 16)
            )
        else:

            ctk.CTkLabel(
                container,
                text="",
                height=1
            ).pack(
                pady=(0, 2)
            )

        frequent_label = ctk.CTkLabel(
            container,
            text="Sık yapılan aramalar:",
            text_color="#D8DEE9",
            font=(
                "Arial",
                13 if compact else 15,
                "bold"
            )
        )

        frequent_label.pack(
            pady=(0, 4) if compact else (0, 8)
        )

        quick_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        quick_frame.pack(
            fill="x",
            padx=32 if compact else 90,
            pady=(0, 8) if compact else (0, 10),
            expand=True
        )

        quick_jobs = [

            "İnsan Kaynakları",
            "Yazılım",
            "Pazarlama",
            "Mimar"
        ]

        for index, job in enumerate(quick_jobs):

            quick_frame.grid_columnconfigure(
                index,
                weight=1,
                uniform="quick_search"
            )

            btn = ctk.CTkButton(

                quick_frame,

                text=job,

                height=34 if compact else 42,

                corner_radius=12,

                command=lambda j=job:
                self.quick_search(j)
            )

            btn.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=7
            )

        search_history = self.settings.get(
            "search_history",
            []
        )

        if isinstance(search_history, list) and search_history:

            recent_label = ctk.CTkLabel(
                container,
                text="Son aramalar",
                text_color="gray",
                font=(
                    "Arial",
                    13,
                    "bold"
                )
            )

            recent_label.pack(
                pady=(0, 3) if compact else (0, 6)
            )

            recent_frame = ctk.CTkFrame(
                container,
                fg_color="transparent"
            )

            recent_frame.pack(
                fill="x",
                padx=45 if compact else 140,
                pady=(0, 8) if compact else (0, 12),
                expand=True
            )

            recent_index = 0

            for history_item in search_history[:4]:

                if not isinstance(history_item, dict):

                    continue

                keyword = str(
                    history_item.get(
                        "keyword",
                        ""
                    )
                ).strip()

                city = str(
                    history_item.get(
                        "city",
                        ""
                    )
                ).strip()

                if not keyword:

                    continue

                recent_frame.grid_columnconfigure(
                    recent_index,
                    weight=1,
                    uniform="recent_search"
                )

                button_text = (
                    f"{keyword} · {city}"
                    if city
                    else keyword
                )

                has_saved_filters = any(
                    [
                        history_item.get("experiences"),
                        history_item.get("remote"),
                        history_item.get("sort_type") not in [
                            "",
                            "Varsayılan",
                            None
                        ]
                    ]
                )

                if has_saved_filters:

                    button_text = f"{button_text} · filtreli"

                recent_button = ctk.CTkButton(
                    recent_frame,
                    text=button_text,
                    height=28 if compact else 32,
                    corner_radius=10,
                    fg_color="#3A3A3A",
                    hover_color="#4A4A4A",
                    command=lambda item=history_item:
                    self.run_history_search(
                        item
                    )
                )

                recent_button.grid(
                    row=0,
                    column=recent_index,
                    sticky="ew",
                    padx=6
                )

                recent_index += 1

        features_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        features_frame.pack(
            fill="x",
            padx=20 if compact else 44,
            pady=(2, 6) if compact else (4, 12),
            expand=True
        )

        features = [

            (
                "⚡ Hızlı Arama",
                "Seçili kaynaklarda aynı anda arama yapar."
            ),

            (
                "🎯 Gelişmiş Filtreler",
                "Şehir, deneyim ve çalışma modeli filtreleme desteği."
            ),

            (
                "⭐ Favoriler",
                "İlgilendiğiniz ilanları uygulama içinde saklar."
            ),

            (
                "🚫 İlan Gizleme",
                "İlgilenmediğiniz ilanları sonuçlardan saklar."
            )
        ]

        for index in range(len(features)):

            features_frame.grid_columnconfigure(
                index,
                weight=1,
                uniform="home_features"
            )

        for index, (title_text, desc) in enumerate(features):

            card = ctk.CTkFrame(
                features_frame,
                height=84 if compact else 128,
                corner_radius=12 if compact else 16
            )

            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=8
            )

            card.pack_propagate(False)
            card.grid_propagate(False)
            card.grid_columnconfigure(
                0,
                weight=1
            )

            title_label = ctk.CTkLabel(

                card,

                text=title_text,

                font=(
                    "Arial",
                    14 if compact else 17,
                    "bold"
                ),
                anchor="center",
                justify="center"
            )

            title_label.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=10,
                pady=(10, 4) if compact else (18, 8)
            )

            desc_label = ctk.CTkLabel(

                card,

                text=desc,

                wraplength=150 if compact else 180,

                justify="center",

                font=(
                    "Arial",
                    11 if compact else 13
                ),
                anchor="center"
            )

            desc_label.grid(
                row=1,
                column=0,
                sticky="n",
                padx=12
            )

    def quick_search(self, keyword):

        self.keyword_entry.delete(
            0,
            "end"
        )

        self.keyword_entry.insert(
            0,
            keyword
        )

        self.start_search()

    def run_history_search(self, history_item, city=None):

        if isinstance(history_item, dict):

            keyword = str(
                history_item.get(
                    "keyword",
                    ""
                )
            ).strip()

            city = str(
                history_item.get(
                    "city",
                    ""
                )
            ).strip()

            sources = history_item.get(
                "sources",
                None
            )

            experiences = history_item.get(
                "experiences",
                []
            )

            remote_models = history_item.get(
                "remote",
                []
            )

            sort_type = history_item.get(
                "sort_type",
                ""
            )

            if isinstance(sources, list):

                for source, var in self.source_vars.items():

                    var.set(
                        source in sources
                    )

            if isinstance(experiences, list):

                for exp, var in self.exp_vars.items():

                    var.set(
                        exp in experiences
                    )

            if isinstance(remote_models, list):

                for remote, var in self.remote_vars.items():

                    var.set(
                        remote in remote_models
                    )

            if sort_type:

                self.sort_var.set(sort_type)

        else:

            keyword = str(
                history_item or ""
            ).strip()

            city = str(
                city or ""
            ).strip()

        self.keyword_entry.delete(
            0,
            "end"
        )

        self.keyword_entry.insert(
            0,
            keyword
        )

        self.city_entry.delete(
            0,
            "end"
        )

        if city:

            self.city_entry.insert(
                0,
                city
            )

        self.start_search()
