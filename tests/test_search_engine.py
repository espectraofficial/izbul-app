from models.job import Job
from utils.search_engine import deduplicate_jobs, normalize_text


def test_normalize_text_removes_turkish_diacritics():

    assert normalize_text("İnsan Kaynakları Şefi") == "insan kaynakları sefi"


def test_deduplicate_jobs_uses_title_company_and_location():

    first = Job(
        site="Kariyer",
        company="ACME",
        title="Yazılım Uzmanı",
        description="",
        url="https://example.com/1",
        apply_url="https://example.com/1",
        location="İstanbul"
    )
    duplicate = Job(
        site="Jooble",
        company="acme",
        title="Yazılım Uzmanı",
        description="",
        url="https://example.com/2",
        apply_url="https://example.com/2",
        location="İstanbul"
    )

    assert deduplicate_jobs([first, duplicate]) == [first]
