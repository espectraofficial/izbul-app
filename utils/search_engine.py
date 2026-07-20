import logging
import unicodedata

from scrapers.kariyer import search_kariyer
from scrapers.eleman import search_eleman
from scrapers.jooble import (
    get_jooble_api_key,
    search_jooble
)


logger = logging.getLogger(__name__)


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

SOURCE_SITE_BY_KEY = {
    "kariyer": "Kariyer",
    "jooble": "Jooble",
    "eleman": "Eleman.net"
}

SOURCE_KEY_BY_SITE = {
    site: source
    for source, site in SOURCE_SITE_BY_KEY.items()
}


def normalize_text(value):

    text = (
        str(value or "")
        .strip()
        .lower()
        .replace("ı", "i")
    )

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

    counts = {
        source: 0
        for source in SOURCE_SITE_BY_KEY
    }

    for job in jobs:

        source = SOURCE_KEY_BY_SITE.get(
            getattr(
                job,
                "site",
                ""
            )
        )

        if source:

            counts[source] += 1

    return counts


def smart_search(
    keyword,
    selected_city=None,
    sources=None,
    status_callback=None,
    report_callback=None,
    progress_callback=None
):

    all_jobs = []

    selected_sources = set(
        ["kariyer", "jooble", "eleman"]
        if sources is None
        else sources
    )

    def emit_status(message):

        if status_callback:

            status_callback(message)

    def emit_progress(source, status, count=None, message=""):

        if progress_callback:

            progress_callback(
                {
                    "source": source,
                    "status": status,
                    "count": count,
                    "message": message
                }
            )

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

    eleman_location = str(
        selected_city or ""
    ).strip()

    if not selected_sources:

        emit_status("En az bir kaynak seçin.")

        return []

    for source in selected_sources:

        emit_progress(
            source,
            "Bekliyor",
            count=0
        )

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

            emit_progress(
                "kariyer",
                "Atlandı",
                count=0,
                message="Şehir kodu bulunamadı."
            )

        kariyer_start_count = len(all_jobs)

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

                    emit_progress(
                        "kariyer",
                        "Aranıyor",
                        count=max(
                            0,
                            len(all_jobs) - kariyer_start_count
                        ),
                        message=city_name
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

                    emit_progress(
                        "kariyer",
                        "Hata",
                        count=max(
                            0,
                            len(all_jobs) - kariyer_start_count
                        ),
                        message=message
                    )

                    logger.exception("Kariyer.net araması başarısız")

        if locations and "kariyer" not in source_errors:

            emit_progress(
                "kariyer",
                "Tamamlandı",
                count=max(
                    0,
                    len(all_jobs) - kariyer_start_count
                )
            )

    # ELEMAN.NET
    if "eleman" in selected_sources:

        try:

            emit_status("Eleman.net aranıyor...")

            eleman_start_count = len(all_jobs)

            emit_progress(
                "eleman",
                "Aranıyor",
                count=0
            )

            eleman_jobs = search_eleman(
                keyword,
                city=eleman_location,
                raise_errors=True,
                max_pages=1
            )

            all_jobs.extend(
                eleman_jobs
            )

            emit_progress(
                "eleman",
                "Tamamlandı",
                count=max(
                    0,
                    len(all_jobs) - eleman_start_count
                )
            )

        except Exception as e:

            message = "Eleman.net geçici olarak yanıt vermedi."

            add_source_error(
                "eleman",
                message
            )

            emit_status(message)

            emit_progress(
                "eleman",
                "Hata",
                count=0,
                message=message
            )

            logger.exception("Eleman.net araması başarısız")

    # JOOBLE
    if "jooble" in selected_sources:

        if not get_jooble_api_key():

            message = "Jooble API anahtarı yok; Jooble atlandı."

            add_source_error(
                "jooble",
                message
            )

            emit_status(message)

            emit_progress(
                "jooble",
                "Atlandı",
                count=0,
                message=message
            )

        else:

            jooble_start_count = len(all_jobs)

            for kw in keywords:

                try:

                    emit_status("Jooble aranıyor...")

                    emit_progress(
                        "jooble",
                        "Aranıyor",
                        count=max(
                            0,
                            len(all_jobs) - jooble_start_count
                        )
                    )

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

                    emit_progress(
                        "jooble",
                        "Hata",
                        count=max(
                            0,
                            len(all_jobs) - jooble_start_count
                        ),
                        message=message
                    )

                    logger.exception("Jooble araması başarısız")

            if "jooble" not in source_errors:

                emit_progress(
                    "jooble",
                    "Tamamlandı",
                    count=max(
                        0,
                        len(all_jobs) - jooble_start_count
                    )
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
