from datetime import datetime, timedelta, timezone

from models.job import Job
from ui import search_mixin
from ui.search_cache import (
    CACHE_MAX_ENTRIES,
    build_search_cache_key,
    clear_search_cache,
    get_search_cache_file,
    load_cached_search,
    save_cached_search,
)
from ui.search_mixin import SearchMixin


NOW = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)


def make_job(index=1):
    return Job(
        site="Kariyer",
        company="Örnek Şirket",
        title=f"Yazılım Uzmanı {index}",
        description="Python geliştirme",
        url=f"https://example.test/jobs/{index}",
        apply_url=f"https://example.test/jobs/{index}",
        posted_date="2026-07-20",
        job_date_text="Bugün",
        remote="Hibrit",
        experience="Mid-Level",
        location="İstanbul",
        logo_url="https://example.test/logo.png",
    )


def test_cache_key_normalizes_query_and_source_order():
    first = build_search_cache_key(
        " İnsan Kaynakları ",
        "İSTANBUL",
        ["jooble", "kariyer"],
    )
    second = build_search_cache_key(
        "insan kaynaklari",
        "istanbul",
        ["kariyer", "jooble"],
    )

    assert first == second


def test_cached_search_roundtrip_preserves_job_and_report(tmp_path):
    job = make_job()
    report = {"source_counts": {"kariyer": 1}, "source_errors": {}}

    saved = save_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer", "jooble"],
        [job],
        search_report=report,
        app_data_dir=tmp_path,
        now=NOW,
    )
    cached = load_cached_search(
        "yazilim",
        "istanbul",
        ["jooble", "kariyer"],
        app_data_dir=tmp_path,
        now=NOW + timedelta(hours=1),
    )

    assert saved is True
    assert cached["search_report"] == report
    assert cached["jobs"][0].title == job.title
    assert cached["jobs"][0].remote == "Hibrit"
    assert cached["jobs"][0].logo_url == job.logo_url


def test_expired_cache_is_not_returned(tmp_path):
    save_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer"],
        [make_job()],
        app_data_dir=tmp_path,
        now=NOW,
    )

    assert load_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer"],
        app_data_dir=tmp_path,
        now=NOW + timedelta(hours=25),
    ) is None


def test_cache_keeps_only_most_recent_queries(tmp_path):
    for index in range(CACHE_MAX_ENTRIES + 2):
        save_cached_search(
            f"Arama {index}",
            "İstanbul",
            ["kariyer"],
            [make_job(index)],
            app_data_dir=tmp_path,
            now=NOW + timedelta(minutes=index),
        )

    oldest = load_cached_search(
        "Arama 0",
        "İstanbul",
        ["kariyer"],
        app_data_dir=tmp_path,
        now=NOW + timedelta(minutes=20),
    )
    newest = load_cached_search(
        f"Arama {CACHE_MAX_ENTRIES + 1}",
        "İstanbul",
        ["kariyer"],
        app_data_dir=tmp_path,
        now=NOW + timedelta(minutes=20),
    )

    assert oldest is None
    assert newest is not None


def test_missing_cache_primary_is_recovered_from_backup(tmp_path):
    save_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer"],
        [make_job()],
        app_data_dir=tmp_path,
        now=NOW,
    )
    get_search_cache_file(tmp_path).unlink()

    cached = load_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer"],
        app_data_dir=tmp_path,
        now=NOW,
    )

    assert cached is not None
    assert cached["jobs"][0].title == "Yazılım Uzmanı 1"


def test_clear_cache_removes_primary_and_backup(tmp_path):
    save_cached_search(
        "Yazılım",
        "İstanbul",
        ["kariyer"],
        [make_job()],
        app_data_dir=tmp_path,
        now=NOW,
    )

    assert clear_search_cache(tmp_path) is True
    assert not get_search_cache_file(tmp_path).exists()
    assert not get_search_cache_file(tmp_path).with_suffix(
        ".json.bak"
    ).exists()
    assert clear_search_cache(tmp_path) is False


def test_search_preview_marks_results_as_cached(monkeypatch):
    cached = {
        "jobs": [make_job()],
        "search_report": {"source_counts": {"kariyer": 1}},
    }
    monkeypatch.setattr(
        search_mixin,
        "load_cached_search",
        lambda *args, **kwargs: cached,
    )

    class PreviewHarness:
        def apply_filters(self):
            self.filters_applied = True

    app = PreviewHarness()

    shown = SearchMixin.show_cached_search_preview(
        app,
        "Yazılım",
        "İstanbul",
        ["kariyer"],
    )

    assert shown is True
    assert app.cache_preview_active is True
    assert app.cache_refresh_failed is False
    assert app.all_jobs == cached["jobs"]
    assert app.current_page == 1
    assert app.filters_applied is True


class SearchJobsHarness(SearchMixin):
    def __init__(self, cached_search=None):
        self.search_token = 7
        self.active_cached_search = cached_search
        self.cache_preview_active = bool(cached_search)
        self.cache_refresh_failed = False
        self.completed_token = None

    def thread_safe_status(self, message, search_token=None):
        return None

    def thread_safe_source_progress(self, progress, search_token):
        return None

    def after(self, delay, callback):
        callback()

    def after_search_complete(self, search_token=None):
        self.completed_token = search_token


def test_failed_refresh_keeps_cached_results(monkeypatch):
    cached_job = make_job()
    cached = {
        "jobs": [cached_job],
        "search_report": {"source_counts": {"kariyer": 1}},
    }

    def fake_search(*args, report_callback, **kwargs):
        report_callback(
            {
                "source_counts": {"kariyer": 0},
                "source_errors": {"kariyer": "Kaynak yanıt vermedi."},
            }
        )
        return []

    monkeypatch.setattr(search_mixin, "smart_search", fake_search)
    app = SearchJobsHarness(cached)

    app.search_jobs("Yazılım", "İstanbul", ["kariyer"], 7)

    assert app.all_jobs == [cached_job]
    assert app.cache_preview_active is True
    assert app.cache_refresh_failed is True
    assert "önbellekteki sonuçlar" in app.search_summary_message
    assert app.completed_token == 7


def test_successful_refresh_replaces_and_saves_cache(monkeypatch):
    fresh_job = make_job(2)
    saved = []

    def fake_search(*args, report_callback, **kwargs):
        report_callback(
            {
                "source_counts": {"kariyer": 1},
                "source_errors": {},
            }
        )
        return [fresh_job]

    monkeypatch.setattr(search_mixin, "smart_search", fake_search)
    monkeypatch.setattr(
        search_mixin,
        "save_cached_search",
        lambda *args, **kwargs: saved.append((args, kwargs)),
    )
    app = SearchJobsHarness()

    app.search_jobs("Yazılım", "İstanbul", ["kariyer"], 7)

    assert app.all_jobs == [fresh_job]
    assert app.cache_preview_active is False
    assert len(saved) == 1
    assert saved[0][0][3] == [fresh_job]


def test_cache_write_failure_does_not_discard_live_results(monkeypatch):
    fresh_job = make_job(3)

    def fake_search(*args, report_callback, **kwargs):
        report_callback({"source_counts": {"kariyer": 1}})
        return [fresh_job]

    monkeypatch.setattr(search_mixin, "smart_search", fake_search)
    monkeypatch.setattr(
        search_mixin,
        "save_cached_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk dolu")),
    )
    app = SearchJobsHarness()

    app.search_jobs("Yazılım", "İstanbul", ["kariyer"], 7)

    assert app.all_jobs == [fresh_job]
    assert app.completed_token == 7
