import queue
import sys

import customtkinter as ctk

from ui.config import APP_NAME, DEFAULT_SETTINGS
from ui.diagnostics import configure_logging
from ui.favorites_mixin import FavoritesMixin
from ui.filters_mixin import FiltersMixin
from ui.home_mixin import HomeViewMixin
from ui.job_details_mixin import JobDetailsMixin
from ui.layout import (
    calculate_compact_scaling,
    calculate_window_layout,
)
from ui.navigation_mixin import NavigationMixin
from ui.presentation_mixin import PresentationMixin
from ui.results_view import ResultsView
from ui.search_mixin import SearchMixin
from ui.settings_mixin import SettingsMixin
from ui.storage import (
    get_favorites_file,
    get_hidden_jobs_file,
    load_settings,
    migrate_legacy_favorites,
    save_settings,
)
from ui.update_mixin import UpdateMixin


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class JobApp(HomeViewMixin, SettingsMixin, SearchMixin, FiltersMixin, PresentationMixin, NavigationMixin, UpdateMixin, FavoritesMixin, JobDetailsMixin, ctk.CTk):

    def __init__(self):

        super().__init__()

        # =========================
        # WINDOW
        # =========================

        self.title(APP_NAME)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_layout = calculate_window_layout(
            screen_width,
            screen_height,
            reserved_height=(
                150 if sys.platform == "darwin" else 100
            ),
            max_height=(
                820 if sys.platform == "darwin" else 860
            )
        )
        self.compact_layout = window_layout.compact

        window_scaling, widget_scaling = calculate_compact_scaling(
            self.compact_layout,
            sys.platform,
            self._get_window_scaling()
        )
        ctk.set_window_scaling(window_scaling)
        ctk.set_widget_scaling(widget_scaling)

        self.geometry(
            f"{window_layout.width}x{window_layout.height}"
            f"+{window_layout.x}+{window_layout.y}"
        )

        self.minsize(
            window_layout.min_width,
            window_layout.min_height
        )

        self.after(
            100,
            self.force_focus
        )

        self.bind_all(
            "<Control-f>",
            self.focus_search_entry
        )

        self.bind_all(
            "<Command-f>",
            self.focus_search_entry
        )

        self.bind_all(
            "<Escape>",
            self.handle_escape
        )

        # =========================
        # DATA
        # =========================

        self.all_jobs = []
        self.filtered_jobs = []
        self.favorite_jobs = []
        self.hidden_jobs = []
        self.toast_label = None
        self.settings = load_settings()
        self.logo_images = {}
        self.logo_placeholder_images = {}
        self.logo_labels_by_url = {}
        self.logo_refresh_queue = queue.SimpleQueue()

        ctk.set_appearance_mode(
            self.settings.get(
                "appearance_mode",
                "dark"
            )
        )

        self.favorites_file = get_favorites_file()
        self.hidden_jobs_file = get_hidden_jobs_file()
        self.last_status_message = "Hazır"
        self.search_summary_message = ""
        self.last_search_report = {}
        self.source_progress = {}
        self.source_progress_labels = {}
        self.current_search_sources = []
        self.latest_release_info = None
        self.update_prompt_window = None
        self.update_check_in_progress = False
        self.search_in_progress = False
        self.search_token = 0
        self.active_cached_search = None
        self.cache_preview_active = False
        self.cache_refresh_failed = False
        self.view_mode = "home"
        self.navigation_history = []
        self.update_back_button_state()

        migrate_legacy_favorites(
            self.favorites_file
        )

        self.jobs_per_page = int(
            self.settings.get(
                "jobs_per_page",
                10
            )
        )

        # =========================
        # MAIN CONTAINER
        # =========================

        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.main_container.pack(
            fill="both",
            expand=True
        )

        # =========================
        # TOP BAR
        # =========================

        self.top_frame = ctk.CTkFrame(
            self.main_container,
            height=60 if self.compact_layout else 70,
            corner_radius=0
        )

        self.top_frame.pack(
            fill="x"
        )

        # BACK BUTTON

        self.back_button = ctk.CTkButton(

            self.top_frame,

            text="<",

            width=38 if self.compact_layout else 42,

            height=38 if self.compact_layout else 42,

            corner_radius=999,

            font=("Arial", 18, "bold"),
            anchor="center",
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.go_back
        )

        self.back_button.pack(
            side="left",
            padx=(14, 6) if self.compact_layout else (20, 8),
            pady=10 if self.compact_layout else 15
        )
        
        # SEARCH ENTRY

        search_group = ctk.CTkFrame(
            self.top_frame,
            fg_color="transparent"
        )

        search_group.pack(
            side="left",
            padx=(10, 6) if self.compact_layout else (18, 10),
            pady=9 if self.compact_layout else 12
        )

        self.keyword_entry = ctk.CTkEntry(

            search_group,

            width=280 if self.compact_layout else 320,

            height=38 if self.compact_layout else 44,

            corner_radius=12,

            placeholder_text="Pozisyon veya keyword ara"
        )

        self.keyword_entry.pack(
            side="left",
            padx=(0, 10)
        )

        last_keyword = self.settings.get(
            "last_keyword",
            ""
        )

        if last_keyword:

            self.keyword_entry.insert(
                0,
                last_keyword
            )

        self.keyword_entry.bind(
            "<Return>",
            lambda event:
            self.start_search()
        )

        # SEARCH BUTTON

        self.search_button = ctk.CTkButton(

            search_group,

            text="Ara",

            width=72 if self.compact_layout else 82,

            height=38 if self.compact_layout else 44,

            corner_radius=12,
            fg_color="#1F6AA5",
            hover_color="#155A8E",
            font=("Arial", 14, "bold"),

            command=self.start_search
        )

        self.search_button.pack(
            side="left",
            padx=(0, 8)
        )

        # LINKEDIN SEARCH BUTTON

        self.linkedin_button = ctk.CTkButton(

            search_group,

            text="LinkedIn'de Ara",

            width=124 if self.compact_layout else 136,

            height=38 if self.compact_layout else 44,

            corner_radius=12,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.open_linkedin_search
        )

        self.linkedin_button.pack(
            side="left",
            padx=0
        )

        nav_group = ctk.CTkFrame(
            self.top_frame,
            fg_color="transparent"
        )

        nav_group.pack(
            side="right",
            padx=(6, 14) if self.compact_layout else (8, 20),
            pady=9 if self.compact_layout else 12
        )

        # FAVORITES BUTTON

        self.favorites_button = ctk.CTkButton(

            nav_group,

            text="★ Favoriler",

            width=106 if self.compact_layout else 118,

            height=38 if self.compact_layout else 44,

            corner_radius=12,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.show_favorites
        )

        self.favorites_button.pack(
            side="right",
            padx=(8, 0)
        )

        # HOME BUTTON

        self.home_button = ctk.CTkButton(

            nav_group,

            text="Ana Sayfa",

            width=108 if self.compact_layout else 120,

            height=38 if self.compact_layout else 44,

            corner_radius=12,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.go_home
        )

        self.home_button.pack(
            side="right",
            padx=(8, 0)
        )

        # SETTINGS BUTTON

        self.settings_button = ctk.CTkButton(

            nav_group,

            text="Ayarlar",

            width=86 if self.compact_layout else 96,

            height=38 if self.compact_layout else 44,

            corner_radius=12,
            fg_color="#2F2F2F",
            hover_color="#454545",

            command=self.show_settings
        )

        self.settings_button.pack(
            side="right",
            padx=(8, 0)
        )

        # =========================
        # CONTENT CONTAINER
        # =========================

        self.content_container = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )

        self.content_container.pack(
            fill="both",
            expand=True,
            padx=6 if self.compact_layout else 10,
            pady=6 if self.compact_layout else 10
        )

        # =========================
        # LEFT SIDEBAR
        # =========================

        self.sidebar = ctk.CTkFrame(
            self.content_container,
            width=245 if self.compact_layout else 280,
            corner_radius=14 if self.compact_layout else 18
        )

        self.sidebar.pack(
            side="left",
            fill="y",
            padx=(3, 7) if self.compact_layout else (5, 10)
        )

        sort_values = [
            "Varsayılan",
            "A-Z Pozisyona Göre",
            "A-Z Şirkete Göre",
            "Junior Önce",
            "Senior Önce",
            "Remote Önce",
            "En Yeni Önce"
        ]
        sort_type = self.settings.get(
            "sort_type",
            "Varsayılan"
        )

        if sort_type not in sort_values:
            sort_type = "Varsayılan"

        self.sort_var = ctk.StringVar(
            value=sort_type
        )

        filter_actions = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        filter_actions.pack(
            side="bottom",
            fill="x",
            padx=0,
            pady=(0, 5) if self.compact_layout else (0, 12)
        )

        sort_label = ctk.CTkLabel(
            filter_actions,
            text="Sıralama",
            font=(
                "Arial",
                10 if self.compact_layout else 13,
                "bold"
            )
        )
        sort_label.pack(
            anchor="w",
            padx=12 if self.compact_layout else 18,
            pady=(0, 2)
        )

        filter_action_row = ctk.CTkFrame(
            filter_actions,
            fg_color="transparent"
        )
        filter_action_row.pack(
            fill="x",
            padx=10 if self.compact_layout else 16
        )

        self.sort_menu = ctk.CTkOptionMenu(
            filter_action_row,
            values=sort_values,
            variable=self.sort_var,
            width=104 if self.compact_layout else 120,
            height=30 if self.compact_layout else 34,
            font=("Arial", 10 if self.compact_layout else 12),
            dropdown_font=("Arial", 10 if self.compact_layout else 12),
            command=lambda _: self.auto_apply_filters()
        )
        self.clear_filter_button = ctk.CTkButton(
            filter_action_row,
            text="Filtreleri Temizle",
            height=30 if self.compact_layout else 36,
            width=104 if self.compact_layout else 120,
            corner_radius=12,
            fg_color="#444444",
            hover_color="#555555",
            font=("Arial", 10 if self.compact_layout else 12),
            command=self.clear_filters
        )

        if self.compact_layout:
            self.sort_menu.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 4)
            )
            self.clear_filter_button.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(4, 0)
            )
        else:
            self.sort_menu.pack(
                fill="x"
            )
            ctk.CTkFrame(
                filter_action_row,
                height=1,
                corner_radius=0,
                fg_color=("#C8C8C8", "#4A4A4A")
            ).pack(
                fill="x",
                pady=(11, 10)
            )
            self.clear_filter_button.pack(
                fill="x"
            )

        # =========================
        # FILTER TITLE
        # =========================

        filter_title = ctk.CTkLabel(

            self.sidebar,

            text="Filtreler",

            font=(
                "Arial",
                19 if self.compact_layout else 22,
                "bold"
            )
        )

        filter_title.pack(
            anchor="w",
            padx=14 if self.compact_layout else 18,
            pady=(5, 2) if self.compact_layout else (14, 10)
        )

        # =========================
        # CITY FILTER
        # =========================

        city_label = ctk.CTkLabel(

            self.sidebar,

            text="İl / İlçe",

            font=(
                "Arial",
                11 if self.compact_layout else 13,
                "bold"
            )
        )

        city_label.pack(
            anchor="w",
            padx=14 if self.compact_layout else 18,
            pady=(1, 1) if self.compact_layout else (4, 4)
        )

        self.city_entry = ctk.CTkEntry(

            self.sidebar,

            width=210 if self.compact_layout else 230,

            height=30 if self.compact_layout else 34,

            corner_radius=10,

            placeholder_text="Şehir veya ilçe ara..."
        )

        self.city_entry.pack(
            padx=16 if self.compact_layout else 20,
            pady=(0, 3) if self.compact_layout else (0, 10)
        )

        default_city = (
            self.settings.get(
                "last_city",
                ""
            ) or
            self.settings.get(
                "default_city",
                ""
            )
        )

        if default_city:

            self.city_entry.insert(
                0,
                default_city
            )

        # =========================
        # SOURCE FILTER
        # =========================

        source_label = ctk.CTkLabel(

            self.sidebar,

            text="Kaynaklar",

            font=(
                "Arial",
                11 if self.compact_layout else 13,
                "bold"
            )
        )

        source_label.pack(
            anchor="w",
            padx=14 if self.compact_layout else 18,
            pady=(1, 1) if self.compact_layout else (4, 5)
        )

        self.source_vars = {}

        selected_sources = self.settings.get(
            "selected_sources",
            DEFAULT_SETTINGS["selected_sources"]
        )

        if not isinstance(selected_sources, list):

            selected_sources = DEFAULT_SETTINGS[
                "selected_sources"
            ]

        source_values = [
            ("kariyer", "Kariyer.net"),
            ("jooble", "Jooble"),
            ("eleman", "Eleman.net")
        ]

        if not self.settings.get(
            "eleman_source_added",
            False
        ):

            if "eleman" not in selected_sources:

                selected_sources.append("eleman")

            self.settings["eleman_source_added"] = True

            save_settings(
                self.settings
            )

        for source_key, source_name in source_values:

            var = ctk.BooleanVar(
                value=source_key in selected_sources
            )

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=source_name,

                variable=var,
                font=("Arial", 11 if self.compact_layout else 12),
                height=18 if self.compact_layout else 22,
                checkbox_width=15 if self.compact_layout else 16,
                checkbox_height=15 if self.compact_layout else 16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=18 if self.compact_layout else 22,
                pady=0 if self.compact_layout else 2
            )

            self.source_vars[source_key] = var

        # Başvuru durumu yalnızca Favoriler ekranındaki durum düğmeleriyle
        # yönetilir; genel filtre panelinde aynı kontrolü tekrar göstermeyiz.
        self.application_status_filter_var = ctk.StringVar(
            value="Tümü"
        )

        # =========================
        # EXPERIENCE FILTER
        # =========================

        experience_label = ctk.CTkLabel(

            self.sidebar,

            text="Deneyim Seviyesi",

            font=(
                "Arial",
                11 if self.compact_layout else 13,
                "bold"
            )
        )

        experience_label.pack(
            anchor="w",
            padx=14 if self.compact_layout else 18,
            pady=(2, 1) if self.compact_layout else (8, 5)
        )

        self.exp_vars = {}

        selected_experiences = self.settings.get(
            "selected_experiences",
            []
        )

        if not isinstance(selected_experiences, list):

            selected_experiences = []

        experience_values = [

            "Stajyer",
            "Junior",
            "Mid-Level",
            "Senior",
            "Manager",
            "Director"
        ]

        experience_options_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        experience_options_frame.pack(
            fill="x",
            padx=14 if self.compact_layout else 18
        )

        for exp in experience_values:

            var = ctk.BooleanVar(
                value=exp in selected_experiences
            )

            checkbox = ctk.CTkCheckBox(

                experience_options_frame,

                text=exp,

                variable=var,
                font=("Arial", 11 if self.compact_layout else 12),
                height=18 if self.compact_layout else 22,
                checkbox_width=15 if self.compact_layout else 16,
                checkbox_height=15 if self.compact_layout else 16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=4,
                pady=0 if self.compact_layout else 2
            )

            self.exp_vars[exp] = var

        # =========================
        # REMOTE FILTER
        # =========================

        remote_label = ctk.CTkLabel(

            self.sidebar,

            text="Çalışma Şekli",

            font=(
                "Arial",
                11 if self.compact_layout else 13,
                "bold"
            )
        )

        remote_label.pack(
            anchor="w",
            padx=14 if self.compact_layout else 18,
            pady=(2, 1) if self.compact_layout else (8, 5)
        )

        self.remote_vars = {}

        selected_remote = self.settings.get(
            "selected_remote",
            []
        )

        if not isinstance(selected_remote, list):

            selected_remote = []

        remote_values = [

            "Ofis",
            "Hibrit",
            "Remote"
        ]

        for remote in remote_values:

            var = ctk.BooleanVar(
                value=remote in selected_remote
            )

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=remote,

                variable=var,
                font=("Arial", 11 if self.compact_layout else 12),
                height=18 if self.compact_layout else 22,
                checkbox_width=15 if self.compact_layout else 16,
                checkbox_height=15 if self.compact_layout else 16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=18 if self.compact_layout else 22,
                pady=0 if self.compact_layout else 2
            )

            self.remote_vars[remote] = var

        # =========================
        # RIGHT CONTENT
        # =========================

        self.right_content = ctk.CTkFrame(
            self.content_container,
            fg_color="transparent"
        )

        self.right_content.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.status_label = ctk.CTkLabel(

            self.right_content,

            text=self.last_status_message,

            font=(
                "Arial",
                14
            ),

            anchor="w"
        )

        self.status_label.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        self.source_progress_frame = ctk.CTkFrame(
            self.right_content,
            fg_color="transparent"
        )

        self.source_progress_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        self.home_frame = ctk.CTkFrame(
            self.right_content,
            corner_radius=18
        )

        # =========================
        # RESULTS FRAME
        # =========================

        self.results_frame = ctk.CTkScrollableFrame(

            self.right_content,

            corner_radius=18
        )

        self.results_frame.pack(
            fill="both",
            expand=True,
            pady=(0, 10)
        )

        self.fast_results_container = ctk.CTkFrame(
            self.right_content,
            corner_radius=18,
            fg_color=("#E3E3E3", "#292929")
        )

        self.fast_results_view = ResultsView(
            self.fast_results_container,
            self
        )

        self.fast_results_view.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        # =========================
        # PAGINATION
        # =========================

        self.pagination_frame = ctk.CTkFrame(
            self.right_content,
            corner_radius=15
        )

        self.pagination_frame.pack(
            fill="x"
        )

        self.prev_button = ctk.CTkButton(

            self.pagination_frame,

            text="← Önceki",

            width=120,

            height=40,
            corner_radius=12,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.prev_page
        )

        self.prev_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        self.page_label = ctk.CTkLabel(

            self.pagination_frame,

            text="Sayfa 1",

            font=(
                "Arial",
                15,
                "bold"
            )
        )

        self.page_label.pack(
            side="left",
            padx=20
        )

        self.next_button = ctk.CTkButton(

            self.pagination_frame,

            text="Sonraki →",

            width=120,

            height=40,
            corner_radius=12,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.next_page
        )

        self.next_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        self.load_favorites()
        self.load_hidden_jobs()

        self.after(
            100,
            self.poll_logo_refresh_queue
        )

        self.show_welcome_screen()

        self.after(
            800,
            self.show_install_cleanup_prompt
        )

        self.after(
            1200,
            lambda:
            self.check_for_updates(silent=True)
        )

    # =========================
    # BACK
    # =========================








    # =========================
    # TOAST MESSAGE
    # =========================








































if __name__ == "__main__":

    configure_logging()

    app = JobApp()

    app.mainloop()
