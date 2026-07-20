import logging
import threading
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from scrapers.jooble import get_jooble_api_key, save_jooble_api_key, search_jooble
from ui.config import APP_VERSION, DEFAULT_SETTINGS, get_theme_label, get_theme_value
from ui.diagnostics import build_diagnostic_archive
from ui.storage import get_app_data_dir, save_settings


class SettingsMixin:

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
            pady=(0, 8)
        )

        def export_diagnostic_report():

            default_name = (
                "Izbul-tanilama-"
                + datetime.now().strftime("%Y%m%d-%H%M%S")
                + ".zip"
            )

            destination = filedialog.asksaveasfilename(
                parent=settings_window,
                title="Tanılama Raporunu Kaydet",
                initialfile=default_name,
                defaultextension=".zip",
                filetypes=[("ZIP arşivi", "*.zip")]
            )

            if not destination:

                return

            try:

                build_diagnostic_archive(destination)
                set_settings_status(
                    "Tanılama raporu dışa aktarıldı.",
                    "#27AE60"
                )

            except Exception as error:

                logging.getLogger(__name__).exception(
                    "Tanılama raporu dışa aktarılamadı"
                )
                set_settings_status(
                    f"Tanılama raporu oluşturulamadı: {error}",
                    "#C0392B"
                )

        diagnostics_button = ctk.CTkButton(
            container,
            text="Tanılama Raporunu Dışa Aktar",
            height=38,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=export_diagnostic_report
        )

        diagnostics_button.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
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
