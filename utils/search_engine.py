from scrapers.kariyer import search_kariyer
from scrapers.jooble import (
    get_jooble_api_key,
    search_jooble
)
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
                normalize_text(
                    getattr(
                        job,
                        "title",
                        ""
                    )
                ),
                normalize_text(
                    getattr(
                        job,
                        "company",
                        ""
                    )
                ),
                normalize_text(
                    getattr(
                        job,
                        "location",
                        ""
                    )
                )
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


def get_http_status(error):

    response = getattr(
        error,
        "response",
        None
    )

    if response is None:

        return None

    return getattr(
        response,
        "status_code",
        None
    )


def smart_search(
    keyword,
    selected_city=None,
    sources=None,
    status_callback=None
):

    all_jobs = []

    selected_sources = set(
        ["kariyer", "jooble"]
        if sources is None
        else sources
    )

    def emit_status(message):

        if status_callback:

            status_callback(message)

    keywords = expand_keywords(keyword)

    locations = expand_locations(
        selected_city
    )

    jooble_location = get_search_location(
        selected_city
    )

    if not selected_sources:

        emit_status("En az bir kaynak seçin.")

        return []

    # 🔥 KARIYER.NET
    if "kariyer" in selected_sources:

        for kw in keywords:

            for loc in locations:

                try:

                    emit_status("Kariyer.net aranıyor...")

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

                    emit_status("Kariyer.net geçici olarak yanıt vermedi.")

                    print(
                        "Kariyer hata:",
                        e
                    )

    # JOOBLE
    if "jooble" in selected_sources:

        if not get_jooble_api_key():

            emit_status("Jooble API anahtarı yok; Jooble atlandı.")

        else:

            for kw in keywords:

                try:

                    emit_status("Jooble aranıyor...")

                    jooble_jobs = search_jooble(
                        kw,
                        location=jooble_location,
                        raise_errors=True
                    )

                    print(
                        f"Jooble bulundu: {len(jooble_jobs)}"
                    )

                    all_jobs.extend(
                        jooble_jobs
                    )

                except Exception as e:

                    status_code = get_http_status(e)

                    if status_code == 403:

                        emit_status(
                            "Jooble API anahtarı geçersiz veya henüz aktif değil."
                        )

                    else:

                        emit_status(
                            "Jooble geçici olarak yanıt vermedi."
                        )

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

    emit_status(
        f"{len(unique_jobs)} ilan bulundu."
    )

    return unique_jobs
