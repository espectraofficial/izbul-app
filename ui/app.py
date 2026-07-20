import queue

import customtkinter as ctk

from ui.config import APPLICATION_STATUSES, APP_NAME, DEFAULT_SETTINGS
from ui.diagnostics import configure_logging
from ui.favorites_mixin import FavoritesMixin
from ui.filters_mixin import FiltersMixin
from ui.home_mixin import HomeViewMixin
from ui.job_details_mixin import JobDetailsMixin
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

        window_width = min(
            1500,
            max(
                1300,
                int(screen_width * 0.92)
            )
        )
        window_height = min(
            900,
            max(
                750,
                int((screen_height - 80) * 0.92)
            )
        )

        x = int((screen_width - window_width) / 2)
        y = int(((screen_height - window_height) / 2) - 60)

        if y < 30:
            y = 30

        self.geometry(
            f"{window_width}x{window_height}+{x}+{y}"
        )

        self.minsize(1300, 750)

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
            height=70,
            corner_radius=0
        )

        self.top_frame.pack(
            fill="x"
        )

        # BACK BUTTON

        self.back_button = ctk.CTkButton(

            self.top_frame,

            text="<",

            width=42,

            height=42,

            corner_radius=999,

            font=("Arial", 18, "bold"),
            anchor="center",
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=self.go_back
        )

        self.back_button.pack(
            side="left",
            padx=(20, 8),
            pady=15
        )
        
        # SEARCH ENTRY

        search_group = ctk.CTkFrame(
            self.top_frame,
            fg_color="transparent"
        )

        search_group.pack(
            side="left",
            padx=(18, 10),
            pady=12
        )

        self.keyword_entry = ctk.CTkEntry(

            search_group,

            width=320,

            height=44,

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

            width=82,

            height=44,

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

            width=136,

            height=44,

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
            padx=(8, 20),
            pady=12
        )

        # FAVORITES BUTTON

        self.favorites_button = ctk.CTkButton(

            nav_group,

            text="★ Favoriler",

            width=118,

            height=44,

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

            width=120,

            height=44,

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

            width=96,

            height=44,

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
            padx=10,
            pady=10
        )

        # =========================
        # LEFT SIDEBAR
        # =========================

        self.sidebar = ctk.CTkFrame(
            self.content_container,
            width=280,
            corner_radius=18
        )

        self.sidebar.pack(
            side="left",
            fill="y",
            padx=(5, 10)
        )

        # =========================
        # FILTER TITLE
        # =========================

        filter_title = ctk.CTkLabel(

            self.sidebar,

            text="Filtreler",

            font=(
                "Arial",
                22,
                "bold"
            )
        )

        filter_title.pack(
            anchor="w",
            padx=18,
            pady=(14, 10)
        )

        # =========================
        # CITY FILTER
        # =========================

        city_label = ctk.CTkLabel(

            self.sidebar,

            text="İl / İlçe",

            font=(
                "Arial",
                13,
                "bold"
            )
        )

        city_label.pack(
            anchor="w",
            padx=18,
            pady=(4, 4)
        )

        self.city_entry = ctk.CTkEntry(

            self.sidebar,

            width=230,

            height=34,

            corner_radius=10,

            placeholder_text="Şehir veya ilçe ara..."
        )

        self.city_entry.pack(
            padx=20,
            pady=(0, 10)
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
                13,
                "bold"
            )
        )

        source_label.pack(
            anchor="w",
            padx=18,
            pady=(4, 5)
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
                font=("Arial", 12),
                height=22,
                checkbox_width=16,
                checkbox_height=16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=22,
                pady=2
            )

            self.source_vars[source_key] = var

        status_filter_label = ctk.CTkLabel(

            self.sidebar,

            text="Başvuru Durumu",

            font=(
                "Arial",
                13,
                "bold"
            )
        )

        status_filter_label.pack(
            anchor="w",
            padx=18,
            pady=(8, 5)
        )

        selected_application_statuses = self.settings.get(
            "selected_application_statuses",
            []
        )

        if not isinstance(selected_application_statuses, list):

            selected_application_statuses = []

        self.application_status_filter_var = ctk.StringVar(
            value=(
                selected_application_statuses[0]
                if len(selected_application_statuses) == 1
                else "Tümü"
            )
        )

        self.application_status_filter_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "Tümü",
                *APPLICATION_STATUSES
            ],
            variable=self.application_status_filter_var,
            width=230,
            height=34,
            command=lambda _:
            self.auto_apply_filters()
        )

        self.application_status_filter_menu.pack(
            padx=18,
            pady=(0, 8)
        )

        # =========================
        # EXPERIENCE FILTER
        # =========================

        experience_label = ctk.CTkLabel(

            self.sidebar,

            text="Deneyim Seviyesi",

            font=(
                "Arial",
                13,
                "bold"
            )
        )

        experience_label.pack(
            anchor="w",
            padx=18,
            pady=(8, 5)
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

        for exp in experience_values:

            var = ctk.BooleanVar(
                value=exp in selected_experiences
            )

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=exp,

                variable=var,
                font=("Arial", 12),
                height=22,
                checkbox_width=16,
                checkbox_height=16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=22,
                pady=2
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
                13,
                "bold"
            )
        )

        remote_label.pack(
            anchor="w",
            padx=18,
            pady=(8, 5)
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
                font=("Arial", 12),
                height=22,
                checkbox_width=16,
                checkbox_height=16,
                command=self.auto_apply_filters
            )

            checkbox.pack(
                anchor="w",
                padx=22,
                pady=2
            )

            self.remote_vars[remote] = var

        # =========================
        # SORTING 
        # =========================

        sort_label = ctk.CTkLabel(

            self.sidebar,

            text="Sıralama",

            font=(
                "Arial",
                13,
                "bold"
            )
        )

        sort_label.pack(
            anchor="w",
            padx=18,
            pady=(8, 5)
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

        self.sort_menu = ctk.CTkOptionMenu(

            self.sidebar,

            values=sort_values,

            variable=self.sort_var,

            width=230,

            height=34,

            command=lambda _:
            self.auto_apply_filters()
        )

        self.sort_menu.pack(
            padx=18,
            pady=(0, 8)
        )

        # =========================
        # APPLY FILTER BUTTON
        # =========================

        filter_actions = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        filter_actions.pack(
            side="bottom",
            fill="x",
            padx=0,
            pady=(0, 12)
        )

        self.clear_filter_button = ctk.CTkButton(

            filter_actions,

            text="Filtreleri Temizle",

            height=36,

            corner_radius=12,

            fg_color="#444444",

            hover_color="#555555",

            command=self.clear_filters
        )

        self.clear_filter_button.pack(
            padx=18,
            pady=(0, 0),
            fill="x"
        )

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
