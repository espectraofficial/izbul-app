import customtkinter as ctk
import threading
import math
import webbrowser
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from scrapers.jooble import (
    get_jooble_api_key,
    save_jooble_api_key
)
from utils.search_engine import smart_search, normalize_text


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


APP_NAME = "Job Finder"

DEFAULT_SETTINGS = {
    "default_city": "",
    "jobs_per_page": 10,
    "appearance_mode": "dark"
}


def get_app_data_dir():

    if sys.platform == "darwin":

        return (
            Path.home()
            / "Library"
            / "Application Support"
            / APP_NAME
        )

    if sys.platform.startswith("win"):

        appdata = os.getenv("APPDATA")

        if appdata:

            return Path(appdata) / APP_NAME

    return (
        Path.home()
        / ".config"
        / APP_NAME
    )


def get_favorites_file():

    app_data_dir = get_app_data_dir()

    app_data_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data_dir / "favorites.json"


def get_settings_file():

    app_data_dir = get_app_data_dir()

    app_data_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data_dir / "settings.json"


def load_settings():

    settings_file = get_settings_file()

    if not settings_file.exists():

        return DEFAULT_SETTINGS.copy()

    try:

        with open(
            settings_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        settings = DEFAULT_SETTINGS.copy()

        if isinstance(data, dict):

            settings.update(data)

        return settings

    except Exception as e:

        print("Ayarlar yüklenemedi:", e)

        return DEFAULT_SETTINGS.copy()


def save_settings(settings):

    settings_file = get_settings_file()

    with open(
        settings_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            settings,
            file,
            ensure_ascii=False,
            indent=4
        )


def migrate_legacy_favorites(favorites_file):

    if favorites_file.exists():

        return

    legacy_paths = [
        Path.cwd() / "favorites.json",
        Path(__file__).resolve().parent.parent / "favorites.json"
    ]

    for legacy_path in legacy_paths:

        if not legacy_path.exists():

            continue

        try:

            with open(
                legacy_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(data, list):

                continue

            with open(
                favorites_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            return

        except Exception as e:

            print("Eski favoriler taşınamadı:", e)


class JobApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        # =========================
        # WINDOW
        # =========================

        self.title("Job Finder")

        window_width = 1500
        window_height = 900

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

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

        # =========================
        # DATA
        # =========================

        self.all_jobs = []
        self.filtered_jobs = []
        self.favorite_jobs = []
        self.toast_label = None
        self.settings = load_settings()

        ctk.set_appearance_mode(
            self.settings.get(
                "appearance_mode",
                "dark"
            )
        )

        self.favorites_file = get_favorites_file()
        self.last_status_message = "Hazır"
        self.view_mode = "home"

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

            command=self.go_back
        )

        self.back_button.pack(
            side="left",
            padx=(20, 8),
            pady=15
        )
        
        # SEARCH ENTRY

        self.keyword_entry = ctk.CTkEntry(

            self.top_frame,

            width=420,

            height=44,

            corner_radius=12,

            placeholder_text="Pozisyon veya keyword ara"
        )

        self.keyword_entry.pack(
            side="left",
            padx=(25, 10),
            pady=15
        )

        self.keyword_entry.bind(
            "<Return>",
            lambda event:
            self.start_search()
        )

        # SEARCH BUTTON

        self.search_button = ctk.CTkButton(

            self.top_frame,

            text="İş Ara",

            width=130,

            height=44,

            corner_radius=12,

            command=self.start_search
        )

        self.search_button.pack(
            side="left",
            padx=10
        )

        # LINKEDIN SEARCH BUTTON

        self.linkedin_button = ctk.CTkButton(

            self.top_frame,

            text="LinkedIn'de Aç",

            width=140,

            height=44,

            corner_radius=12,

            command=self.open_linkedin_search
        )

        self.linkedin_button.pack(
            side="left",
            padx=10
        )

        # FAVORITES BUTTON

        self.favorites_button = ctk.CTkButton(

            self.top_frame,

            text="Favoriler",

            width=120,

            height=44,

            corner_radius=12,

            command=self.show_favorites
        )

        self.favorites_button.pack(
            side="left",
            padx=10
        )

        # HOME BUTTON

        self.home_button = ctk.CTkButton(

            self.top_frame,

            text="Ana Sayfa",

            width=120,

            height=44,

            corner_radius=12,

            command=self.show_welcome_screen
        )

        self.home_button.pack(
            side="left",
            padx=10
        )

        # SETTINGS BUTTON

        self.settings_button = ctk.CTkButton(

            self.top_frame,

            text="Ayarlar",

            width=110,

            height=44,

            corner_radius=12,

            command=self.show_settings
        )

        self.settings_button.pack(
            side="left",
            padx=10
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

        self.sidebar = ctk.CTkScrollableFrame(
            self.content_container,
            width=300,
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
                28,
                "bold"
            )
        )

        filter_title.pack(
            anchor="w",
            padx=20,
            pady=(20, 20)
        )

        # =========================
        # CITY FILTER
        # =========================

        city_label = ctk.CTkLabel(

            self.sidebar,

            text="İl / İlçe",

            font=(
                "Arial",
                15,
                "bold"
            )
        )

        city_label.pack(
            anchor="w",
            padx=20,
            pady=(10, 5)
        )

        self.city_entry = ctk.CTkEntry(

            self.sidebar,

            width=240,

            height=40,

            corner_radius=10,

            placeholder_text="Şehir veya ilçe ara..."
        )

        self.city_entry.pack(
            padx=20,
            pady=(0, 20)
        )

        default_city = self.settings.get(
            "default_city",
            ""
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
                15,
                "bold"
            )
        )

        source_label.pack(
            anchor="w",
            padx=20,
            pady=(10, 10)
        )

        self.source_vars = {}

        source_values = [
            ("kariyer", "Kariyer.net"),
            ("jooble", "Jooble")
        ]

        for source_key, source_name in source_values:

            var = ctk.BooleanVar(
                value=True
            )

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=source_name,

                variable=var
            )

            checkbox.pack(
                anchor="w",
                padx=25,
                pady=4
            )

            self.source_vars[source_key] = var

        # =========================
        # EXPERIENCE FILTER
        # =========================

        experience_label = ctk.CTkLabel(

            self.sidebar,

            text="Deneyim Seviyesi",

            font=(
                "Arial",
                15,
                "bold"
            )
        )

        experience_label.pack(
            anchor="w",
            padx=20,
            pady=(10, 10)
        )

        self.exp_vars = {}

        experience_values = [

            "Stajyer",
            "Junior",
            "Mid-Level",
            "Senior",
            "Manager",
            "Director"
        ]

        for exp in experience_values:

            var = ctk.BooleanVar()

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=exp,

                variable=var
            )

            checkbox.pack(
                anchor="w",
                padx=25,
                pady=4
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
                15,
                "bold"
            )
        )

        remote_label.pack(
            anchor="w",
            padx=20,
            pady=(25, 10)
        )

        self.remote_vars = {}

        remote_values = [

            "Ofis",
            "Hibrit",
            "Remote"
        ]

        for remote in remote_values:

            var = ctk.BooleanVar()

            checkbox = ctk.CTkCheckBox(

                self.sidebar,

                text=remote,

                variable=var
            )

            checkbox.pack(
                anchor="w",
                padx=25,
                pady=4
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
                15,
                "bold"
            )
        )

        sort_label.pack(
            anchor="w",
            padx=20,
            pady=(30, 10)
        )

        self.sort_var = ctk.StringVar(
            value ="Varsayılan"
        )

        self.sort_menu = ctk.CTkOptionMenu(

            self.sidebar,

            values=[
                "Varsayılan",

                "A-Z Pozisyona Göre",

                "A-Z Şirkete Göre",

                "Junior Önce",

                "Senior Önce",

                "Remote Önce",

                "En Yeni Önce"
            ],

            variable=self.sort_var,

            width=240,

            height=40,
        )

        self.sort_menu.pack(
            padx=20,
            pady=(0, 10)
        )

        # =========================
        # APPLY FILTER BUTTON
        # =========================

        self.apply_filter_button = ctk.CTkButton(

            self.sidebar,

            text="Filtreleri Uygula",

            height=44,

            corner_radius=12,

            command=self.apply_filters
        )

        self.apply_filter_button.pack(
            padx=20,
            pady=(30, 20),
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

            command=self.next_page
        )

        self.next_button.pack(
            side="left",
            padx=10,
            pady=10
        )

        self.load_favorites()

        self.show_welcome_screen()

    # =========================
    # BACK
    # =========================

    def go_back(self):

        if hasattr(self, "previous_jobs"):

            self.filtered_jobs = self.previous_jobs

            self.current_page = self.previous_page

            self.display_jobs()

    # =========================
    # WELCOME SCREEN
    # =========================

    def show_welcome_screen(self):

        self.view_mode = "home"

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

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        container = ctk.CTkFrame(
            self.results_frame,
            corner_radius=20
        )

        container.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        title = ctk.CTkLabel(

            container,

            text="🔍 Job Finder",

            font=(
                "Arial",
                42,
                "bold"
            )
        )

        title.pack(
            pady=(60, 15)
        )

        subtitle = ctk.CTkLabel(

            container,

            text=(
                "Kariyer.net iş ilanlarını\n"
                "tek ekranda bulun.\n"
                "\n"
                "Sık yapılan aramalar:"

            ),

            justify="center",

            font=(
                "Arial",
                20
            )
        )

        subtitle.pack(
            pady=(0, 40)
        )

        quick_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        quick_frame.pack(
            pady=(0, 45)
        )

        quick_jobs = [

            "İnsan Kaynakları",
            "Yazılım",
            "Pazarlama",
            "Mimar"
        ]

        for job in quick_jobs:

            btn = ctk.CTkButton(

                quick_frame,

                text=job,

                width=180,

                height=46,

                corner_radius=12,

                command=lambda j=job:
                self.quick_search(j)
            )

            btn.pack(
                side="left",
                padx=10
            )

        features_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        features_frame.pack(
            pady=10
        )

        features = [

            (
                "⚡ Hızlı Arama",
                "Kariyer.net ilanlarını tek ekranda listeler."
            ),

            (
                "🎯 Gelişmiş Filtreler",
                "Şehir, deneyim ve çalışma modeli filtreleme desteği."
            ),

            (
                "⭐ Favoriler",
                "İlgilendiğiniz ilanları favorilere ekleyin."
            ),

            (
                "🖥 Modern Dashboard",
                "Profesyonel sidebar tabanlı modern arayüz."
            )
        ]

        for title_text, desc in features:

            card = ctk.CTkFrame(
                features_frame,
                width=260,
                height=160,
                corner_radius=18
            )

            card.pack(
                side="left",
                padx=10
            )

            card.pack_propagate(False)

            title_label = ctk.CTkLabel(

                card,

                text=title_text,

                font=(
                    "Arial",
                    18,
                    "bold"
                )
            )

            title_label.pack(
                pady=(28, 12)
            )

            desc_label = ctk.CTkLabel(

                card,

                text=desc,

                wraplength=220,

                justify="center",

                font=(
                    "Arial",
                    14
                )
            )

            desc_label.pack(
                padx=15
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

        settings_window.geometry("520x460")

        settings_window.resizable(False, False)

        settings_window.transient(self)

        settings_window.focus()

        container = ctk.CTkFrame(
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
            pady=(0, 16)
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
            value=self.settings.get(
                "appearance_mode",
                "dark"
            )
        )

        theme_menu = ctk.CTkOptionMenu(
            container,
            values=[
                "dark",
                "light",
                "system"
            ],
            variable=theme_var,
            width=460,
            height=40
        )

        theme_menu.pack(
            padx=22,
            pady=(0, 22)
        )

        def save_settings_from_window():

            try:

                jobs_per_page = int(
                    page_entry.get().strip()
                )

                if jobs_per_page < 1:

                    raise ValueError

            except ValueError:

                self.show_toast(
                    "Sayfa başına ilan pozitif sayı olmalı.",
                    "#C0392B"
                )

                return

            api_key = api_entry.get().strip()

            save_jooble_api_key(api_key)

            self.settings = {
                "default_city": city_entry.get().strip(),
                "jobs_per_page": jobs_per_page,
                "appearance_mode": theme_var.get()
            }

            save_settings(
                self.settings
            )

            self.jobs_per_page = jobs_per_page

            ctk.set_appearance_mode(
                theme_var.get()
            )

            self.show_toast(
                "Ayarlar kaydedildi.",
                "#27AE60"
            )

            settings_window.destroy()

        save_button = ctk.CTkButton(

            container,

            text="Kaydet",

            height=42,

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

    def show_toast(self, message, color="#1F6AA5"):
        
        if self.toast_label:

            self.toast_label.destroy()

        self.toast_label = ctk.CTkLabel(

            self,

            text=message,

            fg_color=color,

            text_color="white",

            corner_radius=14,

            height=42,

            font=("Arial",14,"bold"),

            padx=22,

            pady=10
        )

        self.toast_label.place(

            relx=0.9,
            rely=0.043,
            
            anchor="center"
        )

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

    def start_search(self):

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

        self.search_button.configure(
            state="disabled",
            text="Aranıyor..."
        )

        self.view_mode = "results"

        self.set_status_message(
            "Arama başlatıldı..."
        )

        threading.Thread(

            target=self.search_jobs,

            args=(keyword, selected_city, selected_sources),

            daemon=True
        ).start()

    def get_selected_sources(self):

        return [

            source

            for source, var in self.source_vars.items()

            if var.get()
        ]

    def set_status_message(self, message):

        self.last_status_message = message

        if hasattr(self, "status_label"):

            self.status_label.configure(
                text=message
            )

    def thread_safe_status(self, message):

        self.after(
            0,
            lambda:
            self.set_status_message(message)
        )

    def search_jobs(self, keyword, selected_city, selected_sources):

        jobs = smart_search(
            keyword,
            selected_city=selected_city,
            sources=selected_sources,
            status_callback=self.thread_safe_status
        )

        self.all_jobs = jobs
        self.filtered_jobs = jobs
        self.current_page = 1

        self.after(
            0,
            self.after_search_complete
        )

    def after_search_complete(self):

        self.apply_filters()
        self.update_ui()

    # =========================
    # SAVE FAVORITES
    # =========================

    def save_favorites(self):

        try:

            Path(self.favorites_file).parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                self.favorites_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.favorite_jobs,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as e:

            print("Favoriler kaydedilemedi:", e)

    # =========================
    # LOAD FAVORITES
    # =========================

    def load_favorites(self):

        if not os.path.exists(self.favorites_file):

            self.favorite_jobs = []

            return

        try:

            with open(
                self.favorites_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(data, list):

                self.favorite_jobs = data
            
            else:
                self.favorite_jobs = []

        except Exception as e:

            print("Favoriler yüklenemedi:", e)

            self.favorite_jobs = []

    # =========================
    # FAVORITES
    # =========================

    def toggle_favorite(self, job):

        job_url = getattr(job, "url", "")

        job_data = {
            
            "site": str(getattr(job, "site", "")),
            "company": str(getattr(job, "company", "")),
            "title": str(getattr(job, "title", "")),
            "description": str(getattr(job, "description", "")),
            "url": str(job_url),
            "apply_url": str(getattr(job, "apply_url", "")),
            "remote": str(getattr(job, "remote", "")),
            "experience": str(getattr(job, "experience", "")),
            "location": str(getattr(job, "location", "")),
            "posted_date": str(getattr(job, "posted_date", "")),
            "job_date_text": str(getattr(job, "job_date_text", ""))
        }

        existing = None

        for fav in self.favorite_jobs:

            if fav.get("url") == job_url:

                existing = fav
                break

        if existing:

            self.favorite_jobs.remove(existing)

            self.show_toast(
                "İlan favorilerden kaldırıldı.",
                "#C0392B"
            )

        else:

            self.favorite_jobs.append(job_data)

            self.show_toast(
                "İlan favorilere eklendi.",
                "#27AE60"
            )

        self.save_favorites()

        if self.filtered_jobs == []:

            self.show_favorites()

        else:

            self.display_jobs()
    
    def show_favorites(self):

        self.previous_jobs = self.filtered_jobs

        self.previous_page = self.current_page

        self.view_mode = "favorites"

        self.apply_filters()

    def get_favorite_job_objects(self):

        class FavoriteJob:

            def __init__(self, data):
                
                self.title = data.get("title", "")
                self.company = data.get("company", "")
                self.site = data.get("site", "")
                self.description = data.get("description", "")
                self.location = data.get("location", "")
                self.experience = data.get("experience", "")
                self.remote = data.get("remote", "")
                self.url = data.get("url", "")
                self.apply_url = data.get("apply_url", "")
                self.posted_date = data.get("posted_date", "")
                self.job_date_text = data.get("job_date_text", "")

        return [

            FavoriteJob(job)

            for job in self.favorite_jobs
        ]

    def safe_button_text(self, button, text):

        try:
            if button.winfo_exists():
                button.configure(text=text)
        except:
            pass

    def show_job_details(self, job):

        detail_window = ctk.CTkToplevel(self)

        detail_window.title("İlan Detayı")

        detail_window.geometry("720x620")

        detail_window.minsize(620, 520)

        detail_window.transient(self)

        detail_window.focus()

        container = ctk.CTkFrame(
            detail_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        title_label = ctk.CTkLabel(

            container,

            text=getattr(job, "title", ""),

            font=(
                "Arial",
                26,
                "bold"
            ),

            anchor="w",

            justify="left",

            wraplength=640
        )

        title_label.pack(
            fill="x",
            padx=22,
            pady=(22, 8)
        )

        company_label = ctk.CTkLabel(

            container,

            text=getattr(job, "company", ""),

            font=(
                "Arial",
                17
            ),

            anchor="w",

            justify="left"
        )

        company_label.pack(
            fill="x",
            padx=22,
            pady=(0, 14)
        )

        meta_text = (
            f"Kaynak: {getattr(job, 'site', '')}\n"
            f"Konum: {getattr(job, 'location', '')}\n"
            f"Tarih: {getattr(job, 'job_date_text', '')}\n"
            f"Deneyim: {getattr(job, 'experience', '')}\n"
            f"Çalışma: {getattr(job, 'remote', '')}"
        )

        meta_label = ctk.CTkLabel(

            container,

            text=meta_text,

            font=(
                "Arial",
                14
            ),

            anchor="w",

            justify="left"
        )

        meta_label.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        description_box = ctk.CTkTextbox(
            container,
            height=260,
            wrap="word"
        )

        description_box.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(0, 16)
        )

        description = getattr(
            job,
            "description",
            ""
        ).strip()

        if not description:

            description = "Bu kaynak detay açıklaması sağlamıyor."

        description_box.insert(
            "1.0",
            description
        )

        description_box.configure(
            state="disabled"
        )

        button_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        button_frame.pack(
            fill="x",
            padx=22,
            pady=(0, 20)
        )

        favorite_button = ctk.CTkButton(

            button_frame,

            text="Favori Durumunu Değiştir",

            width=190,

            height=40,

            command=lambda:
            self.toggle_favorite(job)
        )

        favorite_button.pack(
            side="left",
            padx=(0, 10)
        )

        open_button = ctk.CTkButton(

            button_frame,

            text="İlana Git",

            width=130,

            height=40,

            command=lambda:
            webbrowser.open(
                getattr(
                    job,
                    "url",
                    ""
                )
            )
        )

        open_button.pack(
            side="right"
        )
    
    def apply_filters(self):

        if self.view_mode == "favorites":

            filtered = self.get_favorite_job_objects()

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
                        )
                    )
                ]

        else:

            filtered = self.all_jobs

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

        selected_experiences = [

            exp

            for exp, var in self.exp_vars.items()

            if var.get()
        ]

        if selected_experiences:

            filtered = [

                job for job in filtered

                if getattr(
                    job,
                    "experience",
                    ""
                ) in selected_experiences
            ]

        selected_remote = [

            remote

            for remote, var in self.remote_vars.items()

            if var.get()
        ]

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
            priority = {
                "Stajyer": 0,
                "Junior": 1,
                "Mid-Level": 2,
                "Senior": 3,
                "Manager": 4,
                "Director": 5
            }

            filtered.sort(

                key=lambda j:
                priority.get(
                    j.experience,
                    999
                )
            )

        elif sort_type == "Senior Önce":
            priority = {
                "Director": 0,
                "Manager": 1,
                "Senior": 2,
                "Mid-Level": 3,
                "Junior": 4,
                "Stajyer": 5
            }

            filtered.sort(

                key=lambda j:
                priority.get(
                    j.experience,
                    999
                )
            )

        elif sort_type == "Remote Önce":

            priority = {
                "Remote": 0,
                "Hibrit": 1,
                "Ofis": 2
            }

            filtered.sort(

                key=lambda j:
                priority.get(
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

        self.display_jobs()

    def update_ui(self):

        self.search_button.configure(
            state="normal",
            text="İş Ara"
        )

        self.prev_button.configure(
            state="normal"
        )

        self.next_button.configure(
            state="normal"
        )

        self.display_jobs()

    def display_jobs(self):

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        start = (
            self.current_page - 1
        ) * self.jobs_per_page

        end = (
            start + self.jobs_per_page
        )

        jobs = self.filtered_jobs[
            start:end
        ]

        if not jobs:

            empty_text = (
                "Favori iş ilanı bulunamadı."
                if self.view_mode == "favorites"
                else "İlan bulunamadı."
            )

            empty_label = ctk.CTkLabel(

                self.results_frame,

                text=empty_text,

                font=(
                    "Arial",
                    22,
                    "bold"
                )
            )

            empty_label.pack(
                pady=80
            )

            return

        for job in jobs:

            card = ctk.CTkFrame(
                self.results_frame,
                corner_radius=18
            )

            card.pack(
                fill="x",
                padx=10,
                pady=10
            )

            title = ctk.CTkLabel(

                card,

                text=job.title,

                font=(
                    "Arial",
                    22,
                    "bold"
                ),

                anchor="w"
            )

            title.pack(
                anchor="w",
                padx=20,
                pady=(18, 5)
            )

            company = ctk.CTkLabel(

                card,

                text=job.company,

                font=(
                    "Arial",
                    15
                ),

                anchor="w"
            )

            company.pack(
                anchor="w",
                padx=20
            )

            source_name = getattr(
                job,
                "site",
                "Bilinmiyor"
            )

            source_colors = {
                "Kariyer": "#1F6AA5",
                "Jooble": "#2E8B57"
            }

            source_badge = ctk.CTkLabel(

                card,

                text=source_name,

                fg_color=source_colors.get(
                    source_name,
                    "#555555"
                ),

                text_color="white",

                corner_radius=10,

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

            location = ctk.CTkLabel(

                card,

                text=f"📍 {job.location}",

                font=(
                    "Arial",
                    14
                ),

                anchor="w"
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

                date_label = ctk.CTkLabel(

                    card,

                    text=f"🕒 {job_date_text}",

                    font=("Arial", 13),

                    anchor="w"
                )

                date_label.pack(
                    anchor="w",
                    padx=20,
                    pady=(4, 0)
                )

            details = ctk.CTkLabel(

                card,

                text=(
                    f"Deneyim: {job.experience}   |   "
                    f"Çalışma: {job.remote}"
                ),

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

            button_frame = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            button_frame.pack(
                fill="x",
                padx=15,
                pady=(0, 15)
            )

            open_button = ctk.CTkButton(

                button_frame,

                text="İlana Git",

                width=130,

                height=38,

                corner_radius=12,

                command=lambda url=job.url:
                webbrowser.open(url)
            )

            open_button.pack(
                side="right",
                padx=5
            )

            detail_button = ctk.CTkButton(

                button_frame,

                text="Detay",

                width=100,

                height=38,

                corner_radius=12,

                command=lambda j=job:
                self.show_job_details(j)
            )

            detail_button.pack(
                side="right",
                padx=5
            )

            is_favorite = any(

                fav.get("url") == getattr(job, "url", "")

                for fav in self.favorite_jobs
            )

            favorite_button = ctk.CTkButton(

                button_frame,

                text="★ Favori" if not is_favorite else "★ Favorilerde",

                width=160,

                height=38,

                corner_radius=12,

                fg_color="#1F6AA5" if is_favorite else "#444444",

                hover_color="#144870" if is_favorite else "#AA3333",

                text_color="white",

                command=lambda j=job:
                self.toggle_favorite(j)
            )

            favorite_button.pack(
                side="right",
                padx=5
            )

            favorite_button.bind(

                "<Enter>",

                lambda e, b=favorite_button, fav=is_favorite:

                self.safe_button_text(
                    b,

                    "Favorilerden kaldır" 
                    if fav 
                    else "★ Favori"
                )
            )

            favorite_button.bind(

                "<Leave>",

                lambda e, b=favorite_button, fav=is_favorite:
                self.safe_button_text(
                    b,

                    "★ Favorilerde"
                    if fav
                    else "★ Favori"
                )
            )

        total_pages = max(

            1,

            math.ceil(
                len(self.filtered_jobs)
                / self.jobs_per_page
            )
        )

        self.page_label.configure(

            text=(
                f"Sayfa "
                f"{self.current_page}"
                f" / "
                f"{total_pages}"
            )
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

            self.current_page += 1

            self.display_jobs()

    def prev_page(self):

        if self.current_page > 1:

            self.current_page -= 1

            self.display_jobs()


if __name__ == "__main__":

    app = JobApp()

    app.mainloop()
