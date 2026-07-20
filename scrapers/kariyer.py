import html
import logging
import re

import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
)


logger = logging.getLogger(__name__)


def clean_detail_text(value):

    text = re.sub(
        r"<(br|p|li|div|h[1-6])[^>]*>",
        "\n",
        str(value or ""),
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = html.unescape(text)

    lines = [
        " ".join(line.split())
        for line in text.splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    ).strip()


def extract_detail_description(page_html):

    marker_patterns = [
        r"GENEL\s+NİTELİKLER\s+VE\s+İŞ\s+TANIMI",
        r"İş\s+İlanı\s+Hakkında"
    ]

    end_patterns = [
        r"Aday\s+Kriterleri",
        r"Şirket\s+Hakkında",
        r"Hakkımızda",
        r"Yan\s+Haklar",
        r"İlgini\s+Çekebilecek",
        r"Benzer\s+İlan"
    ]

    clean_page_text = clean_detail_text(
        page_html
    )

    start_index = -1

    for pattern in marker_patterns:

        match = re.search(
            pattern,
            clean_page_text,
            flags=re.IGNORECASE
        )

        if match:

            start_index = match.end()

            break

    if start_index == -1:

        return ""

    detail_text = clean_page_text[start_index:].strip()

    end_indexes = []

    for pattern in end_patterns:

        match = re.search(
            pattern,
            detail_text,
            flags=re.IGNORECASE
        )

        if match:

            end_indexes.append(
                match.start()
            )

    if end_indexes:

        detail_text = detail_text[:min(end_indexes)]

    return detail_text.strip()


def fetch_kariyer_detail_description(job_url):

    if not job_url:

        return ""

    response = requests.get(
        job_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        },
        timeout=12
    )

    response.raise_for_status()

    return extract_detail_description(
        response.text
    )


def get_logo_url(item):

    logo_url = (
        item.get("squareLogoUrl") or
        item.get("logoUrl") or
        item.get("fullPathLogoUrl") or
        ""
    )

    if "firma-logosuz" in logo_url:

        return ""

    if logo_url and not logo_url.startswith("http"):

        return "https://www.kariyer.net" + logo_url

    return logo_url


def search_kariyer(
    keyword,
    city="34",
    raise_errors=False,
    max_pages=2
):

    jobs = []

    url = (
        "https://candidatesearchapigateway.kariyer.net/search"
    )

    headers = {

        "Content-Type": "application/json;charset=UTF-8",

        "User-Agent": "Mozilla/5.0",

        "Accept": "application/json",

        "Origin": "https://www.kariyer.net",

        "Referer": "https://www.kariyer.net/"
    }

    page = 1

    seen = set()

    while page <= max_pages:

        payload = {

            "memberId": 0,

            "currentPage": page,

            "size": 50,

            "calculateHiddenJobCount": True,

            "keywordPosition": keyword,

            "location": {
                "cities": [city]
            }
        }

        try:

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:

            if raise_errors:

                raise

            logger.exception("Kariyer.net isteği başarısız")

            break

        items = data.get(
            "data",
            {}
        ).get(
            "jobs",
            {}
        ).get(
            "items",
            []
        )

        if not items:
            break

        new_count = 0

        for item in items:

            try:

                link = item.get(
                    "jobUrl",
                    ""
                )

                if (
                    link and
                    not link.startswith("http")
                ):

                    link = (
                        "https://www.kariyer.net"
                        + link
                    )

                if link in seen:
                    continue

                seen.add(link)

                new_count += 1

                # 🔥 REMOTE
                work_model = item.get(
                    "workModel",
                    ""
                )

                remote = parse_remote(
                    work_model
                )

                # 🔥 EXPERIENCE
                experience = parse_experience(

                    title=item.get(
                        "title",
                        ""
                    ),

                    description="",

                    position_level=item.get(
                        "positionLevel"
                    )
                )

                # 🔥 LOCATION
                location = item.get(
                    "allLocations",
                    "Belirtilmemiş"
                )

                jobs.append(

                    Job(

                        site="Kariyer",

                        company=item.get(
                            "companyName",
                            ""
                        ),

                        title=item.get(
                            "title",
                            ""
                        ),

                        description="",

                        url=link,

                        apply_url=link,

                        remote=remote,

                        experience=experience,

                        location=location,

                        posted_date=item.get(
                            "postingDate",
                            ""
                        ),

                        job_date_text=item.get(
                            "jobDateText",
                            ""
                        ),

                        logo_url=get_logo_url(
                            item
                        )
                    )
                )

            except Exception as e:

                logger.exception("Kariyer.net ilanı ayrıştırılamadı")

                continue

        if new_count == 0:
            break

        page += 1

    return jobs
