from scrapers.kariyer import search_kariyer
from scrapers.jooble import search_jooble
import unicodedata


CITY_MAP = {
    "istanbul": "34",
    "ankara": "06",
    "izmir": "35"
}


def normalize_text(value):

    text = str(value or "").strip().lower()

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )


def deduplicate_jobs(jobs):

    unique = []

    seen = set()

    for job in jobs:

        try:

            key = (
                job.title.strip().lower(),
                job.company.strip().lower()
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(job)

        except:
            continue

    return unique


def expand_keywords(keyword):

    keyword = keyword.lower()

    base = [keyword]

    if " " in keyword:
        base.extend(keyword.split())

    synonyms = {

        "insan kaynakları": [
            "human resources",
            "hr",
            "recruitment"
        ],

        "mimar": [
            "architect"
        ],

        "yazılım": [
            "software",
            "developer",
            "engineer"
        ]
    }

    for key, values in synonyms.items():

        if key == keyword:

            base.extend(values)

    return list(set(base))


def expand_locations(selected_city=None):

    normalized_city = normalize_text(
        selected_city
    )

    if normalized_city:

        for city, code in CITY_MAP.items():

            if (
                normalized_city == city or
                city in normalized_city
            ):

                return [code]

    return list(CITY_MAP.values())


def get_search_location(selected_city=None):

    selected_city = str(
        selected_city or ""
    ).strip()

    if selected_city:

        return selected_city

    return "Türkiye"


def smart_search(keyword, selected_city=None):

    all_jobs = []

    keywords = expand_keywords(keyword)

    locations = expand_locations(
        selected_city
    )

    jooble_location = get_search_location(
        selected_city
    )

    # 🔥 KARIYER.NET
    for kw in keywords:

        for loc in locations:

            try:

                kariyer_jobs = search_kariyer(
                    kw,
                    city=loc
                )

                print(
                    f"Kariyer bulundu: {len(kariyer_jobs)}"
                )

                all_jobs.extend(
                    kariyer_jobs
                )

            except Exception as e:

                print(
                    "Kariyer hata:",
                    e
                )

    # JOOBLE
    for kw in keywords:

        try:

            jooble_jobs = search_jooble(
                kw,
                location=jooble_location
            )

            print(
                f"Jooble bulundu: {len(jooble_jobs)}"
            )

            all_jobs.extend(
                jooble_jobs
            )

        except Exception as e:

            print(
                "Jooble hata:",
                e
            )

    # 🔥 DUPLICATE REMOVE
    unique_jobs = deduplicate_jobs(
        all_jobs
    )

    print(
        f"Toplam unique ilan: {len(unique_jobs)}"
    )

    return unique_jobs
