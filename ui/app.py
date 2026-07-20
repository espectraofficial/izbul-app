import customtkinter as ctk
import tkinter as tk
import threading
import math
import queue
import webbrowser
from urllib.parse import quote_plus

from scrapers.jooble import (
    get_jooble_api_key,
    save_jooble_api_key,
    search_jooble
)
from ui.config import (
    APP_NAME,
    APP_VERSION,
    APPLICATION_STATUSES,
    APPLICATION_STATUS_COLORS,
    DEFAULT_SETTINGS,
    get_theme_label,
    get_theme_value
)
from ui.favorites_mixin import FavoritesMixin
from ui.job_details_mixin import JobDetailsMixin
from ui.formatters import (
    format_card_location,
    format_job_date_text,
    format_saved_at
)
from ui.storage import (
    get_app_data_dir,
    get_favorites_file,
    get_hidden_jobs_file,
    load_settings,
    migrate_legacy_favorites,
    save_settings
)
from ui.navigation_mixin import NavigationMixin
from ui.results_view import ResultsView
from ui.lightweight_widgets import (
    create_fast_action,
    create_fast_label,
    get_results_palette
)
from ui.update_mixin import UpdateMixin
from utils.search_engine import (
    SOURCE_KEY_BY_SITE,
    SOURCE_SITE_BY_KEY,
    smart_search,
    normalize_text
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

EXPERIENCE_ASC_PRIORITY = {
    "Stajyer": 0,
    "Junior": 1,
    "Mid-Level": 2,
    "Senior": 3,
    "Manager": 4,
    "Director": 5
}

EXPERIENCE_DESC_PRIORITY = {
    "Director": 0,
    "Manager": 1,
    "Senior": 2,
    "Mid-Level": 3,
    "Junior": 4,
    "Stajyer": 5
}

REMOTE_PRIORITY = {
    "Remote": 0,
    "Hibrit": 1,
    "Ofis": 2
}


class JobApp(NavigationMixin, UpdateMixin, FavoritesMixin, JobDetailsMixin, ctk.CTk):

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
            padx=16,
            pady=16
        )

        title = ctk.CTkLabel(

            container,

            text="🔍 İzbul",

            font=(
                "Arial",
                42,
                "bold"
            )
        )

        title.pack(
            pady=(18, 8)
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
                18
            )
        )

        subtitle.pack(
            pady=(0, 16)
        )

        status_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        status_frame.pack(
            anchor="center",
            pady=(0, 16)
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
                width=168,
                height=74,
                corner_radius=14
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
                wraplength=132,
                font=(
                    "Arial",
                    12
                ),
                anchor="center",
                justify="center"
            ).grid(
                row=1,
                column=0,
                pady=(0, 4)
            )

            ctk.CTkLabel(
                status_card,
                text=value_text,
                wraplength=140,
                font=(
                    "Arial",
                    14,
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
                width=230,
                height=38,
                corner_radius=10,
                command=self.show_settings
            )

            setup_button.pack(
                pady=(0, 16)
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
                15,
                "bold"
            )
        )

        frequent_label.pack(
            pady=(0, 8)
        )

        quick_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        quick_frame.pack(
            fill="x",
            padx=90,
            pady=(0, 14)
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

                height=42,

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
                pady=(0, 6)
            )

            recent_frame = ctk.CTkFrame(
                container,
                fg_color="transparent"
            )

            recent_frame.pack(
                fill="x",
                padx=140,
                pady=(0, 18)
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
                    height=32,
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
            padx=44,
            pady=(4, 14)
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
                height=112,
                corner_radius=16
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
                    17,
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
                pady=(18, 8)
            )

            desc_label = ctk.CTkLabel(

                card,

                text=desc,

                wraplength=180,

                justify="center",

                font=(
                    "Arial",
                    13
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

    def open_linkedin_search(self):

        keyword = (
            self.keyword_entry.get()
            .strip()
        )

        city = (
            self.city_entry.get()
            .strip()
        )

        if not keyword:

            self.show_toast(
                "Önce pozisyon veya keyword yazın.",
                "#C0392B"
            )

            return

        url = (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={quote_plus(keyword)}"
        )

        if city:

            url += f"&location={quote_plus(city)}"

        webbrowser.open(url)

    def show_settings(self):

        settings_window = ctk.CTkToplevel(self)

        settings_window.title("Ayarlar")

        settings_window.geometry("560x640")

        settings_window.resizable(False, False)

        settings_window.transient(self)

        settings_window.focus_force()

        container = ctk.CTkScrollableFrame(
            settings_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        title = ctk.CTkLabel(

            container,

            text="Ayarlar",

            font=(
                "Arial",
                28,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            padx=22,
            pady=(22, 20)
        )

        api_label = ctk.CTkLabel(
            container,
            text="Jooble API Key",
            font=("Arial", 14, "bold")
        )

        api_label.pack(
            anchor="w",
            padx=22,
            pady=(0, 6)
        )

        api_entry = ctk.CTkEntry(
            container,
            width=460,
            height=40,
            show="*"
        )

        api_entry.pack(
            padx=22,
            pady=(0, 8)
        )

        api_actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        api_actions.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        api_visible = ctk.BooleanVar(
            value=False
        )

        def toggle_api_visibility():

            api_visible.set(
                not api_visible.get()
            )

            api_entry.configure(
                show="" if api_visible.get() else "*"
            )

            toggle_api_button.configure(
                text="Gizle" if api_visible.get() else "Göster"
            )

        toggle_api_button = ctk.CTkButton(

            api_actions,

            text="Göster",

            width=100,

            height=34,

            fg_color="#444444",

            hover_color="#555555",

            command=toggle_api_visibility
        )

        toggle_api_button.pack(
            side="left"
        )

        current_key = get_jooble_api_key()

        if current_key:

            api_entry.insert(
                0,
                current_key
            )

        city_label = ctk.CTkLabel(
            container,
            text="Varsayılan şehir",
            font=("Arial", 14, "bold")
        )

        city_label.pack(
            anchor="w",
            padx=22,
            pady=(0, 6)
        )

        city_entry = ctk.CTkEntry(
            container,
            width=460,
            height=40
        )

        city_entry.pack(
            padx=22,
            pady=(0, 16)
        )

        city_entry.insert(
            0,
            self.settings.get(
                "default_city",
                ""
            )
        )

        page_label = ctk.CTkLabel(
            container,
            text="Sayfa başına ilan",
            font=("Arial", 14, "bold")
        )

        page_label.pack(
            anchor="w",
            padx=22,
            pady=(0, 6)
        )

        page_entry = ctk.CTkEntry(
            container,
            width=460,
            height=40
        )

        page_entry.pack(
            padx=22,
            pady=(0, 16)
        )

        page_entry.insert(
            0,
            str(self.jobs_per_page)
        )

        theme_label = ctk.CTkLabel(
            container,
            text="Tema",
            font=("Arial", 14, "bold")
        )

        theme_label.pack(
            anchor="w",
            padx=22,
            pady=(0, 6)
        )

        theme_var = ctk.StringVar(
            value=get_theme_label(
                self.settings.get(
                    "appearance_mode",
                    "dark"
                )
            )
        )

        theme_menu = ctk.CTkOptionMenu(
            container,
            values=[
                "Koyu",
                "Açık",
                "Sistem"
            ],
            variable=theme_var,
            width=460,
            height=40
        )

        theme_menu.pack(
            padx=22,
            pady=(0, 22)
        )

        settings_status = ctk.CTkLabel(

            container,

            text="",

            font=("Arial", 13, "bold"),

            text_color="#27AE60"
        )

        settings_status.pack(
            fill="x",
            padx=22,
            pady=(0, 12)
        )

        def set_settings_status(message, color="#27AE60"):

            settings_status.configure(
                text=message,
                text_color=color
            )

        def test_jooble_connection():

            api_key = api_entry.get().strip()

            if not api_key:

                set_settings_status(
                    "Jooble API key boş.",
                    "#C0392B"
                )

                return

            test_button.configure(
                state="disabled",
                text="Test ediliyor..."
            )

            set_settings_status(
                "Jooble bağlantısı test ediliyor...",
                "#1F6AA5"
            )

            def run_test():

                try:

                    save_jooble_api_key(api_key)

                    jobs = search_jooble(
                        "software",
                        "İstanbul",
                        results_on_page=1,
                        raise_errors=True
                    )

                    message = (
                        "Jooble bağlantısı başarılı."
                        if jobs
                        else "Bağlantı başarılı, sonuç bulunamadı."
                    )

                    self.after(
                        0,
                        lambda:
                        set_settings_status(
                            message,
                            "#27AE60"
                        )
                    )

                except Exception as e:

                    error_message = (
                        f"Jooble bağlantısı başarısız: {e}"
                    )

                    self.after(
                        0,
                        lambda:
                        set_settings_status(
                            error_message,
                            "#C0392B"
                        )
                    )

                finally:

                    self.after(
                        0,
                        lambda:
                        test_button.configure(
                            state="normal",
                            text="Bağlantıyı Test Et"
                        )
                    )

            threading.Thread(
                target=run_test,
                daemon=True
            ).start()

        def reset_settings_form():

            api_entry.delete(
                0,
                "end"
            )

            city_entry.delete(
                0,
                "end"
            )

            page_entry.delete(
                0,
                "end"
            )

            page_entry.insert(
                0,
                str(DEFAULT_SETTINGS["jobs_per_page"])
            )

            theme_var.set(
                get_theme_label(
                    DEFAULT_SETTINGS["appearance_mode"]
                )
            )

            set_settings_status(
                "Form varsayılan değerlere döndü.",
                "#1F6AA5"
            )

        secondary_actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        secondary_actions.pack(
            fill="x",
            padx=22,
            pady=(0, 14)
        )

        test_button = ctk.CTkButton(

            secondary_actions,

            text="Bağlantıyı Test Et",

            height=38,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=test_jooble_connection
        )

        test_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        reset_button = ctk.CTkButton(

            secondary_actions,

            text="Sıfırla",

            height=38,

            fg_color="#5A2F2F",

            hover_color="#744040",

            command=reset_settings_form
        )

        reset_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        hidden_info = ctk.CTkLabel(
            container,
            text=f"Gizlenen ilanlar: {len(self.hidden_jobs)}",
            text_color="gray",
            font=(
                "Arial",
                13
            ),
            anchor="w"
        )

        hidden_info.pack(
            fill="x",
            padx=22,
            pady=(0, 8)
        )

        def clear_hidden_from_settings():

            self.clear_hidden_jobs()

            hidden_info.configure(
                text="Gizlenen ilanlar: 0"
            )

            set_settings_status(
                "Gizlenen ilanlar temizlendi.",
                "#27AE60"
            )

        hidden_actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        hidden_actions.pack(
            fill="x",
            padx=22,
            pady=(0, 14)
        )

        show_hidden_button = ctk.CTkButton(
            hidden_actions,
            text="Gizlenenleri Görüntüle",
            height=38,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=self.show_hidden_jobs_window
        )

        show_hidden_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        clear_hidden_button = ctk.CTkButton(
            hidden_actions,
            text="Temizle",
            height=38,
            fg_color="#5A2F2F",
            hover_color="#744040",
            command=clear_hidden_from_settings
        )

        clear_hidden_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

        update_label = ctk.CTkLabel(
            container,
            text=f"Güncellemeler: mevcut sürüm {APP_VERSION}",
            text_color="gray",
            font=(
                "Arial",
                13
            ),
            anchor="w"
        )

        update_label.pack(
            fill="x",
            padx=22,
            pady=(0, 8)
        )

        update_actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        update_actions.pack(
            fill="x",
            padx=22,
            pady=(0, 14)
        )

        download_update_button = ctk.CTkButton(
            update_actions,
            text="İndir ve Kur",
            height=38,
            fg_color="#2E8B57",
            hover_color="#247348",
            command=self.open_latest_release
        )

        def refresh_update_buttons():

            if self.latest_release_info:

                update_label.configure(
                    text=(
                        "Güncellemeler: yeni sürüm mevcut "
                        f"{self.latest_release_info.get('version', '')}"
                    ),
                    text_color="#27AE60"
                )

                if not download_update_button.winfo_ismapped():

                    download_update_button.pack(
                        side="left",
                        fill="x",
                        expand=True,
                        padx=(8, 0)
                    )

            else:

                update_label.configure(
                    text=f"Güncellemeler: mevcut sürüm {APP_VERSION}",
                    text_color="gray"
                )

                if download_update_button.winfo_ismapped():

                    download_update_button.pack_forget()

        def check_updates_from_settings():

            update_label.configure(
                text="Güncellemeler kontrol ediliyor...",
                text_color="#1F6AA5"
            )

            self.check_for_updates(
                silent=False
            )

            settings_window.after(
                1200,
                refresh_update_buttons
            )

        check_update_button = ctk.CTkButton(
            update_actions,
            text="Güncellemeleri Kontrol Et",
            height=38,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=check_updates_from_settings
        )

        check_update_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        refresh_update_buttons()

        data_path_label = ctk.CTkLabel(

            container,

            text=f"Veriler: {get_app_data_dir()}",

            font=("Arial", 11),

            anchor="w",

            justify="left",

            wraplength=460
        )

        data_path_label.pack(
            fill="x",
            padx=22,
            pady=(0, 12)
        )

        ownership_frame = ctk.CTkFrame(
            container,
            corner_radius=14
        )

        ownership_frame.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        ctk.CTkLabel(
            ownership_frame,
            text="Yapımcı ve Haklar",
            font=(
                "Arial",
                14,
                "bold"
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=16,
            pady=(14, 4)
        )

        ctk.CTkLabel(
            ownership_frame,
            text=(
                f"Sürüm: {APP_VERSION}\n"
                "Yapımcı: Ümit Ege Güldez\n"
                "© 2026 Ümit Ege Güldez. Tüm hakları saklıdır."
            ),
            text_color="#D8D8D8",
            font=(
                "Arial",
                13
            ),
            anchor="w",
            justify="left"
        ).pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        source_notice_frame = ctk.CTkFrame(
            container,
            corner_radius=14
        )

        source_notice_frame.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        ctk.CTkLabel(
            source_notice_frame,
            text="Kaynak Bildirimi",
            font=(
                "Arial",
                14,
                "bold"
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=16,
            pady=(14, 4)
        )

        ctk.CTkLabel(
            source_notice_frame,
            text=(
                "İzbul bağımsız bir uygulamadır. Kariyer.net, Jooble, "
                "Eleman.net veya LinkedIn ile resmi bir ortaklığı yoktur. "
                "Üçüncü taraf marka ve ilan hakları ilgili sahiplerine aittir."
            ),
            text_color="#D8D8D8",
            font=(
                "Arial",
                12
            ),
            anchor="w",
            justify="left",
            wraplength=420
        ).pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        def save_settings_from_window():

            try:

                jobs_per_page = int(
                    page_entry.get().strip()
                )

                if jobs_per_page < 1:

                    raise ValueError

                if jobs_per_page > 100:

                    jobs_per_page = 100

            except ValueError:

                set_settings_status(
                    "Sayfa başına ilan pozitif sayı olmalı.",
                    "#C0392B"
                )

                return

            api_key = api_entry.get().strip()

            save_jooble_api_key(api_key)

            theme_value = get_theme_value(
                theme_var.get()
            )

            default_city = city_entry.get().strip()

            self.settings.update(
                {
                    "default_city": default_city,
                    "jobs_per_page": jobs_per_page,
                    "appearance_mode": theme_value
                }
            )

            save_settings(
                self.settings
            )

            self.jobs_per_page = jobs_per_page

            ctk.set_appearance_mode(
                theme_value
            )

            if self.view_mode in [
                "results",
                "favorites"
            ]:
                self.display_jobs()

            self.city_entry.delete(
                0,
                "end"
            )

            if default_city:

                self.city_entry.insert(
                    0,
                    default_city
                )

            set_settings_status(
                "Ayarlar kaydedildi.",
                "#27AE60"
            )

            self.set_status_message(
                "Ayarlar kaydedildi."
            )

            settings_window.after(
                900,
                settings_window.destroy
            )

        save_button = ctk.CTkButton(

            container,

            text="Kaydet",

            height=42,
            fg_color="#2E8B57",
            hover_color="#247348",
            font=("Arial", 14, "bold"),

            command=save_settings_from_window
        )

        save_button.pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

    # =========================
    # TOAST MESSAGE
    # =========================

    def position_toast(self):

        if not self.toast_label:

            return

        try:

            self.update_idletasks()

            app_x = self.winfo_rootx()
            app_y = self.winfo_rooty()
            content_x = self.right_content.winfo_rootx() - app_x
            content_y = self.right_content.winfo_rooty() - app_y
            content_width = self.right_content.winfo_width()

            self.toast_label.place(
                x=content_x + content_width - 22,
                y=content_y - 3,
                anchor="ne"
            )

            self.toast_label.lift()

        except Exception:

            self.toast_label.place(
                relx=0.965,
                y=0,
                anchor="ne"
            )

    def show_toast(self, message, color="#1F6AA5"):

        if self.toast_label:

            self.toast_label.destroy()

        self.toast_label = ctk.CTkLabel(

            self,

            text=message,

            fg_color=color,

            text_color="white",

            corner_radius=14,

            width=270,

            height=34,

            font=("Arial",13,"bold"),

            padx=18,

            pady=7
        )

        self.position_toast()

        self.after(
            2200,
            self.hide_toast
        )

    def hide_toast(self):
        
        if self.toast_label:

            self.toast_label.destroy()

            self.toast_label = None


    def force_focus(self):

        self.lift()
        self.focus_force()

        self.attributes(
            "-topmost",
            True
        )

        self.after(
            500,
            lambda:
            self.attributes(
                "-topmost",
                False
            )
        )

    def focus_search_entry(self, event=None):

        self.keyword_entry.focus_set()
        self.keyword_entry.select_range(
            0,
            "end"
        )

        return "break"

    def handle_escape(self, event=None):

        if self.search_in_progress:

            self.cancel_search()

            return "break"

        focused_widget = self.focus_get()

        if focused_widget == self.keyword_entry:

            self.keyword_entry.delete(
                0,
                "end"
            )

            return "break"

        if focused_widget == self.city_entry:

            self.city_entry.delete(
                0,
                "end"
            )

            self.auto_apply_filters()

            return "break"

        return None

    def update_search_history(self, keyword, city, selected_sources=None):

        keyword = str(
            keyword or ""
        ).strip()

        city = str(
            city or ""
        ).strip()

        if not keyword:

            return

        current_history = self.settings.get(
            "search_history",
            []
        )

        if not isinstance(current_history, list):

            current_history = []

        normalized_key = (
            normalize_text(keyword),
            normalize_text(city)
        )

        selected_sources = (
            selected_sources
            if isinstance(selected_sources, list)
            else self.get_selected_sources()
        )

        selected_experiences = [
            exp
            for exp, var in self.exp_vars.items()
            if var.get()
        ]

        selected_remote = [
            remote
            for remote, var in self.remote_vars.items()
            if var.get()
        ]

        next_history = [
            item
            for item in current_history
            if isinstance(item, dict) and (
                normalize_text(
                    item.get(
                        "keyword",
                        ""
                    )
                ),
                normalize_text(
                    item.get(
                        "city",
                        ""
                    )
                )
            ) != normalized_key
        ]

        next_history.insert(
            0,
            {
                "keyword": keyword,
                "city": city,
                "sources": selected_sources,
                "experiences": selected_experiences,
                "remote": selected_remote,
                "sort_type": self.sort_var.get()
            }
        )

        self.settings["search_history"] = next_history[:8]

    def start_search(self):

        if self.search_in_progress:

            self.cancel_search()

            return

        keyword = (
            self.keyword_entry.get()
            .strip()
        )

        if not keyword:
            return

        selected_city = (
            self.city_entry.get()
            .strip()
        )

        selected_sources = self.get_selected_sources()

        if not selected_sources:

            self.show_toast(
                "En az bir kaynak seçin.",
                "#C0392B"
            )

            return

        self.update_search_history(
            keyword,
            selected_city,
            selected_sources
        )

        self.save_search_preferences()

        self.push_navigation_state()

        self.search_in_progress = True
        self.search_token += 1
        self.current_search_sources = selected_sources[:]

        active_token = self.search_token

        self.search_button.configure(
            state="normal",
            text="Durdur",
            fg_color="#8B2E2E",
            hover_color="#AA3333"
        )

        self.view_mode = "results"

        self.set_status_message(
            "Arama başlatıldı..."
        )

        self.reset_source_progress(
            selected_sources
        )

        threading.Thread(

            target=self.search_jobs,

            args=(
                keyword,
                selected_city,
                selected_sources,
                active_token
            ),

            daemon=True
        ).start()

    def cancel_search(self):

        self.search_in_progress = False
        self.search_token += 1

        self.search_button.configure(
            state="normal",
            text="Ara",
            fg_color="#1F6AA5",
            hover_color="#155A8E"
        )

        self.set_status_message(
            "Arama durduruldu."
        )

        for source in self.source_progress:

            self.source_progress[source]["status"] = "Durduruldu"

        self.render_source_progress()

    def get_selected_sources(self):

        return [

            source

            for source, var in self.source_vars.items()

            if var.get()
        ]

    def get_selected_application_statuses(self):

        if not hasattr(
            self,
            "application_status_filter_var"
        ):

            return []

        selected_status = self.application_status_filter_var.get()

        if selected_status == "Tümü":

            return []

        return [selected_status]

    def save_search_preferences(self):

        self.settings.update(
            {
                "last_keyword": self.keyword_entry.get().strip(),
                "last_city": self.city_entry.get().strip(),
                "selected_sources": self.get_selected_sources(),
                "selected_application_statuses": (
                    self.get_selected_application_statuses()
                ),
                "selected_experiences": [
                    exp
                    for exp, var in self.exp_vars.items()
                    if var.get()
                ],
                "selected_remote": [
                    remote
                    for remote, var in self.remote_vars.items()
                    if var.get()
                ],
                "sort_type": self.sort_var.get()
            }
        )

        save_settings(
            self.settings
        )

    def set_status_message(self, message):

        self.last_status_message = message

        if hasattr(self, "status_label"):

            self.status_label.configure(
                text=message
            )

    def reset_source_progress(self, selected_sources):

        self.source_progress = {
            source: {
                "status": "Bekliyor",
                "count": 0,
                "message": ""
            }
            for source in selected_sources
        }

        self.render_source_progress()

    def get_source_progress_color(self, status):

        colors = {
            "Bekliyor": "#3A3A3A",
            "Aranıyor": "#1F6AA5",
            "Tamamlandı": "#2E8B57",
            "Atlandı": "#7A5A22",
            "Hata": "#8B2E2E",
            "Durduruldu": "#555555"
        }

        return colors.get(
            status,
            "#3A3A3A"
        )

    def render_source_progress(self):

        if not hasattr(self, "source_progress_frame"):

            return

        for widget in self.source_progress_frame.winfo_children():

            widget.destroy()

        self.source_progress_labels = {}

        source_labels = {
            "kariyer": "Kariyer.net",
            "jooble": "Jooble",
            "eleman": "Eleman.net"
        }

        for source in [
            "kariyer",
            "eleman",
            "jooble"
        ]:

            if source not in self.source_progress:

                continue

            data = self.source_progress[source]
            status = data.get(
                "status",
                "Bekliyor"
            )
            count = data.get(
                "count",
                0
            )

            text = f"{source_labels.get(source, source)}: {status}"

            if count is not None and status in [
                "Aranıyor",
                "Tamamlandı"
            ]:

                text = f"{text} · {count}"

            label = ctk.CTkLabel(
                self.source_progress_frame,
                text=text,
                fg_color=self.get_source_progress_color(status),
                corner_radius=10,
                font=(
                    "Arial",
                    12,
                    "bold"
                ),
                padx=10,
                pady=4
            )

            label.pack(
                side="left",
                padx=(0, 8)
            )

            self.source_progress_labels[source] = label

    def update_source_progress(self, progress):

        if not isinstance(progress, dict):

            return

        source = progress.get("source")

        if not source:

            return

        self.source_progress[source] = {
            "status": progress.get(
                "status",
                "Bekliyor"
            ),
            "count": progress.get(
                "count",
                0
            ),
            "message": progress.get(
                "message",
                ""
            )
        }

        self.render_source_progress()

    def finalize_source_progress(self, selected_sources, search_report):

        source_counts = (
            search_report or {}
        ).get(
            "source_counts",
            {}
        )

        source_errors = (
            search_report or {}
        ).get(
            "source_errors",
            {}
        )

        for source in selected_sources:

            status = (
                "Hata"
                if source in source_errors
                else "Tamamlandı"
            )

            if source in source_errors and "atlandı" in source_errors[source].lower():

                status = "Atlandı"

            self.source_progress[source] = {
                "status": status,
                "count": source_counts.get(
                    source,
                    0
                ),
                "message": source_errors.get(
                    source,
                    ""
                )
            }

        self.render_source_progress()

    def thread_safe_status(self, message, search_token=None):

        self.after(
            0,
            lambda:
            (
                self.set_status_message(message)
                if search_token is None or search_token == self.search_token
                else None
            )
        )

    def thread_safe_source_progress(self, progress, search_token):

        self.after(
            0,
            lambda:
            (
                self.update_source_progress(progress)
                if search_token == self.search_token
                else None
            )
        )

    def search_jobs(self, keyword, selected_city, selected_sources, search_token):

        search_report = {}

        jobs = smart_search(
            keyword,
            selected_city=selected_city,
            sources=selected_sources,
            status_callback=lambda message:
            self.thread_safe_status(
                message,
                search_token
            ),
            progress_callback=lambda progress:
            self.thread_safe_source_progress(
                progress,
                search_token
            ),
            report_callback=search_report.update
        )

        if search_token != self.search_token:

            return

        self.last_search_report = search_report
        self.all_jobs = jobs
        self.filtered_jobs = jobs
        self.current_page = 1
        self.search_summary_message = self.build_search_summary(
            jobs,
            selected_sources,
            search_report
        )

        self.after(
            0,
            lambda:
            self.after_search_complete(search_token)
        )

    def build_search_summary(self, jobs, selected_sources, search_report=None):

        source_labels = {
            "kariyer": "Kariyer.net",
            "jooble": "Jooble",
            "eleman": "Eleman.net"
        }

        search_report = search_report or {}

        counts = {
            source: 0
            for source in source_labels
        }

        for job in jobs:

            source = SOURCE_KEY_BY_SITE.get(
                getattr(
                    job,
                    "site",
                    ""
                )
            )

            if source:

                counts[source] += 1

        errors = search_report.get(
            "source_errors",
            {}
        )

        parts = [
            f"{source_labels.get(source, source)}: {counts.get(source, 0)}"
            for source in selected_sources
        ]

        summary = (
            f"{len(jobs)} ilan bulundu"
            + (
                f" ({', '.join(parts)})"
                if parts
                else ""
            )
            + "."
        )

        if errors:

            summary += (
                " "
                + " ".join(
                    errors[source]
                    for source in selected_sources
                    if source in errors
                )
            )

        return summary

    def after_search_complete(self, search_token=None):

        if search_token is not None and search_token != self.search_token:

            return

        self.search_in_progress = False

        self.finalize_source_progress(
            self.current_search_sources,
            self.last_search_report
        )

        self.update_ui()
        self.apply_filters()

    def auto_apply_filters(self):

        if self.view_mode not in [
            "results",
            "favorites"
        ]:

            return

        self.save_search_preferences()

        self.apply_filters()

    def filter_favorites_by_status(self, status):

        if status not in APPLICATION_STATUSES:

            return

        self.view_mode = "favorites"

        if hasattr(
            self,
            "application_status_filter_var"
        ):

            self.application_status_filter_var.set(status)

        self.save_search_preferences()

        self.apply_filters()

        self.set_status_message(
            f"Favoriler filtrelendi: {status}"
        )

    def clear_favorite_filters(self):

        self.reset_favorite_filters(
            save_preferences=True
        )

        self.apply_filters()

        self.set_status_message(
            "Tüm favoriler gösteriliyor."
        )

    def reset_favorite_filters(self, save_preferences=False):

        self.keyword_entry.delete(
            0,
            "end"
        )

        self.city_entry.delete(
            0,
            "end"
        )

        for var in self.exp_vars.values():

            var.set(False)

        for var in self.remote_vars.values():

            var.set(False)

        if hasattr(
            self,
            "application_status_filter_var"
        ):

            self.application_status_filter_var.set(
                "Tümü"
            )

        self.sort_var.set(
            "Varsayılan"
        )

        if save_preferences:

            self.save_search_preferences()

    def clear_filters(self):

        self.city_entry.delete(
            0,
            "end"
        )

        for var in self.exp_vars.values():

            var.set(False)

        for var in self.remote_vars.values():

            var.set(False)

        for var in self.source_vars.values():

            var.set(True)

        if hasattr(
            self,
            "application_status_filter_var"
        ):

            self.application_status_filter_var.set(
                "Tümü"
            )

        self.sort_var.set(
            "Varsayılan"
        )

        self.save_search_preferences()

        self.apply_filters()

        self.set_status_message(
            "Filtreler temizlendi."
        )

    def apply_filters(self):

        if self.view_mode == "favorites":

            filtered = self.get_favorite_job_objects()

            filtered.sort(
                key=lambda job:
                getattr(
                    job,
                    "saved_at",
                    ""
                ),
                reverse=True
            )

            keyword = normalize_text(
                self.keyword_entry.get()
            )

            if keyword:

                filtered = [

                    job for job in filtered

                    if (
                        keyword in normalize_text(
                            getattr(
                                job,
                                "title",
                                ""
                            )
                        ) or
                        keyword in normalize_text(
                            getattr(
                                job,
                                "company",
                                ""
                            )
                        ) or
                        keyword in normalize_text(
                            getattr(
                                job,
                                "description",
                                ""
                            )
                        ) or
                        keyword in normalize_text(
                            getattr(
                                job,
                                "application_note",
                                ""
                            )
                        )
                    )
                ]

            selected_application_statuses = set(
                self.get_selected_application_statuses()
            )

            if selected_application_statuses:

                filtered = [
                    job for job in filtered
                    if getattr(
                        job,
                        "application_status",
                        "Kaydedildi"
                    ) in selected_application_statuses
                ]

        else:

            filtered = [
                job
                for job in self.all_jobs
                if not self.is_hidden_job(job)
            ]

            selected_application_statuses = set(
                self.get_selected_application_statuses()
            )

            if selected_application_statuses:

                status_filtered = []

                for job in filtered:

                    favorite_data = self.get_favorite_data(job)

                    if (
                        favorite_data and
                        favorite_data.get(
                            "application_status",
                            "Kaydedildi"
                        ) in selected_application_statuses
                    ):

                        status_filtered.append(job)

                filtered = status_filtered

        city = normalize_text(
            self.city_entry.get()
        )

        if city:

            filtered = [

                job for job in filtered

                if city in normalize_text(
                    getattr(
                        job,
                        "location",
                        ""
                    )
                )
            ]

        selected_experiences = {

            exp

            for exp, var in self.exp_vars.items()

            if var.get()
        }

        if selected_experiences:

            filtered = [

                job for job in filtered

                if getattr(
                    job,
                    "experience",
                    ""
                ) in selected_experiences
            ]

        selected_remote = {

            remote

            for remote, var in self.remote_vars.items()

            if var.get()
        }

        if selected_remote:

            filtered = [

                job for job in filtered

                if getattr(
                    job,
                    "remote",
                    ""
                ) in selected_remote
            ]
        #==========================
        # SORTING
        #==========================

        sort_type = self.sort_var.get()

        if sort_type == "A-Z Pozisyona Göre":

            filtered.sort(
                key=lambda j:
                j.title.lower()
            )
        
        elif sort_type == "A-Z Şirkete Göre":

            filtered.sort(
                key=lambda j:
                j.company.lower()
            )
        
        elif sort_type == "Junior Önce":
            filtered.sort(

                key=lambda j:
                EXPERIENCE_ASC_PRIORITY.get(
                    j.experience,
                    999
                )
            )

        elif sort_type == "Senior Önce":
            filtered.sort(

                key=lambda j:
                EXPERIENCE_DESC_PRIORITY.get(
                    j.experience,
                    999
                )
            )

        elif sort_type == "Remote Önce":

            filtered.sort(

                key=lambda j:
                REMOTE_PRIORITY.get(
                    j.remote,
                    999
                )
            )

        elif sort_type == "En Yeni Önce":

            filtered.sort(

                key=lambda j:
                j.posted_date,

                reverse=True
            )

        self.filtered_jobs = filtered

        self.current_page = 1

        if self.view_mode == "favorites":

            self.set_status_message(
                f"{len(filtered)} favori ilan gösteriliyor."
            )

        elif self.view_mode == "results":

            self.search_summary_message = self.build_search_summary(
                filtered,
                self.get_selected_sources(),
                self.last_search_report
            )

            self.set_status_message(
                self.search_summary_message
            )

        self.display_jobs(
            scroll_to_top=True
        )

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
                    corner_radius=10,
                    height=30,
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
                corner_radius=10,
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
                corner_radius=10,
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


if __name__ == "__main__":

    app = JobApp()

    app.mainloop()
