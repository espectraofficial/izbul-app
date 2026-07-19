import io
import threading
import webbrowser

import customtkinter as ctk
import requests
from PIL import Image

from scrapers.eleman import fetch_eleman_detail_description
from scrapers.kariyer import fetch_kariyer_detail_description
from ui.config import (
    APPLICATION_STATUSES,
    APPLICATION_STATUS_COLORS
)
from ui.formatters import (
    format_job_date_text,
    format_saved_at
)


class JobDetailsMixin:

    def get_company_initials(self, company):

        words = [
            word
            for word in str(company or "").split()
            if word
        ]

        if not words:

            return "?"

        initials = "".join(
            word[0].upper()
            for word in words[:2]
        )

        return initials[:2]

    def get_logo_image(self, job):

        logo_url = getattr(
            job,
            "logo_url",
            ""
        )

        if not logo_url:

            return None

        if logo_url in self.logo_images:

            return self.logo_images[logo_url]

        self.logo_images[logo_url] = None

        threading.Thread(
            target=self.download_logo_image,
            args=(logo_url,),
            daemon=True
        ).start()

        return None

    def download_logo_image(self, logo_url):

        try:

            response = requests.get(
                logo_url,
                timeout=8
            )

            response.raise_for_status()

            image = Image.open(
                io.BytesIO(response.content)
            ).convert("RGBA")

            logo_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(56, 56)
            )

            self.logo_images[logo_url] = logo_image

            self.schedule_logo_refresh()

        except Exception as e:

            print("Logo yüklenemedi:", e)

            self.logo_images[logo_url] = None

    def schedule_logo_refresh(self):

        if self.logo_refresh_pending:

            return

        self.logo_refresh_pending = True

        self.after(
            250,
            self.refresh_logos
        )

    def refresh_logos(self):

        self.logo_refresh_pending = False

        self.display_jobs()

    def get_job_link(self, job):

        return (
            getattr(
                job,
                "apply_url",
                ""
            ) or
            getattr(
                job,
                "url",
                ""
            )
        )

    def open_job_link(self, job):

        job_link = self.get_job_link(job)

        if not job_link:

            self.show_toast(
                "Bu ilan için bağlantı bulunamadı.",
                "#C0392B"
            )

            return

        webbrowser.open(job_link)

    def copy_job_link(self, job):

        job_link = self.get_job_link(job)

        if not job_link:

            self.show_toast(
                "Kopyalanacak bağlantı bulunamadı.",
                "#C0392B"
            )

            return

        self.clipboard_clear()
        self.clipboard_append(job_link)

        self.show_toast(
            "İlan bağlantısı kopyalandı.",
            "#27AE60"
        )

    def update_description_box(self, description_box, description):

        try:

            if not description_box.winfo_exists():

                return

            description_box.configure(
                state="normal"
            )

            description_box.delete(
                "1.0",
                "end"
            )

            description_box.insert(
                "1.0",
                description
            )

            description_box.configure(
                state="disabled"
            )

        except Exception as e:

            print("Açıklama kutusu güncellenemedi:", e)

    def save_loaded_description(self, job, description):

        if hasattr(job, "description"):

            job.description = description

        job_url = getattr(
            job,
            "url",
            ""
        )

        for favorite in self.favorite_jobs:

            if favorite.get("url") == job_url:

                favorite["description"] = description

                self.save_favorites()

                break

    def load_kariyer_description(self, job, description_box):

        def run():

            try:

                description = fetch_kariyer_detail_description(
                    self.get_job_link(job)
                )

                if not description:

                    description = (
                        "Kariyer.net ilan açıklaması alınamadı. "
                        "Başvuru sayfasından görüntüleyebilirsiniz."
                    )

                else:

                    self.save_loaded_description(
                        job,
                        description
                    )

                self.after(
                    0,
                    lambda:
                    self.update_description_box(
                        description_box,
                        description
                    )
                )

            except Exception as e:

                print("Kariyer detay açıklaması alınamadı:", e)

                self.after(
                    0,
                    lambda:
                    self.update_description_box(
                        description_box,
                        (
                            "Kariyer.net ilan açıklaması alınamadı. "
                            "Başvuru sayfasından görüntüleyebilirsiniz."
                        )
                    )
                )

        threading.Thread(
            target=run,
            daemon=True
        ).start()

    def load_eleman_description(self, job, description_box):

        def run():

            try:

                description = fetch_eleman_detail_description(
                    self.get_job_link(job),
                    title=getattr(
                        job,
                        "title",
                        ""
                    ),
                    company=getattr(
                        job,
                        "company",
                        ""
                    ),
                    location=getattr(
                        job,
                        "location",
                        ""
                    )
                )

                if not description:

                    description = (
                        "Eleman.net ilan açıklaması alınamadı. "
                        "Başvuru sayfasından görüntüleyebilirsiniz."
                    )

                else:

                    self.save_loaded_description(
                        job,
                        description
                    )

                self.after(
                    0,
                    lambda:
                    self.update_description_box(
                        description_box,
                        description
                    )
                )

            except Exception as e:

                print("Eleman.net detay açıklaması alınamadı:", e)

                self.after(
                    0,
                    lambda:
                    self.update_description_box(
                        description_box,
                        (
                            "Eleman.net ilan açıklaması alınamadı. "
                            "Başvuru sayfasından görüntüleyebilirsiniz."
                        )
                    )
                )

        threading.Thread(
            target=run,
            daemon=True
        ).start()

    def show_job_details(self, job):

        detail_window = ctk.CTkToplevel(self)

        detail_window.title("İlan Detayı")

        detail_window.geometry("720x620")

        detail_window.minsize(620, 520)

        detail_window.transient(self)

        detail_window.focus()

        container = ctk.CTkScrollableFrame(
            detail_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        header_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        header_frame.pack(
            fill="x",
            padx=22,
            pady=(22, 10)
        )

        logo_frame = ctk.CTkFrame(
            header_frame,
            width=66,
            height=66,
            corner_radius=12
        )

        logo_frame.pack(
            side="left",
            padx=(0, 14)
        )

        logo_frame.pack_propagate(False)

        logo_image = self.get_logo_image(job)

        if logo_image:

            logo_label = ctk.CTkLabel(
                logo_frame,
                text="",
                image=logo_image
            )

        else:

            logo_label = ctk.CTkLabel(
                logo_frame,
                text=self.get_company_initials(
                    getattr(
                        job,
                        "company",
                        ""
                    )
                ),
                font=(
                    "Arial",
                    18,
                    "bold"
                )
            )

        logo_label.pack(
            fill="both",
            expand=True
        )

        title_frame = ctk.CTkFrame(
            header_frame,
            fg_color="transparent"
        )

        title_frame.pack(
            side="left",
            fill="x",
            expand=True
        )

        title_label = ctk.CTkLabel(

            title_frame,

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
            pady=(0, 8)
        )

        company_label = ctk.CTkLabel(

            title_frame,

            text=getattr(job, "company", ""),

            font=(
                "Arial",
                17
            ),

            anchor="w",

            justify="left",
            wraplength=560
        )

        company_label.pack(
            fill="x",
            pady=(0, 2)
        )

        meta_frame = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        meta_frame.pack(
            fill="x",
            padx=22,
            pady=(0, 16)
        )

        meta_items = [
            getattr(job, "site", ""),
            getattr(job, "location", ""),
            format_job_date_text(
                getattr(
                    job,
                    "job_date_text",
                    ""
                )
            ),
            getattr(job, "experience", ""),
            getattr(job, "remote", "")
        ]

        for item in meta_items:

            if not item:

                continue

            ctk.CTkLabel(
                meta_frame,
                text=item,
                fg_color="#333333",
                corner_radius=10,
                font=(
                    "Arial",
                    12,
                    "bold"
                ),
                padx=10,
                pady=5
            ).pack(
                side="left",
                padx=(0, 8)
            )

        favorite_data = self.get_favorite_data(job)
        is_favorite = favorite_data is not None

        if is_favorite:

            application_status = favorite_data.get(
                "application_status",
                getattr(
                    job,
                    "application_status",
                    "Kaydedildi"
                )
            )

            status_frame = ctk.CTkFrame(
                container,
                fg_color="transparent"
            )

            status_frame.pack(
                fill="x",
                padx=22,
                pady=(0, 16)
            )

            ctk.CTkLabel(
                status_frame,
                text="Başvuru Durumu",
                font=(
                    "Arial",
                    14,
                    "bold"
                )
            ).pack(
                side="left",
                padx=(0, 10)
            )

            status_var = ctk.StringVar(
                value=application_status
            )

            ctk.CTkOptionMenu(
                status_frame,
                values=APPLICATION_STATUSES,
                variable=status_var,
                width=160,
                height=36,
                command=lambda value:
                self.update_application_status(
                    job,
                    value
                )
            ).pack(
                side="left"
            )

            favorite_dates = []

            saved_at = format_saved_at(
                favorite_data.get(
                    "saved_at",
                    getattr(
                        job,
                        "saved_at",
                        ""
                    )
                )
            )

            status_updated_at = format_saved_at(
                favorite_data.get(
                    "status_updated_at",
                    getattr(
                        job,
                        "status_updated_at",
                        ""
                    )
                )
            )

            if saved_at:

                favorite_dates.append(
                    f"Favoriye eklenme: {saved_at}"
                )

            if status_updated_at:

                favorite_dates.append(
                    f"Durum güncelleme: {status_updated_at}"
                )

            if favorite_dates:

                ctk.CTkLabel(
                    container,
                    text="   |   ".join(favorite_dates),
                    text_color="gray",
                    font=(
                        "Arial",
                        13
                    ),
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=22,
                    pady=(0, 14)
                )

            note_label = ctk.CTkLabel(
                container,
                text="Başvuru Notu",
                font=(
                    "Arial",
                    15,
                    "bold"
                ),
                anchor="w"
            )

            note_label.pack(
                fill="x",
                padx=22,
                pady=(0, 8)
            )

            note_box = ctk.CTkTextbox(
                container,
                height=95,
                wrap="word"
            )

            note_box.pack(
                fill="x",
                padx=22,
                pady=(0, 10)
            )

            note_box.insert(
                "1.0",
                favorite_data.get(
                    "application_note",
                    getattr(
                        job,
                        "application_note",
                        ""
                    )
                )
            )

            note_button = ctk.CTkButton(
                container,
                text="Notu Kaydet",
                width=130,
                height=36,
                corner_radius=10,
                fg_color="#3A3A3A",
                hover_color="#4A4A4A",
                command=lambda j=job, box=note_box:
                self.update_application_note(
                    j,
                    box.get(
                        "1.0",
                        "end"
                    )
                )
            )

            note_button.pack(
                anchor="w",
                padx=22,
                pady=(0, 16)
            )

        ctk.CTkLabel(
            container,
            text="İlan Açıklaması",
            font=(
                "Arial",
                15,
                "bold"
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=22,
            pady=(0, 8)
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

        job_site = getattr(
            job,
            "site",
            ""
        )

        should_fetch_kariyer_detail = (
            not description and
            job_site == "Kariyer"
        )

        should_fetch_eleman_detail = (
            job_site == "Eleman.net" and
            (
                not description or
                description.endswith("...") or
                len(description) <= 450
            )
        )

        if should_fetch_kariyer_detail:

            description = "Kariyer.net ilan detayı yükleniyor..."

        elif should_fetch_eleman_detail:

            description = "Eleman.net ilan detayı yükleniyor..."

        elif not description:

            description = "Bu kaynak detay açıklaması sağlamıyor."

        description_box.insert(
            "1.0",
            description
        )

        description_box.configure(
            state="disabled"
        )

        if should_fetch_kariyer_detail:

            self.load_kariyer_description(
                job,
                description_box
            )

        if should_fetch_eleman_detail:

            self.load_eleman_description(
                job,
                description_box
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

            text=(
                "★ Favoriden Çıkar"
                if is_favorite
                else "★ Favoriye Ekle"
            ),

            width=180,

            height=40,

            fg_color="#5B3F00" if is_favorite else "#2F2F2F",

            hover_color="#AA3333" if is_favorite else "#4A4A4A",

            command=lambda:
            self.toggle_favorite(job)
        )

        favorite_button.pack(
            side="left",
            padx=(0, 10)
        )

        copy_button = ctk.CTkButton(

            button_frame,

            text="Linki Kopyala",

            width=130,

            height=40,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",

            command=lambda:
            self.copy_job_link(job)
        )

        copy_button.pack(
            side="right",
            padx=(10, 0)
        )

        open_button = ctk.CTkButton(

            button_frame,

            text="Başvuruya Git",

            width=142,

            height=40,
            fg_color="#2E8B57",
            hover_color="#247348",
            font=("Arial", 14, "bold"),

            command=lambda:
            self.open_job_link(job)
        )

        open_button.pack(
            side="right"
        )
