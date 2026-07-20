import csv
import json
import os
import webbrowser
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ui.config import APPLICATION_STATUSES
from ui.formatters import (
    format_saved_at,
    get_current_timestamp
)


class FavoritesMixin:

    def rebuild_favorites_index(self):

        self.favorite_jobs_by_url = {
            favorite.get("url"): favorite
            for favorite in getattr(self, "favorite_jobs", [])
            if favorite.get("url")
        }

    def rebuild_hidden_jobs_index(self):

        self.hidden_job_urls = {
            hidden.get("url")
            for hidden in getattr(self, "hidden_jobs", [])
            if hidden.get("url")
        }

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

        finally:

            self.rebuild_favorites_index()

    # =========================
    # LOAD FAVORITES
    # =========================

    def load_favorites(self):

        if not os.path.exists(self.favorites_file):

            self.favorite_jobs = []
            self.rebuild_favorites_index()

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

                changed = False

                for favorite in self.favorite_jobs:

                    if "application_status" not in favorite:

                        favorite["application_status"] = "Kaydedildi"
                        changed = True

                    if "application_note" not in favorite:

                        favorite["application_note"] = ""
                        changed = True

                    if "saved_at" not in favorite:

                        favorite["saved_at"] = get_current_timestamp()
                        changed = True

                    if "status_updated_at" not in favorite:

                        favorite["status_updated_at"] = favorite.get(
                            "saved_at",
                            get_current_timestamp()
                        )
                        changed = True

                if changed:

                    self.save_favorites()
            
            else:
                self.favorite_jobs = []

            self.rebuild_favorites_index()

        except Exception as e:

            print("Favoriler yüklenemedi:", e)

            self.favorite_jobs = []
            self.rebuild_favorites_index()

    def save_hidden_jobs(self):

        try:

            Path(self.hidden_jobs_file).parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                self.hidden_jobs_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.hidden_jobs,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as e:

            print("Gizlenen ilanlar kaydedilemedi:", e)

        finally:

            self.rebuild_hidden_jobs_index()

    def load_hidden_jobs(self):

        if not os.path.exists(self.hidden_jobs_file):

            self.hidden_jobs = []
            self.rebuild_hidden_jobs_index()

            return

        try:

            with open(
                self.hidden_jobs_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            self.hidden_jobs = (
                data
                if isinstance(data, list)
                else []
            )

            self.rebuild_hidden_jobs_index()

        except Exception as e:

            print("Gizlenen ilanlar yüklenemedi:", e)

            self.hidden_jobs = []
            self.rebuild_hidden_jobs_index()

    def get_job_identity(self, job):

        return str(
            getattr(
                job,
                "url",
                ""
            ) or getattr(
                job,
                "apply_url",
                ""
            )
        ).strip()

    def is_hidden_job(self, job):

        job_identity = self.get_job_identity(job)

        if not job_identity:

            return False

        return job_identity in getattr(
            self,
            "hidden_job_urls",
            set()
        )

    def hide_job(self, job):

        job_identity = self.get_job_identity(job)

        if not job_identity:

            self.show_toast(
                "Bu ilan gizlenemedi.",
                "#C0392B"
            )

            return

        if not self.is_hidden_job(job):

            self.hidden_jobs.append(
                {
                    "url": job_identity,
                    "title": str(
                        getattr(
                            job,
                            "title",
                            ""
                        )
                    ),
                    "company": str(
                        getattr(
                            job,
                            "company",
                            ""
                        )
                    ),
                    "site": str(
                        getattr(
                            job,
                            "site",
                            ""
                        )
                    ),
                    "hidden_at": get_current_timestamp()
                }
            )

            self.save_hidden_jobs()

        self.show_toast(
            "İlan gizlendi.",
            "#3A3A3A"
        )

        self.apply_filters()

    def clear_hidden_jobs(self):

        self.hidden_jobs = []
        self.save_hidden_jobs()
        self.apply_filters()

        self.show_toast(
            "Gizlenen ilanlar temizlendi.",
            "#27AE60"
        )

    def restore_hidden_job(self, hidden_job, window=None):

        job_url = str(
            hidden_job.get(
                "url",
                ""
            )
        )

        self.hidden_jobs = [
            item
            for item in self.hidden_jobs
            if item.get("url") != job_url
        ]

        self.save_hidden_jobs()
        self.apply_filters()

        self.show_toast(
            "İlan tekrar görünür yapıldı.",
            "#27AE60"
        )

        if window and window.winfo_exists():

            window.destroy()
            self.show_hidden_jobs_window()

    def show_hidden_jobs_window(self):

        hidden_window = ctk.CTkToplevel(self)

        hidden_window.title("Gizlenen İlanlar")

        hidden_window.geometry("680x520")

        hidden_window.minsize(560, 420)

        hidden_window.transient(self)

        hidden_window.focus()

        container = ctk.CTkScrollableFrame(
            hidden_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        header = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=16,
            pady=(16, 12)
        )

        ctk.CTkLabel(
            header,
            text="Gizlenen İlanlar",
            font=(
                "Arial",
                24,
                "bold"
            )
        ).pack(
            side="left"
        )

        if self.hidden_jobs:

            clear_button = ctk.CTkButton(
                header,
                text="Tümünü Temizle",
                width=130,
                height=34,
                corner_radius=10,
                fg_color="#5A2F2F",
                hover_color="#744040",
                command=lambda:
                (
                    self.clear_hidden_jobs(),
                    hidden_window.destroy()
                )
            )

            clear_button.pack(
                side="right"
            )

        if not self.hidden_jobs:

            ctk.CTkLabel(
                container,
                text="Gizlenen ilan yok.",
                font=(
                    "Arial",
                    20,
                    "bold"
                )
            ).pack(
                pady=(80, 8)
            )

            ctk.CTkLabel(
                container,
                text="Arama sonuçlarında Gizle butonunu kullanınca ilanlar burada listelenir.",
                text_color="gray",
                font=(
                    "Arial",
                    14
                ),
                wraplength=480,
                justify="center"
            ).pack()

            return

        for hidden_job in self.hidden_jobs:

            card = ctk.CTkFrame(
                container,
                corner_radius=14
            )

            card.pack(
                fill="x",
                padx=16,
                pady=8
            )

            info_frame = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            info_frame.pack(
                side="left",
                fill="x",
                expand=True,
                padx=16,
                pady=14
            )

            ctk.CTkLabel(
                info_frame,
                text=hidden_job.get(
                    "title",
                    "Başlıksız ilan"
                ),
                font=(
                    "Arial",
                    16,
                    "bold"
                ),
                anchor="w",
                justify="left",
                wraplength=360
            ).pack(
                fill="x",
                anchor="w"
            )

            details = " · ".join(
                value
                for value in [
                    hidden_job.get(
                        "company",
                        ""
                    ),
                    hidden_job.get(
                        "site",
                        ""
                    ),
                    format_saved_at(
                        hidden_job.get(
                            "hidden_at",
                            ""
                        )
                    )
                ]
                if value
            )

            ctk.CTkLabel(
                info_frame,
                text=details,
                text_color="gray",
                font=(
                    "Arial",
                    13
                ),
                anchor="w",
                justify="left",
                wraplength=360
            ).pack(
                fill="x",
                anchor="w",
                pady=(6, 0)
            )

            action_frame = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            action_frame.pack(
                side="right",
                padx=14,
                pady=14
            )

            ctk.CTkButton(
                action_frame,
                text="Geri Al",
                width=90,
                height=34,
                corner_radius=10,
                command=lambda item=hidden_job:
                self.restore_hidden_job(
                    item,
                    hidden_window
                )
            ).pack(
                side="left",
                padx=(0, 8)
            )

            ctk.CTkButton(
                action_frame,
                text="Aç",
                width=70,
                height=34,
                corner_radius=10,
                fg_color="#2E8B57",
                hover_color="#247348",
                command=lambda url=hidden_job.get("url", ""):
                webbrowser.open(url)
            ).pack(
                side="left"
            )

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
            "job_date_text": str(getattr(job, "job_date_text", "")),
            "logo_url": str(getattr(job, "logo_url", "")),
            "application_status": "Kaydedildi",
            "application_note": "",
            "saved_at": get_current_timestamp(),
            "status_updated_at": get_current_timestamp()
        }

        existing = getattr(
            self,
            "favorite_jobs_by_url",
            {}
        ).get(job_url)

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

        if self.view_mode != "favorites":

            self.push_navigation_state()

        self.view_mode = "favorites"

        self.reset_favorite_filters(
            save_preferences=False
        )

        self.apply_filters()

    def get_favorite_data(self, job):

        job_url = getattr(
            job,
            "url",
            ""
        )

        return getattr(
            self,
            "favorite_jobs_by_url",
            {}
        ).get(job_url)

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
                self.logo_url = data.get("logo_url", "")
                self.application_status = data.get(
                    "application_status",
                    "Kaydedildi"
                )
                self.application_note = data.get(
                    "application_note",
                    ""
                )
                self.saved_at = data.get(
                    "saved_at",
                    ""
                )
                self.status_updated_at = data.get(
                    "status_updated_at",
                    ""
                )

        return [

            FavoriteJob(job)

            for job in self.favorite_jobs
        ]

    def update_application_status(self, job, status):

        job_url = getattr(
            job,
            "url",
            ""
        )

        if status not in APPLICATION_STATUSES:

            status = "Kaydedildi"

        favorite = getattr(
            self,
            "favorite_jobs_by_url",
            {}
        ).get(job_url)

        if favorite:

            favorite["application_status"] = status
            favorite["status_updated_at"] = get_current_timestamp()

        if hasattr(job, "application_status"):

            job.application_status = status

        if hasattr(job, "status_updated_at"):

            job.status_updated_at = get_current_timestamp()

        self.save_favorites()

        self.set_status_message(
            f"Başvuru durumu güncellendi: {status}"
        )

        if self.view_mode == "favorites":

            self.apply_filters()

    def update_application_note(self, job, note):

        job_url = getattr(
            job,
            "url",
            ""
        )

        note = str(
            note or ""
        ).strip()

        favorite = getattr(
            self,
            "favorite_jobs_by_url",
            {}
        ).get(job_url)

        if favorite:

            favorite["application_note"] = note

        if hasattr(job, "application_note"):

            job.application_note = note

        self.save_favorites()

        self.show_toast(
            "Başvuru notu kaydedildi.",
            "#27AE60"
        )

        if self.view_mode == "favorites":

            self.apply_filters()

    def export_favorites_csv(self):

        if not self.favorite_jobs:

            self.show_toast(
                "Dışa aktarılacak favori bulunamadı.",
                "#C0392B"
            )

            return

        file_path = filedialog.asksaveasfilename(
            title="Favorileri CSV olarak kaydet",
            defaultextension=".csv",
            filetypes=[
                (
                    "CSV dosyası",
                    "*.csv"
                )
            ],
            initialfile="izbul-favoriler.csv"
        )

        if not file_path:

            return

        try:

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "Pozisyon",
                        "Firma",
                        "Konum",
                        "Kaynak",
                        "Başvuru Durumu",
                        "Çalışma Şekli",
                        "Deneyim",
                        "Tarih",
                        "Favoriye Eklenme",
                        "Durum Güncelleme",
                        "Not",
                        "Link"
                    ]
                )

                writer.writeheader()

                for favorite in self.favorite_jobs:

                    writer.writerow(
                        {
                            "Pozisyon": favorite.get("title", ""),
                            "Firma": favorite.get("company", ""),
                            "Konum": favorite.get("location", ""),
                            "Kaynak": favorite.get("site", ""),
                            "Başvuru Durumu": favorite.get(
                                "application_status",
                                "Kaydedildi"
                            ),
                            "Çalışma Şekli": favorite.get("remote", ""),
                            "Deneyim": favorite.get("experience", ""),
                            "Tarih": favorite.get("job_date_text", ""),
                            "Favoriye Eklenme": format_saved_at(
                                favorite.get("saved_at", "")
                            ),
                            "Durum Güncelleme": format_saved_at(
                                favorite.get("status_updated_at", "")
                            ),
                            "Not": favorite.get("application_note", ""),
                            "Link": (
                                favorite.get("apply_url", "") or
                                favorite.get("url", "")
                            )
                        }
                    )

            self.show_toast(
                "Favoriler CSV olarak kaydedildi.",
                "#27AE60"
            )

        except Exception as e:

            print("Favoriler dışa aktarılamadı:", e)

            self.show_toast(
                "Favoriler dışa aktarılamadı.",
                "#C0392B"
            )
