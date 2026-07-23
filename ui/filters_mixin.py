from ui.config import APPLICATION_STATUSES
from utils.search_engine import normalize_text


EXPERIENCE_ASC_PRIORITY = {
    "Stajyer": 0, "Junior": 1, "Mid-Level": 2,
    "Senior": 3, "Manager": 4, "Director": 5
}
EXPERIENCE_DESC_PRIORITY = {
    "Director": 0, "Manager": 1, "Senior": 2,
    "Mid-Level": 3, "Junior": 4, "Stajyer": 5
}
REMOTE_PRIORITY = {"Remote": 0, "Hibrit": 1, "Ofis": 2}


class FiltersMixin:

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

        city = (
            ""
            if self.view_mode == "favorites"
            else normalize_text(
                self.city_entry.get()
            )
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
