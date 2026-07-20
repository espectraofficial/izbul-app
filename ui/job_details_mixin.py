import io
import hashlib
import threading
import webbrowser

import customtkinter as ctk
import requests
from PIL import Image, ImageDraw, ImageFont, ImageTk

from scrapers.eleman import fetch_eleman_detail_description
from scrapers.kariyer import fetch_kariyer_detail_description
from ui.config import (
    APPLICATION_STATUSES
)
from ui.formatters import (
    format_job_date_text,
    format_saved_at
)


LOGO_LOADING = object()
LOGO_FAILED = object()
LOGO_MISSING = object()

LOGO_PLACEHOLDER_COLORS = (
    "#3D729D",
    "#3B806F",
    "#725F9A",
    "#A06B48",
    "#9C5268",
    "#637C4B",
    "#39758A"
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

    def get_logo_placeholder(self, company, size=56):

        company_text = str(company or "Bilinmeyen Firma").strip()
        cache_key = (company_text.casefold(), size)
        cached_image = self.logo_placeholder_images.get(cache_key)

        if cached_image is not None:

            return cached_image

        scale = 3
        canvas_size = size * scale
        digest = hashlib.sha256(
            company_text.casefold().encode("utf-8")
        ).digest()
        background = LOGO_PLACEHOLDER_COLORS[
            digest[0] % len(LOGO_PLACEHOLDER_COLORS)
        ]
        image = Image.new(
            "RGBA",
            (canvas_size, canvas_size),
            (0, 0, 0, 0)
        )
        draw = ImageDraw.Draw(image)
        inset = 2 * scale
        draw.rounded_rectangle(
            (
                inset,
                inset,
                canvas_size - inset - 1,
                canvas_size - inset - 1
            ),
            radius=18 * scale,
            fill=background,
            outline=(255, 255, 255, 38),
            width=scale
        )
        font = self.load_placeholder_font(18 * scale)
        draw.text(
            (canvas_size / 2, canvas_size / 2 - scale),
            self.get_company_initials(company_text),
            fill="white",
            font=font,
            anchor="mm"
        )
        image = image.resize(
            (size, size),
            Image.Resampling.LANCZOS
        )
        photo = ImageTk.PhotoImage(image)
        self.logo_placeholder_images[cache_key] = photo

        return photo

    @staticmethod
    def load_placeholder_font(size):

        for font_name in (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf"
        ):

            try:

                return ImageFont.truetype(font_name, size)

            except OSError:

                continue

        return ImageFont.load_default(size=size)

    def register_logo_label(self, logo_url, logo_label):

        if not logo_url:

            return

        self.logo_labels_by_url.setdefault(
            logo_url,
            []
        ).append(logo_label)

    def get_logo_image(self, job):

        logo_url = getattr(
            job,
            "logo_url",
            ""
        )

        if not logo_url:

            return None

        cached_logo = self.logo_images.get(
            logo_url,
            LOGO_MISSING
        )

        if cached_logo is LOGO_LOADING or cached_logo is LOGO_FAILED:

            return None

        if cached_logo is not LOGO_MISSING:

            return self.build_logo_photo(cached_logo)

        self.logo_images[logo_url] = LOGO_LOADING

        threading.Thread(
            target=self.download_logo_image,
            args=(logo_url,),
            daemon=True
        ).start()

        return None

    def build_logo_photo(self, cached_logo):

        if not isinstance(cached_logo, dict):

            return cached_logo

        photo = cached_logo.get("photo")

        if photo is None:

            image = cached_logo["image"]

            if image.size != (56, 56):

                image = image.resize(
                    (56, 56),
                    Image.Resampling.LANCZOS
                )

            photo = ImageTk.PhotoImage(image)
            cached_logo["photo"] = photo

        return photo

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

            if (
                image.width < 2 or
                image.height < 2 or
                image.getbbox() is None
            ):

                raise ValueError("Geçersiz veya boş logo görseli")

            self.logo_images[logo_url] = {
                "image": image,
                "photo": None
            }

            self.schedule_logo_refresh()

        except Exception as e:

            print("Logo yüklenemedi:", e)

            self.logo_images[logo_url] = LOGO_FAILED

    def schedule_logo_refresh(self):

        self.logo_refresh_queue.put(True)

    def poll_logo_refresh_queue(self):

        should_refresh = False

        while not self.logo_refresh_queue.empty():

            self.logo_refresh_queue.get_nowait()
            should_refresh = True

        if should_refresh:

            self.refresh_logos()

        self.after(
            100,
            self.poll_logo_refresh_queue
        )

    def refresh_logos(self):

        for logo_url, labels in list(
            getattr(
                self,
                "logo_labels_by_url",
                {}
            ).items()
        ):

            cached_logo = self.logo_images.get(logo_url)

            if (
                cached_logo is LOGO_LOADING or
                cached_logo is LOGO_FAILED or
                cached_logo is None
            ):

                continue

            logo_image = self.build_logo_photo(
                cached_logo
            )

            live_labels = []

            for label in labels:

                try:

                    if not label.winfo_exists():

                        continue

                    label.configure(
                        text="",
                        image=logo_image
                    )

                    live_labels.append(label)

                except Exception:

                    continue

            if live_labels:

                self.logo_labels_by_url[logo_url] = live_labels

            else:

                self.logo_labels_by_url.pop(
                    logo_url,
                    None
                )

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

        favorite = getattr(
            self,
            "favorite_jobs_by_url",
            {}
        ).get(job_url)

        if favorite:

            favorite["description"] = description

            self.save_favorites()

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

        if not logo_image:

            logo_image = self.get_logo_placeholder(
                getattr(
                    job,
                    "company",
                    ""
                )
            )

        logo_label = ctk.CTkLabel(
            logo_frame,
            text="",
            image=logo_image
        )

        self.register_logo_label(
            getattr(
                job,
                "logo_url",
                ""
            ),
            logo_label
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
