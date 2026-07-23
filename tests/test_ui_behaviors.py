from models.job import Job
from ui.app import JobApp
from ui.favorites_mixin import FavoritesMixin
from ui.navigation_mixin import NavigationMixin
from ui.search_mixin import SearchMixin


class FakeVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, start, end):
        self.value = ""

    def insert(self, index, value):
        self.value = value


class FakeButton:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)


def make_job(
    url,
    title,
    location="İstanbul",
    experience="Mid-Level",
    remote="Ofis",
):
    return Job(
        site="Kariyer",
        company="Örnek Şirket",
        title=title,
        description="",
        url=url,
        apply_url=url,
        location=location,
        experience=experience,
        remote=remote,
    )


def make_state(keyword, job):
    return {
        "view_mode": "results",
        "current_page": 1,
        "filtered_jobs": [job],
        "all_jobs": [job],
        "last_status_message": "1 ilan bulundu.",
        "search_summary_message": "1 ilan bulundu.",
        "keyword": keyword,
        "city": "İstanbul",
        "selected_sources": ["kariyer"],
        "selected_application_statuses": [],
        "selected_experiences": [],
        "selected_remote": [],
        "sort_type": "Varsayılan",
    }


def test_navigation_keeps_distinct_searches_with_equal_result_counts():
    navigator = NavigationMixin()
    navigator.navigation_history = []
    navigator.back_button = FakeButton()
    first_job = make_job("https://example.test/1", "Yazılım Uzmanı")
    second_job = make_job("https://example.test/2", "Pazarlama Uzmanı")
    states = iter(
        [
            make_state("Yazılım", first_job),
            make_state("Pazarlama", second_job),
        ]
    )
    navigator.capture_current_view_state = lambda: next(states)

    navigator.push_navigation_state()
    navigator.push_navigation_state()

    assert [
        state["keyword"] for state in navigator.navigation_history
    ] == ["Yazılım", "Pazarlama"]
    assert navigator.back_button.config["state"] == "normal"


def test_back_button_walks_through_every_history_entry():
    navigator = NavigationMixin()
    home = {"view_mode": "home"}
    results = {"view_mode": "results", "keyword": "Yazılım"}
    favorites = {"view_mode": "favorites"}
    navigator.navigation_history = [home, results, favorites]
    navigator.back_button = FakeButton()
    restored = []
    navigator.restore_view_state = restored.append

    navigator.go_back()
    navigator.go_back()
    navigator.go_back()

    assert restored == [favorites, results, home]
    assert navigator.navigation_history == []
    assert navigator.back_button.config["state"] == "disabled"


def test_restoring_empty_sources_unchecks_all_source_controls():
    navigator = NavigationMixin()
    navigator.keyword_entry = FakeEntry("eski")
    navigator.city_entry = FakeEntry("eski")
    navigator.source_vars = {
        "kariyer": FakeVar(True),
        "jooble": FakeVar(True),
    }
    navigator.exp_vars = {"Junior": FakeVar(True)}
    navigator.remote_vars = {"Remote": FakeVar(True)}
    navigator.application_status_filter_var = FakeVar("Görüşme")
    navigator.sort_var = FakeVar("En Yeni Önce")

    navigator.restore_filter_controls_from_state(
        {
            "keyword": "",
            "city": "",
            "selected_sources": [],
            "selected_application_statuses": [],
            "selected_experiences": [],
            "selected_remote": [],
            "sort_type": "Varsayılan",
        }
    )

    assert all(not var.get() for var in navigator.source_vars.values())
    assert navigator.application_status_filter_var.get() == "Tümü"
    assert navigator.sort_var.get() == "Varsayılan"


def test_restoring_result_state_keeps_page_and_scrolls_to_top():
    navigator = NavigationMixin()
    navigator.keyword_entry = FakeEntry()
    navigator.city_entry = FakeEntry()
    navigator.source_vars = {"kariyer": FakeVar(False)}
    navigator.exp_vars = {"Junior": FakeVar(False)}
    navigator.remote_vars = {"Remote": FakeVar(False)}
    navigator.application_status_filter_var = FakeVar("Tümü")
    navigator.sort_var = FakeVar("Varsayılan")
    navigator.prev_button = FakeButton()
    navigator.next_button = FakeButton()
    navigator.set_status_message = lambda message: setattr(
        navigator,
        "last_status_message",
        message,
    )
    display_calls = []
    navigator.display_jobs = lambda scroll_to_top=False: display_calls.append(
        scroll_to_top
    )
    job = make_job("https://example.test/1", "Yazılım Uzmanı")
    state = make_state("Yazılım", job)
    state["current_page"] = 3
    state["last_search_report"] = {"counts": {"kariyer": 1}}

    navigator.restore_view_state(state)

    assert navigator.view_mode == "results"
    assert navigator.current_page == 3
    assert navigator.keyword_entry.get() == "Yazılım"
    assert navigator.source_vars["kariyer"].get() is True
    assert display_calls == [True]


class FilterHarness(FavoritesMixin):
    reset_favorite_filters = JobApp.reset_favorite_filters
    apply_filters = JobApp.apply_filters

    def __init__(self):
        self.view_mode = "results"
        self.navigation_history = []
        self.keyword_entry = FakeEntry()
        self.city_entry = FakeEntry()
        self.source_vars = {
            "kariyer": FakeVar(True),
            "jooble": FakeVar(True),
        }
        self.exp_vars = {
            "Junior": FakeVar(False),
            "Senior": FakeVar(False),
        }
        self.remote_vars = {
            "Remote": FakeVar(False),
            "Ofis": FakeVar(False),
        }
        self.application_status_filter_var = FakeVar("Tümü")
        self.sort_var = FakeVar("Varsayılan")
        self.all_jobs = []
        self.filtered_jobs = []
        self.favorite_jobs = []
        self.favorite_jobs_by_url = {}
        self.hidden_job_urls = set()
        self.last_search_report = {}
        self.search_summary_message = ""
        self.current_page = 4
        self.display_calls = []
        self.status_messages = []

    def push_navigation_state(self):
        self.navigation_history.append(self.view_mode)

    def save_search_preferences(self):
        return None

    def get_selected_application_statuses(self):
        status = self.application_status_filter_var.get()
        return [] if status == "Tümü" else [status]

    def get_selected_sources(self):
        return [
            source for source, var in self.source_vars.items() if var.get()
        ]

    def is_hidden_job(self, job):
        return job.url in self.hidden_job_urls

    def build_search_summary(self, jobs, selected_sources, report):
        return f"{len(jobs)} ilan bulundu."

    def set_status_message(self, message):
        self.status_messages.append(message)

    def display_jobs(self, scroll_to_top=False):
        self.display_calls.append(scroll_to_top)


def test_opening_favorites_resets_filters_and_shows_every_favorite():
    app = FilterHarness()
    app.keyword_entry.value = "eşleşmeyen arama"
    app.city_entry.value = "Ankara"
    app.exp_vars["Senior"].set(True)
    app.remote_vars["Remote"].set(True)
    app.application_status_filter_var.set("Görüşme")
    app.sort_var.set("En Yeni Önce")
    app.favorite_jobs = [
        {
            "url": "https://example.test/favorite/1",
            "title": "Yazılım Uzmanı",
            "company": "Örnek",
            "location": "İstanbul",
            "experience": "Junior",
            "remote": "Ofis",
            "application_status": "Kaydedildi",
            "saved_at": "2026-07-20T10:00:00",
        },
        {
            "url": "https://example.test/favorite/2",
            "title": "Pazarlama Uzmanı",
            "company": "Örnek",
            "location": "İzmir",
            "experience": "Senior",
            "remote": "Remote",
            "application_status": "Görüşme",
            "saved_at": "2026-07-20T11:00:00",
        },
    ]

    app.show_favorites()

    assert app.navigation_history == ["results"]
    assert app.view_mode == "favorites"
    assert app.keyword_entry.get() == ""
    assert app.city_entry.get() == "Ankara"
    assert app.application_status_filter_var.get() == "Tümü"
    assert len(app.filtered_jobs) == 2
    assert app.current_page == 1
    assert app.display_calls == [True]


def test_combined_filters_hide_irrelevant_and_hidden_results():
    app = FilterHarness()
    matching = make_job(
        "https://example.test/1",
        "Junior Yazılım Geliştirici",
        location="İstanbul",
        experience="Junior",
        remote="Remote",
    )
    wrong_city = make_job(
        "https://example.test/2",
        "Junior Yazılım Geliştirici",
        location="Ankara",
        experience="Junior",
        remote="Remote",
    )
    hidden = make_job(
        "https://example.test/3",
        "Junior Yazılım Geliştirici",
        location="İstanbul",
        experience="Junior",
        remote="Remote",
    )
    app.all_jobs = [matching, wrong_city, hidden]
    app.hidden_job_urls = {hidden.url}
    app.city_entry.value = "İstanbul"
    app.exp_vars["Junior"].set(True)
    app.remote_vars["Remote"].set(True)

    app.apply_filters()

    assert app.filtered_jobs == [matching]
    assert app.current_page == 1
    assert app.display_calls == [True]


def test_auto_filter_only_runs_on_results_and_favorites_views():
    class AutoFilterHarness:
        def __init__(self):
            self.view_mode = "home"
            self.saved = 0
            self.applied = 0

        def save_search_preferences(self):
            self.saved += 1

        def apply_filters(self):
            self.applied += 1

    app = AutoFilterHarness()

    JobApp.auto_apply_filters(app)
    app.view_mode = "results"
    JobApp.auto_apply_filters(app)
    app.view_mode = "favorites"
    JobApp.auto_apply_filters(app)

    assert app.saved == 2
    assert app.applied == 2


def test_application_status_filter_is_only_active_in_favorites():
    app = SearchMixin()
    app.application_status_filter_var = FakeVar("Görüşme")

    app.view_mode = "results"
    assert app.get_selected_application_statuses() == []

    app.view_mode = "favorites"
    assert app.get_selected_application_statuses() == ["Görüşme"]


def test_all_favorite_statuses_disable_application_status_filter():
    app = SearchMixin()
    app.view_mode = "favorites"
    app.application_status_filter_var = FakeVar("Tümü")

    assert app.get_selected_application_statuses() == []


class PaginationHarness:
    def __init__(self):
        self.filtered_jobs = list(range(25))
        self.jobs_per_page = 10
        self.current_page = 1
        self.history_pages = []
        self.display_calls = []

    def push_navigation_state(self):
        self.history_pages.append(self.current_page)

    def display_jobs(self, scroll_to_top=False):
        self.display_calls.append(scroll_to_top)


def test_pagination_records_history_and_scrolls_each_page_to_top():
    app = PaginationHarness()

    JobApp.next_page(app)
    JobApp.next_page(app)
    JobApp.next_page(app)
    JobApp.prev_page(app)

    assert app.current_page == 2
    assert app.history_pages == [1, 2, 3]
    assert app.display_calls == [True, True, True]
