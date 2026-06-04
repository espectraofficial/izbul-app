import html
import json
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from models.job import Job
from utils.job_parser import (
    parse_remote,
    parse_experience
)


BASE_URL = "https://www.eleman.net"


TURKISH_CHAR_MAP = str.maketrans(
    {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
        "İ": "i",
        "Ğ": "g",
        "Ü": "u",
        "Ş": "s",
        "Ö": "o",
        "Ç": "c"
    }
)


def clean_text(value):

    text = re.sub(
        r"<[^>]+>",
        " ",
        str(value or "")
    )

    text = html.unescape(text)

    text = text.replace(
        "**",
        " "
    )

    return " ".join(
        text.split()
    )


def normalize_text(value):

    value = str(
        value or ""
    ).strip().translate(
        TURKISH_CHAR_MAP
    ).lower()

    normalized = unicodedata.normalize(
        "NFKD",
        value
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )


def get_keyword_terms(keyword):

    normalized = normalize_text(keyword)

    return [
        term
        for term in re.split(
            r"[^a-z0-9]+",
            normalized
        )
        if len(term) >= 3
    ]


def is_relevant_job(job, keyword):

    terms = get_keyword_terms(keyword)

    if not terms:

        return True

    searchable_text = normalize_text(
        " ".join(
            [
                getattr(job, "title", ""),
                getattr(job, "company", ""),
                getattr(job, "description", "")
            ]
        )
    )

    return all(
        term in searchable_text
        for term in terms
    )


def shorten_description(description, max_length=420):

    description = clean_text(description)

    description = re.sub(
        r"^.{0,90}\b(İş Tanımı|Aranan Nitelikler|Genel Nitelikler|Pozisyon Hakkında|Görev Tanımı)\b\s*",
        "",
        description
    ).strip()

    description = description.lstrip(
        ":;,- "
    )

    noise_markers = [
        "Özgeçmiş Oluştur",
        "Benzer İş İlanlarını",
        "İlan Yayınlandığında",
        "Eleman.net'te yayınlanmaktadır",
        "Firmayı Favorilerime Ekle",
        "Gizle Devamını Göster",
        "Devamını Göster"
    ]

    for marker in noise_markers:

        marker_index = description.find(marker)

        if marker_index != -1:

            description = description[:marker_index].strip()

    if len(description) <= max_length:

        return description

    return description[:max_length].rsplit(
        " ",
        1
    )[0].strip() + "..."


def slugify(value):

    value = str(
        value or ""
    ).strip().translate(
        TURKISH_CHAR_MAP
    ).lower()

    normalized = unicodedata.normalize(
        "NFKD",
        value
    )

    ascii_text = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    ascii_text = re.sub(
        r"[^a-z0-9]+",
        "-",
        ascii_text
    )

    return ascii_text.strip("-")


def build_search_url(keyword, city=None, page=1):

    keyword_slug = slugify(keyword)
    city_slug = slugify(city)

    parts = [
        BASE_URL,
        "is-ilanlari"
    ]

    if city_slug:

        parts.append(city_slug)

    if keyword_slug:

        parts.append(keyword_slug)

    url = "/".join(
        part.strip("/")
        for part in parts
    )

    if page > 1:

        url = f"{url}?sy={page}"

    return url


def get_logo_url(block):

    match = re.search(
        r"<img[^>]+(?:src|data-src)=[\"']([^\"']+)[\"']",
        block,
        flags=re.IGNORECASE
    )

    if not match:

        return ""

    logo_url = html.unescape(
        match.group(1)
    )

    if not logo_url or logo_url.startswith("data:"):

        return ""

    return urljoin(
        BASE_URL,
        logo_url
    )


def extract_job_date(text):

    date_patterns = [
        r"\bBugün\b",
        r"\bDün\b",
        r"\bYeni\b",
        r"\b\d+\s*gün önce\b"
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            date_text = match.group(0)

            if date_text.lower() == "yeni":

                return "", "Yeni"

            return "", date_text

    return "", ""


TITLE_END_WORDS = [
    "Uzmanı",
    "Elemanı",
    "Temsilcisi",
    "Personeli",
    "Müdürü",
    "Yöneticisi",
    "Sorumlusu",
    "Danışmanı",
    "Asistanı",
    "Yetkilisi",
    "Görevlisi",
    "Koordinatörü",
    "Direktörü",
    "Pazarlamacı",
    "Satışçı"
]


def strip_badge_words(value):

    return re.sub(
        r"\b(ACİL|Acil|Yeni)\b",
        "",
        str(value or "")
    ).strip()


def clean_location_segment(segment):

    segment = clean_text(segment)

    city_area_pattern = (
        r"^(.*?(?:İstanbul Anadolu|İstanbul Avrupa|İstanbul|"
        r"Ankara|İzmir|Kocaeli|Bursa|Antalya|Konya|Adana|"
        r"Tekirdağ|Yalova|Edirne|Eskişehir|Nevşehir|Sakarya)"
        r"(?:\s*,\s*(?:İstanbul Anadolu|İstanbul Avrupa|İstanbul|"
        r"Ankara|İzmir|Kocaeli|Bursa|Antalya|Konya|Adana|"
        r"Tekirdağ|Yalova|Edirne|Eskişehir|Nevşehir|Sakarya))*)"
    )

    match = re.search(
        city_area_pattern,
        segment,
        flags=re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    words = segment.split()

    if not words:

        return ""

    if len(words) > 1 and all(
        word[:1].isupper()
        for word in words[1:3]
    ):

        return words[0]

    return segment


def extract_title_company_from_prefix(prefix, keyword=""):

    prefix = clean_text(prefix)

    if not prefix:

        return "", ""

    title_pattern = (
        r"^(.+?\b(?:"
        + "|".join(
            re.escape(word)
            for word in TITLE_END_WORDS
        )
        + r")\b(?:\s*\([^)]*\))?)\s+(.*)$"
    )

    match = re.search(
        title_pattern,
        prefix,
        flags=re.IGNORECASE
    )

    if match:

        title = strip_badge_words(
            match.group(1)
        )

        company = strip_badge_words(
            match.group(2)
        )

        return title, company

    terms = get_keyword_terms(keyword)

    if terms:

        words = prefix.split()

        for index, word in enumerate(words):

            if any(
                term in normalize_text(word)
                for term in terms
            ):

                title = " ".join(
                    words[:index + 1]
                )

                company = " ".join(
                    words[index + 1:]
                )

                return (
                    strip_badge_words(title),
                    strip_badge_words(company)
                )

    words = prefix.split()

    return (
        strip_badge_words(
            " ".join(words[:5])
        ),
        strip_badge_words(
            " ".join(words[5:])
        )
    )


def parse_company_location_description(raw_text, keyword=""):

    text = clean_text(raw_text)

    segments = [
        segment.strip()
        for segment in re.split(
            r"\s+-\s+",
            text
        )
        if segment.strip()
    ]

    title = ""
    company = ""
    location = "Belirtilmemiş"
    description = text
    location_parts = []

    if segments:

        title, company = extract_title_company_from_prefix(
            segments[0],
            keyword=keyword
        )

    description_markers = (
        r"\b(İş Tanımı|İŞ TANIMI|Aranan|Genel Nitelikler|"
        r"Giriş Metni|Görev Tanımı|İş İlanı Hakkında|"
        r"Eleman\.net|Hakkımızda)\b|"
        r"\*\*|#{1,3}"
    )

    if len(segments) >= 2:

        for segment in segments[1:3]:

            cleaned_segment = re.split(
                description_markers,
                segment,
                flags=re.IGNORECASE
            )[0].strip()

            cleaned_segment = clean_location_segment(
                cleaned_segment
            )

            if cleaned_segment:

                location_parts.append(cleaned_segment)

        if location_parts:

            location = " - ".join(location_parts)

    if len(segments) >= 3:

        description = " - ".join(
            segments[2:]
        )
    elif len(segments) >= 2:

        description = segments[1]

    description = re.split(
        description_markers,
        description,
        maxsplit=1,
        flags=re.IGNORECASE
    )[-1].strip()

    if location_parts:

        last_location = location_parts[-1]

        if description.startswith(last_location):

            description = description[
                len(last_location):
            ].strip()

    description = shorten_description(description)

    if description == location:

        description = ""

    return title, company, location, description


class ElemanLinkParser(HTMLParser):

    def __init__(self):

        super().__init__()

        self.links = []
        self.current_href = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):

        if tag.lower() != "a":

            return

        attrs_dict = dict(attrs)

        href = attrs_dict.get("href", "")

        if "/is-ilani/" not in href:

            return

        self.current_href = href
        self.current_text = []

    def handle_data(self, data):

        if self.current_href:

            self.current_text.append(data)

    def handle_endtag(self, tag):

        if (
            tag.lower() == "a" and
            self.current_href
        ):

            title = clean_text(
                " ".join(self.current_text)
            )

            if title:

                self.links.append(
                    {
                        "href": self.current_href,
                        "title": title
                    }
                )

            self.current_href = None
            self.current_text = []


def parse_json_ld_jobs(html_text, keyword=""):

    jobs = []

    for match in re.finditer(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL
    ):

        try:

            data = json.loads(
                html.unescape(
                    match.group(1).strip()
                )
            )

        except Exception:

            continue

        items = data if isinstance(data, list) else [data]

        for item in items:

            if not isinstance(item, dict):

                continue

            graph_items = item.get(
                "@graph",
                [item]
            )

            for graph_item in graph_items:

                if not isinstance(graph_item, dict):

                    continue

                if graph_item.get("@type") != "JobPosting":

                    continue

                organization = graph_item.get(
                    "hiringOrganization",
                    {}
                )

                place = graph_item.get(
                    "jobLocation",
                    {}
                )

                address = place.get(
                    "address",
                    {}
                ) if isinstance(place, dict) else {}

                title = graph_item.get(
                    "title",
                    ""
                )

                description = shorten_description(
                    graph_item.get(
                        "description",
                        ""
                    )
                )

                link = graph_item.get(
                    "url",
                    ""
                )

                if not link:

                    continue

                job = Job(
                    site="Eleman.net",
                    company=organization.get(
                        "name",
                        ""
                    ) if isinstance(organization, dict) else "",
                    title=title,
                    description=description,
                    url=link,
                    apply_url=link,
                    remote=parse_remote(
                        title=title,
                        description=description
                    ),
                    experience=parse_experience(
                        title=title,
                        description=description
                    ),
                    location=" - ".join(
                        part
                        for part in [
                            address.get("addressRegion", ""),
                            address.get("addressLocality", "")
                        ]
                        if part
                    ) or "Belirtilmemiş",
                    posted_date=graph_item.get(
                        "datePosted",
                        ""
                    ),
                    job_date_text="",
                    logo_url=organization.get(
                        "logo",
                        ""
                    ) if isinstance(organization, dict) else ""
                )

                if not is_relevant_job(
                    job,
                    keyword
                ):

                    continue

                jobs.append(job)

    return jobs


def parse_listing_jobs(html_text, keyword=""):

    parser = ElemanLinkParser()
    parser.feed(html_text)

    jobs = []
    seen = set()

    link_matches = list(
        re.finditer(
            r"<a[^>]+href=[\"']([^\"']*/is-ilani/[^\"']+)[\"'][^>]*>",
            html_text,
            flags=re.IGNORECASE
        )
    )

    match_positions = {
        html.unescape(match.group(1)): index
        for index, match in enumerate(link_matches)
    }

    for link in parser.links:

        href = html.unescape(
            link.get("href", "")
        )

        if not href or href in seen:

            continue

        seen.add(href)

        raw_listing_text = clean_text(
            link.get("title", "")
        )

        if not raw_listing_text:

            continue

        link_match_index = match_positions.get(
            href
        )

        if link_match_index is None:

            block = ""

        else:

            start = link_matches[link_match_index].start()
            next_start = min(
                (
                    link_matches[link_match_index + 1].start()
                    if link_match_index + 1 < len(link_matches)
                    else start + 1800
                ),
                start + 1800
            )
            block = html_text[start:next_start]

        block_text = clean_text(block)

        title, company, location, description = parse_company_location_description(
            raw_listing_text,
            keyword=keyword
        )

        if not title:

            continue

        posted_date, job_date_text = extract_job_date(
            block_text
        )

        full_url = urljoin(
            BASE_URL,
            href
        )

        job = Job(
            site="Eleman.net",
            company=company,
            title=title,
            description=description,
            url=full_url,
            apply_url=full_url,
            remote=parse_remote(
                title=title,
                description=description
            ),
            experience=parse_experience(
                title=title,
                description=description
            ),
            location=location,
            posted_date=posted_date,
            job_date_text=job_date_text,
            logo_url=get_logo_url(block)
        )

        if not is_relevant_job(
            job,
            keyword
        ):

            continue

        jobs.append(job)

    return jobs


def search_eleman(
    keyword,
    city=None,
    raise_errors=False,
    max_pages=1
):

    jobs = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    for page in range(
        1,
        max_pages + 1
    ):

        url = build_search_url(
            keyword,
            city=city,
            page=page
        )

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=12
            )

            response.raise_for_status()

        except Exception as e:

            if raise_errors:

                raise

            print("Eleman.net request hata:", e)

            break

        page_jobs = parse_json_ld_jobs(
            response.text,
            keyword=keyword
        )

        if not page_jobs:

            page_jobs = parse_listing_jobs(
                response.text,
                keyword=keyword
            )

        if not page_jobs:

            break

        jobs.extend(page_jobs)

    return jobs
