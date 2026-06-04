import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
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

            print(
                "Kariyer request hata:",
                e
            )

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

                print(
                    "Kariyer parse hata:",
                    e
                )

                continue

        if new_count == 0:
            break

        page += 1

    return jobs
