import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
)


def search_kariyer(keyword, city="34"):

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

    while True:

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

            data = response.json()

        except Exception as e:

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

                print("\n-------------------")

                print(
                    "TITLE:",
                    item.get("title")
                )

                print(
                    "POSITION LEVEL:",
                    item.get("positionLevel")
                )

                print(
                    "WORK MODEL:",
                    item.get("workModel")
                )

                print(
                    "JOB DATE TEXT:",
                    item.get("jobDateText")
                )

                print(
                    "POSTING DATE:",
                    item.get("postingDate")
                )

                print(
                    "JOB DATE STATUS:",
                    item.get("jobDateStatus")
                )

                print("-------------------\n")

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