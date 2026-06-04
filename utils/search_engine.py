from scrapers.kariyer import search_kariyer
from scrapers.jooble import (
    get_jooble_api_key,
    search_jooble
)
import unicodedata


CITY_MAP = {
    "istanbul": "34",
    "ankara": "06",
    "izmir": "35",
    "adana": "01",
    "adiyaman": "02",
    "afyonkarahisar": "03",
    "agri": "04",
    "amasya": "05",
    "antalya": "07",
    "artvin": "08",
    "aydin": "09",
    "balikesir": "10",
    "bilecik": "11",
    "bingol": "12",
    "bitlis": "13",
    "bolu": "14",
    "burdur": "15",
    "bursa": "16",
    "canakkale": "17",
    "cankiri": "18",
    "corum": "19",
    "denizli": "20",
    "diyarbakir": "21",
    "edirne": "22",
    "elazig": "23",
    "erzincan": "24",
    "erzurum": "25",
    "eskisehir": "26",
    "gaziantep": "27",
    "giresun": "28",
    "gumushane": "29",
    "hakkari": "30",
    "hatay": "31",
    "isparta": "32",
    "mersin": "33",
    "kars": "36",
    "kastamonu": "37",
    "kayseri": "38",
    "kirklareli": "39",
    "kirsehir": "40",
    "kocaeli": "41",
    "konya": "42",
    "kutahya": "43",
    "malatya": "44",
    "manisa": "45",
    "kahramanmaras": "46",
    "mardin": "47",
    "mugla": "48",
    "mus": "49",
    "nevsehir": "50",
    "nigde": "51",
    "ordu": "52",
    "rize": "53",
    "sakarya": "54",
    "samsun": "55",
    "siirt": "56",
    "sinop": "57",
    "sivas": "58",
    "tekirdag": "59",
    "tokat": "60",
    "trabzon": "61",
    "tunceli": "62",
    "sanliurfa": "63",
    "usak": "64",
    "van": "65",
    "yozgat": "66",
    "zonguldak": "67",
    "aksaray": "68",
    "bayburt": "69",
    "karaman": "70",
    "kirikkale": "71",
    "batman": "72",
    "sirnak": "73",
    "bartin": "74",
    "ardahan": "75",
    "igdir": "76",
    "yalova": "77",
    "karabuk": "78",
    "kilis": "79",
    "osmaniye": "80",
    "duzce": "81"
}

DEFAULT_KARIYER_CITY_CODES = [
    "34",  # İstanbul
    "06",  # Ankara
    "35",  # İzmir
    "16",  # Bursa
    "41",  # Kocaeli
    "07"   # Antalya
]

CITY_NAMES_BY_CODE = {
    code: city.title()
    for city, code in CITY_MAP.items()
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

        return []

    return DEFAULT_KARIYER_CITY_CODES.copy()


def get_kariyer_keywords(keyword):

    keyword = str(
        keyword or ""
    ).strip()

    if not keyword:

        return []

    return [keyword]


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


def count_jobs_by_source(jobs):

    source_sites = {
        "kariyer": "Kariyer",
        "jooble": "Jooble"
    }

    counts = {
        source: 0
        for source in source_sites
    }

    for job in jobs:

        site = getattr(
            job,
            "site",
            ""
        )

        for source, site_name in source_sites.items():

            if site == site_name:

                counts[source] += 1

    return counts


def smart_search(
    keyword,
    selected_city=None,
    sources=None,
    status_callback=None,
    report_callback=None
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

    source_errors = {}

    def add_source_error(source, message):

        source_errors[source] = message

    keywords = expand_keywords(keyword)

    kariyer_keywords = get_kariyer_keywords(
        keyword
    )

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

        if not locations:

            add_source_error(
                "kariyer",
                "Kariyer.net bu şehir için arama kodu bulamadı."
            )

            emit_status(
                "Kariyer.net bu şehir için atlandı."
            )

        for kw in kariyer_keywords:

            if not locations:

                break

            for loc in locations:

                try:

                    city_name = CITY_NAMES_BY_CODE.get(
                        loc,
                        loc
                    )

                    emit_status(
                        f"Kariyer.net aranıyor: {city_name}"
                    )

                    kariyer_jobs = search_kariyer(
                        kw,
                        city=loc,
                        raise_errors=True,
                        max_pages=2
                    )

                    all_jobs.extend(
                        kariyer_jobs
                    )

                except Exception as e:

                    message = "Kariyer.net geçici olarak yanıt vermedi."

                    add_source_error(
                        "kariyer",
                        message
                    )

                    emit_status(message)

                    print("Kariyer hata:", e)

    # JOOBLE
    if "jooble" in selected_sources:

        if not get_jooble_api_key():

            message = "Jooble API anahtarı yok; Jooble atlandı."

            add_source_error(
                "jooble",
                message
            )

            emit_status(message)

        else:

            for kw in keywords:

                try:

                    emit_status("Jooble aranıyor...")

                    jooble_jobs = search_jooble(
                        kw,
                        location=jooble_location,
                        raise_errors=True
                    )

                    all_jobs.extend(
                        jooble_jobs
                    )

                except Exception as e:

                    status_code = get_http_status(e)

                    if status_code == 403:

                        message = (
                            "Jooble API anahtarı geçersiz veya henüz aktif değil."
                        )

                    else:

                        message = (
                            "Jooble geçici olarak yanıt vermedi."
                        )

                    add_source_error(
                        "jooble",
                        message
                    )

                    emit_status(message)

                    print(
                        "Jooble hata:",
                        e
                    )

    # 🔥 DUPLICATE REMOVE
    unique_jobs = deduplicate_jobs(
        all_jobs
    )

    source_counts = count_jobs_by_source(
        unique_jobs
    )

    emit_status(
        f"{len(unique_jobs)} ilan bulundu."
    )

    if report_callback:

        report_callback(
            {
                "source_counts": source_counts,
                "source_errors": source_errors
            }
        )

    return unique_jobs
