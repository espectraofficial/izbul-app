import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
)


DEFAULT_API_HOST = "tr.jooble.org"
APP_NAME = "İzbul"
LEGACY_APP_NAME = "Job Finder"


def get_app_data_dir(app_name=APP_NAME):

    if os.sys.platform == "darwin":

        return (
            Path.home()
            / "Library"
            / "Application Support"
            / app_name
        )

    if os.sys.platform.startswith("win"):

        appdata = os.getenv("APPDATA")

        if appdata:

            return Path(appdata) / app_name

    return (
        Path.home()
        / ".config"
        / app_name
    )


def get_user_api_key_file():

    current_file = get_app_data_dir(APP_NAME) / "jooble_api_key.txt"
    legacy_file = get_app_data_dir(LEGACY_APP_NAME) / "jooble_api_key.txt"

    if legacy_file.exists() and not current_file.exists():

        current_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        try:

            current_file.write_bytes(
                legacy_file.read_bytes()
            )

        except Exception as e:

            print("Eski Jooble API anahtarı taşınamadı:", e)

    return current_file


def get_jooble_api_key():

    api_key = os.getenv("JOOBLE_API_KEY", "").strip()

    if api_key:

        return api_key

    key_files = [
        get_user_api_key_file(),
        Path.cwd() / "jooble_api_key.txt",
        Path(__file__).resolve().parent.parent / "jooble_api_key.txt"
    ]

    for key_file in key_files:

        if not key_file.exists():

            continue

        try:

            api_key = key_file.read_text(
                encoding="utf-8"
            ).strip()

            if api_key:

                return api_key

        except Exception as e:

            print("Jooble API anahtarı okunamadı:", e)

    return ""


def save_jooble_api_key(api_key):

    key_file = get_user_api_key_file()

    key_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    key_file.write_text(
        str(api_key or "").strip(),
        encoding="utf-8"
    )


def get_jooble_api_url(api_key):

    api_host = os.getenv(
        "JOOBLE_API_HOST",
        DEFAULT_API_HOST
    ).strip()

    api_host = api_host.removeprefix(
        "https://"
    ).removeprefix(
        "http://"
    ).strip("/")

    return f"https://{api_host}/api/{api_key}"


def clean_snippet(value):

    text = re.sub(
        r"<[^>]+>",
        " ",
        str(value or "")
    )

    text = html.unescape(text)

    return " ".join(
        text.split()
    )


def parse_jooble_date(value):

    raw_value = str(value or "").strip()

    if not raw_value:

        return "", ""

    normalized = raw_value.replace(
        "Z",
        "+00:00"
    )

    try:

        date_value = datetime.fromisoformat(
            normalized
        )

        if date_value.tzinfo is None:

            date_value = date_value.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(
            date_value.tzinfo
        )

        days_ago = (
            now.date() - date_value.date()
        ).days

        if days_ago == 0:

            date_text = "Bugün"

        elif days_ago == 1:

            date_text = "Dün"

        elif days_ago > 1:

            date_text = f"{days_ago} gün önce"

        else:

            date_text = date_value.strftime(
                "%d.%m.%Y"
            )

        return (
            date_value.date().isoformat(),
            date_text
        )

    except ValueError:

        return raw_value, raw_value


def search_jooble(
    keyword,
    location="Türkiye",
    page=1,
    results_on_page=20,
    raise_errors=False
):

    api_key = get_jooble_api_key()

    if not api_key:

        print("Jooble atlandı: API anahtarı yok.")

        return []

    payload = {
        "keywords": keyword,
        "location": location or "Türkiye",
        "page": str(page),
        "ResultOnPage": str(results_on_page)
    }

    try:

        response = requests.post(
            get_jooble_api_url(api_key),
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "JobFinderApp/1.0"
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:

        if raise_errors:

            raise

        print("Jooble request hata:", e)

        return []

    jobs = []

    for item in data.get("jobs", []):

        try:

            title = item.get("title", "")

            description = clean_snippet(
                item.get("snippet", "")
            )

            work_type = item.get("type", "")

            remote = parse_remote(
                work_model=work_type,
                title=title,
                description=description
            )

            experience = parse_experience(
                title=title,
                description=description
            )

            link = item.get("link", "")

            posted_date, job_date_text = parse_jooble_date(
                item.get("updated", "")
            )

            jobs.append(
                Job(
                    site="Jooble",
                    company=item.get("company", ""),
                    title=title,
                    description=description,
                    url=link,
                    apply_url=link,
                    remote=remote,
                    experience=experience,
                    location=item.get("location", ""),
                    posted_date=posted_date,
                    job_date_text=job_date_text,
                    logo_url=(
                        item.get("logo") or
                        item.get("logo_url") or
                        item.get("companyLogo") or
                        ""
                    )
                )
            )

        except Exception as e:

            print("Jooble parse hata:", e)

            continue

    return jobs
