from datetime import datetime, timedelta, timezone
from pathlib import Path

from models.job import Job
from ui.storage import (
    get_backup_file,
    get_app_data_dir,
    load_json_with_backup,
    write_json_atomic,
)
from utils.search_engine import normalize_text


CACHE_SCHEMA_VERSION = 1
CACHE_FILE_NAME = "search_cache.json"
CACHE_MAX_ENTRIES = 8
CACHE_MAX_AGE = timedelta(hours=24)
JOB_FIELDS = (
    "site",
    "company",
    "title",
    "description",
    "url",
    "apply_url",
    "posted_date",
    "job_date_text",
    "remote",
    "experience",
    "location",
    "logo_url",
)


def get_search_cache_file(app_data_dir=None):
    base_dir = Path(app_data_dir) if app_data_dir else get_app_data_dir()
    return base_dir / CACHE_FILE_NAME


def clear_search_cache(app_data_dir=None):
    cache_file = get_search_cache_file(app_data_dir)
    backup_file = get_backup_file(cache_file)
    removed = cache_file.exists() or backup_file.exists()
    cache_file.unlink(missing_ok=True)
    backup_file.unlink(missing_ok=True)
    return removed


def build_search_cache_key(keyword, city, sources):
    normalized_sources = sorted(
        {
            normalize_text(source)
            for source in sources or []
            if str(source or "").strip()
        }
    )
    return "|".join(
        [
            normalize_text(keyword),
            normalize_text(city),
            ",".join(normalized_sources),
        ]
    )


def serialize_job(job):
    return {
        field: str(getattr(job, field, "") or "")
        for field in JOB_FIELDS
    }


def deserialize_job(data):
    if not isinstance(data, dict):
        raise ValueError("Önbellekteki ilan verisi geçersiz.")

    return Job(
        **{
            field: str(data.get(field, "") or "")
            for field in JOB_FIELDS
        }
    )


def _load_cache_data(cache_file):
    data = load_json_with_backup(
        cache_file,
        {"schema_version": CACHE_SCHEMA_VERSION, "entries": []},
        expected_type=dict,
    )

    if data.get("schema_version") != CACHE_SCHEMA_VERSION:
        return {"schema_version": CACHE_SCHEMA_VERSION, "entries": []}

    if not isinstance(data.get("entries"), list):
        data["entries"] = []

    return data


def save_cached_search(
    keyword,
    city,
    sources,
    jobs,
    search_report=None,
    app_data_dir=None,
    now=None,
):
    if not jobs:
        return False

    cache_file = get_search_cache_file(app_data_dir)
    cache_data = _load_cache_data(cache_file)
    cache_key = build_search_cache_key(keyword, city, sources)
    saved_at = (now or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )
    entries = [
        entry
        for entry in cache_data["entries"]
        if isinstance(entry, dict) and entry.get("key") != cache_key
    ]
    entries.insert(
        0,
        {
            "key": cache_key,
            "saved_at": saved_at.isoformat(timespec="seconds"),
            "keyword": str(keyword or "").strip(),
            "city": str(city or "").strip(),
            "sources": sorted(set(sources or [])),
            "jobs": [serialize_job(job) for job in jobs],
            "search_report": (
                search_report if isinstance(search_report, dict) else {}
            ),
        },
    )
    cache_data["entries"] = entries[:CACHE_MAX_ENTRIES]
    write_json_atomic(cache_file, cache_data)
    return True


def load_cached_search(
    keyword,
    city,
    sources,
    app_data_dir=None,
    now=None,
    max_age=CACHE_MAX_AGE,
):
    cache_file = get_search_cache_file(app_data_dir)

    cache_data = _load_cache_data(cache_file)
    cache_key = build_search_cache_key(keyword, city, sources)
    current_time = now or datetime.now(timezone.utc)

    for entry in cache_data["entries"]:
        if not isinstance(entry, dict) or entry.get("key") != cache_key:
            continue

        try:
            saved_at = datetime.fromisoformat(str(entry.get("saved_at", "")))
            if saved_at.tzinfo is None:
                saved_at = saved_at.replace(tzinfo=timezone.utc)

            if current_time.astimezone(timezone.utc) - saved_at > max_age:
                return None

            jobs = [
                deserialize_job(job_data)
                for job_data in entry.get("jobs", [])
            ]
        except (TypeError, ValueError):
            return None

        if not jobs:
            return None

        return {
            "saved_at": saved_at,
            "jobs": jobs,
            "search_report": (
                entry.get("search_report", {})
                if isinstance(entry.get("search_report"), dict)
                else {}
            ),
        }

    return None
