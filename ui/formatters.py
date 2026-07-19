import re
from datetime import datetime


def get_current_timestamp():

    return datetime.now().strftime("%Y-%m-%d %H:%M")


def format_saved_at(saved_at):

    saved_at = str(
        saved_at or ""
    ).strip()

    if not saved_at:

        return ""

    try:

        parsed_date = datetime.strptime(
            saved_at,
            "%Y-%m-%d %H:%M"
        )

        return parsed_date.strftime(
            "%d.%m.%Y %H:%M"
        )

    except ValueError:

        return saved_at


def format_job_date_text(job_date_text):

    job_date_text = str(
        job_date_text or ""
    ).strip()

    if not job_date_text:

        return ""

    normalized = job_date_text.lower()

    needs_before_suffix = (
        "önce" not in normalized and
        bool(
            re.search(
                r"\d",
                normalized
            )
        ) and
        (
            "dakika" in normalized or
            "saat" in normalized or
            "gün" in normalized or
            "hafta" in normalized or
            "ay" in normalized
        )
    )

    if needs_before_suffix:

        job_date_text = f"{job_date_text} önce"

    return f"Yayınlandığı tarih: {job_date_text}"


def format_card_location(location):

    location = " ".join(
        str(location or "").split()
    )

    if not location:

        return "Belirtilmemiş"

    leak_markers = [
        r"\b\d{4}\s+yıl",
        r"\bfaaliyet\s+gösteren\b",
        r"\bgörevlendirilmek\s+üzere\b",
        r"\bfirmamız\b",
        r"\bşirketimiz\b",
        r"\bkurumlara\b"
    ]

    cut_indexes = []

    for marker in leak_markers:

        match = re.search(
            marker,
            location,
            flags=re.IGNORECASE
        )

        if match:

            cut_indexes.append(match.start())

    if cut_indexes:

        location = location[:min(cut_indexes)].strip(" -,.")

    max_length = 72

    if len(location) > max_length:

        location = location[:max_length].rsplit(
            " ",
            1
        )[0].strip() + "..."

    return location or "Belirtilmemiş"
