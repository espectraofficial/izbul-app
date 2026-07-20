import logging
import threading
import webbrowser
from urllib.parse import quote_plus

import customtkinter as ctk

from ui.search_cache import load_cached_search, save_cached_search
from ui.storage import save_settings
from utils.search_engine import SOURCE_KEY_BY_SITE, normalize_text, smart_search


logger = logging.getLogger(__name__)


class SearchMixin:

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

        self.show_cached_search_preview(
            keyword,
            selected_city,
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

        source_errors = search_report.get("source_errors", {})
        all_sources_failed = bool(selected_sources) and all(
            source in source_errors
            for source in selected_sources
        )

        if (
            not jobs
            and self.active_cached_search
            and all_sources_failed
        ):
            jobs = self.active_cached_search["jobs"]
            self.cache_preview_active = True
            self.cache_refresh_failed = True

        else:
            self.cache_preview_active = False
            self.cache_refresh_failed = False

            if jobs:
                try:
                    save_cached_search(
                        keyword,
                        selected_city,
                        selected_sources,
                        jobs,
                        search_report=search_report
                    )
                except Exception:
                    logger.exception("Arama önbelleği kaydedilemedi")

        self.last_search_report = search_report
        self.all_jobs = jobs
        self.filtered_jobs = jobs
        self.current_page = 1
        self.search_summary_message = self.build_search_summary(
            jobs,
            selected_sources,
            search_report
        )
        self.active_cached_search = None

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

        if getattr(self, "cache_preview_active", False):

            if getattr(self, "cache_refresh_failed", False):
                summary += " Kaynaklar yenilenemedi; önbellekteki sonuçlar gösteriliyor."
            else:
                summary += " Önbellekten gösteriliyor; kaynaklar yenileniyor."

        return summary

    def show_cached_search_preview(self, keyword, city, selected_sources):

        cached_search = load_cached_search(
            keyword,
            city,
            selected_sources
        )

        self.active_cached_search = cached_search

        if not cached_search:
            self.cache_preview_active = False
            self.cache_refresh_failed = False
            return False

        self.cache_preview_active = True
        self.cache_refresh_failed = False
        self.last_search_report = cached_search["search_report"]
        self.all_jobs = cached_search["jobs"]
        self.filtered_jobs = cached_search["jobs"]
        self.current_page = 1
        self.apply_filters()
        return True

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
