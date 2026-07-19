from ui.formatters import (
    format_card_location,
    format_job_date_text,
    format_saved_at
)


def test_format_saved_at_converts_internal_timestamp():

    assert format_saved_at("2026-07-19 14:05") == "19.07.2026 14:05"


def test_format_saved_at_keeps_unknown_format():

    assert format_saved_at("bugün") == "bugün"


def test_format_job_date_text_adds_before_suffix_for_relative_time():

    assert format_job_date_text("5 saat") == "Yayınlandığı tarih: 5 saat önce"


def test_format_job_date_text_does_not_duplicate_before_suffix():

    assert format_job_date_text("2 gün önce") == "Yayınlandığı tarih: 2 gün önce"


def test_format_card_location_removes_eleman_description_leak():

    location = (
        "İstanbul Avrupa - Başakşehir 2004 yılından bu yana "
        "İnsan Kaynakları alanında faaliyet gösteren şirketimiz"
    )

    assert format_card_location(location) == "İstanbul Avrupa - Başakşehir"


def test_format_card_location_falls_back_when_empty():

    assert format_card_location("") == "Belirtilmemiş"
