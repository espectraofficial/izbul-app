import logging
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk

from ui.storage import save_settings


logger = logging.getLogger(__name__)


class NavigationMixin:

    def get_running_app_path(self):

        if getattr(
            sys,
            "frozen",
            False
        ):

            return Path(
                sys.executable
            ).resolve()

        return Path(
            __file__
        ).resolve()

    def is_running_from_applications(self):

        if sys.platform != "darwin":

            return False

        app_path = str(
            self.get_running_app_path()
        )

        return (
            "/Applications/Izbul.app/" in app_path or
            "/Applications/İzbul.app/" in app_path or
            "/Applications/Izbul.app" in app_path or
            "/Applications/İzbul.app" in app_path
        )

    def get_mounted_dmg_volume(self):

        volume = Path("/Volumes/Izbul")

        if volume.exists():

            return volume

        return None

    def show_install_cleanup_prompt(self):

        if sys.platform != "darwin":

            return

        if self.settings.get("install_cleanup_prompt_seen"):

            return

        if not self.is_running_from_applications():

            return

        volume = self.get_mounted_dmg_volume()

        if not volume:

            return

        cleanup_window = ctk.CTkToplevel(self)
        cleanup_window.title("Kurulum Tamamlandı")
        cleanup_window.geometry("430x230")
        cleanup_window.resizable(False, False)
        cleanup_window.transient(self)
        cleanup_window.focus_force()

        container = ctk.CTkFrame(
            cleanup_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=16
        )

        ctk.CTkLabel(
            container,
            text="Kurulum tamamlandı",
            font=(
                "Arial",
                21,
                "bold"
            )
        ).pack(
            pady=(18, 8)
        )

        ctk.CTkLabel(
            container,
            text=(
                "İzbul Applications klasöründen çalışıyor.\n"
                "Artık kurulum disk imajını çıkarmak ister misiniz?"
            ),
            justify="center",
            text_color="#D8DEE9",
            font=(
                "Arial",
                14
            )
        ).pack(
            padx=24,
            pady=(0, 18)
        )

        actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

        def mark_seen():

            self.settings["install_cleanup_prompt_seen"] = True
            save_settings(
                self.settings
            )

        def close_prompt():

            mark_seen()
            cleanup_window.destroy()

        def eject_volume():

            mark_seen()

            try:

                subprocess.Popen(
                    [
                        "hdiutil",
                        "detach",
                        str(volume)
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                self.show_toast(
                    "Kurulum disk imajı çıkarılıyor.",
                    "#27AE60"
                )

            except Exception as e:

                logger.exception("Disk imajı çıkarılamadı")

                self.show_toast(
                    "Disk imajı çıkarılamadı.",
                    "#C0392B"
                )

            cleanup_window.destroy()

        cleanup_window.protocol(
            "WM_DELETE_WINDOW",
            close_prompt
        )

        later_button = ctk.CTkButton(
            actions,
            text="Daha Sonra",
            height=40,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=close_prompt
        )

        later_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        eject_button = ctk.CTkButton(
            actions,
            text="Disk İmajını Çıkar",
            height=40,
            fg_color="#2E8B57",
            hover_color="#247348",
            command=eject_volume
        )

        eject_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

    def go_back(self):

        if not self.navigation_history:

            return

        previous_state = self.navigation_history.pop()

        self.restore_view_state(
            previous_state
        )

        self.update_back_button_state()

    def push_navigation_state(self):

        state = self.capture_current_view_state()

        if (
            self.navigation_history and
            self.get_view_state_signature(
                self.navigation_history[-1]
            ) == self.get_view_state_signature(state)
        ):

            return

        self.navigation_history.append(state)

        if len(self.navigation_history) > 25:

            self.navigation_history = self.navigation_history[-25:]

        self.update_back_button_state()

    def get_view_state_signature(self, state):

        def job_identity(job):

            if isinstance(job, dict):

                getter = job.get

            else:

                getter = lambda key, default="": getattr(
                    job,
                    key,
                    default
                )

            return (
                str(getter("url", "") or getter("apply_url", "")),
                str(getter("title", "")),
                str(getter("company", ""))
            )

        return (
            state.get("view_mode"),
            state.get("current_page"),
            tuple(
                job_identity(job)
                for job in state.get("filtered_jobs", [])
            ),
            tuple(
                job_identity(job)
                for job in state.get("all_jobs", [])
            ),
            state.get("last_status_message", ""),
            state.get("search_summary_message", ""),
            state.get("keyword", ""),
            state.get("city", ""),
            tuple(state.get("selected_sources", [])),
            tuple(state.get("selected_application_statuses", [])),
            tuple(state.get("selected_experiences", [])),
            tuple(state.get("selected_remote", [])),
            state.get("sort_type", "Varsayılan")
        )

    def update_back_button_state(self):

        if not hasattr(self, "back_button"):

            return

        has_history = bool(self.navigation_history)

        self.back_button.configure(
            state="normal" if has_history else "disabled",
            fg_color="#3A3A3A" if has_history else "#2A2A2A",
            text_color="#E5E7EB" if has_history else "#777777"
        )

    def capture_current_view_state(self):

        return {
            "view_mode": self.view_mode,
            "filtered_jobs": self.filtered_jobs.copy(),
            "all_jobs": self.all_jobs.copy(),
            "current_page": self.current_page,
            "last_status_message": self.last_status_message,
            "search_summary_message": self.search_summary_message,
            "last_search_report": self.last_search_report.copy(),
            "keyword": self.keyword_entry.get(),
            "city": self.city_entry.get(),
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

    def restore_view_state(self, state):

        self.restore_filter_controls_from_state(state)

        self.view_mode = state.get(
            "view_mode",
            "home"
        )

        self.filtered_jobs = state.get(
            "filtered_jobs",
            []
        )

        self.all_jobs = state.get(
            "all_jobs",
            []
        )

        self.current_page = state.get(
            "current_page",
            1
        )

        self.search_summary_message = state.get(
            "search_summary_message",
            ""
        )

        self.last_search_report = state.get(
            "last_search_report",
            {}
        )

        self.set_status_message(
            state.get(
                "last_status_message",
                "Hazır"
            )
        )

        if self.view_mode == "home":

            self.show_welcome_screen()

            return

        self.prev_button.configure(
            state="normal"
        )

        self.next_button.configure(
            state="normal"
        )

        self.display_jobs(
            scroll_to_top=True
        )

    def restore_filter_controls_from_state(self, state):

        self.keyword_entry.delete(
            0,
            "end"
        )

        self.keyword_entry.insert(
            0,
            state.get(
                "keyword",
                ""
            )
        )

        self.city_entry.delete(
            0,
            "end"
        )

        self.city_entry.insert(
            0,
            state.get(
                "city",
                ""
            )
        )

        selected_sources = set(
            state.get(
                "selected_sources",
                []
            )
        )

        for source, var in self.source_vars.items():

            var.set(
                source in selected_sources
            )

        selected_statuses = state.get(
            "selected_application_statuses",
            []
        )

        if hasattr(
            self,
            "application_status_filter_var"
        ):

            self.application_status_filter_var.set(
                selected_statuses[0]
                if len(selected_statuses) == 1
                else "Tümü"
            )

        selected_experiences = set(
            state.get(
                "selected_experiences",
                []
            )
        )

        for exp, var in self.exp_vars.items():

            var.set(
                exp in selected_experiences
            )

        selected_remote = set(
            state.get(
                "selected_remote",
                []
            )
        )

        for remote, var in self.remote_vars.items():

            var.set(
                remote in selected_remote
            )

        self.sort_var.set(
            state.get(
                "sort_type",
                "Varsayılan"
            )
        )

    def go_home(self):

        if self.view_mode != "home":

            self.push_navigation_state()

        self.show_welcome_screen()

    # =========================
    # WELCOME SCREEN
    # =========================
