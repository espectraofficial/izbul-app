import json
from pathlib import Path

from scrapers import eleman, jooble, kariyer


FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, *, payload=None, text=""):
        self._payload = payload
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def load_json(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_text(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_kariyer_search_contract_maps_api_fields(monkeypatch):
    payload = load_json("kariyer_search.json")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(payload=payload)

    monkeypatch.setattr(kariyer.requests, "post", fake_post)

    jobs = kariyer.search_kariyer("Yazilim", city="34", max_pages=1)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.site == "Kariyer"
    assert job.title == "Yazilim Gelistirme Uzmani"
    assert job.company == "ACME Teknoloji A.S."
    assert job.location == "Istanbul(Asya), Kocaeli"
    assert job.remote == "Hibrit"
    assert job.experience == "Mid-Level"
    assert job.posted_date == "2026-07-18"
    assert job.job_date_text == "2 gun"
    assert job.url.startswith("https://www.kariyer.net/")
    assert job.logo_url == "https://www.kariyer.net/firma-logo/acme.png"
    assert calls[0][1]["json"]["location"]["cities"] == ["34"]


def test_jooble_search_contract_maps_and_cleans_api_fields(monkeypatch):
    payload = load_json("jooble_search.json")

    monkeypatch.setattr(jooble, "get_jooble_api_key", lambda: "test-key")
    monkeypatch.setattr(
        jooble.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(payload=payload),
    )

    jobs = jooble.search_jooble("Veri Analisti", location="Ankara")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.site == "Jooble"
    assert job.title == "Junior Veri Analisti"
    assert job.company == "Ornek Analitik"
    assert job.description == (
        "Raporlama ve veri analizi ekibimize katilacak ekip arkadasi ariyoruz."
    )
    assert job.location == "Ankara"
    assert job.remote == "Remote"
    assert job.experience == "Junior"
    assert job.posted_date == "2026-07-19"
    assert job.logo_url == "https://cdn.example.test/ornek-analitik.png"


def test_eleman_json_ld_contract_maps_structured_fields():
    jobs = eleman.parse_json_ld_jobs(
        load_text("eleman_json_ld.html"),
        keyword="Pazarlama",
    )

    assert len(jobs) == 1
    job = jobs[0]
    assert job.site == "Eleman.net"
    assert job.title == "Pazarlama Stajyeri"
    assert job.company == "Ornek Medya"
    assert job.location == "Istanbul Avrupa - Sisli"
    assert job.experience == "Stajyer"
    assert job.remote == "Ofis"
    assert job.posted_date == "2026-07-19"
    assert job.logo_url == "https://img.example.test/ornek-medya.png"
    assert "zorunlu staj" in job.description


def test_eleman_listing_fallback_contract_maps_visible_card_fields(monkeypatch):
    html = load_text("eleman_listing.html")

    monkeypatch.setattr(
        eleman.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(text=html),
    )

    jobs = eleman.search_eleman("Pazarlama", city="Istanbul", max_pages=1)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.site == "Eleman.net"
    assert job.title == "Dijital Pazarlama Uzmanı"
    assert job.company == "Örnek Reklam"
    assert job.location == "İstanbul Avrupa"
    assert job.remote == "Ofis"
    assert job.experience == "Mid-Level"
    assert job.job_date_text == "Bugün"
    assert job.url == (
        "https://www.eleman.net/is-ilani/dijital-pazarlama-uzmani-i67890"
    )
    assert job.logo_url == "https://www.eleman.net/firma-logo/ornek-reklam.png"
    assert "Sosyal medya kampanyalarını" in job.description
