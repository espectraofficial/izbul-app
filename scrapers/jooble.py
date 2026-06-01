import html
import os
import re
from pathlib import Path

import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
)


API_URL = "https://jooble.org/api/{api_key}"


def get_jooble_api_key():

    api_key = os.getenv("JOOBLE_API_KEY", "").strip()

    if api_key:

        return api_key

    key_files = [
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


def search_jooble(
    keyword,
    location="Türkiye",
    page=1,
    results_on_page=20
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
            API_URL.format(api_key=api_key),
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:

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
                    posted_date=item.get("updated", ""),
                    job_date_text=item.get("updated", "")
                )
            )

        except Exception as e:

            print("Jooble parse hata:", e)

            continue

    return jobs