from utils.job_parser import parse_experience, parse_remote


def test_parse_experience_uses_position_level_override():

    assert parse_experience(position_level=10) == "Senior"


def test_parse_experience_detects_intern_and_junior():

    assert parse_experience(title="Stajyer Yazılım Geliştirici") == "Stajyer"
    assert parse_experience(title="Stajyer İnsan Kaynakları Uzmanı") == "Stajyer"
    assert parse_experience(
        title="İnsan Kaynakları Stajyeri ( Zorunlu Staj )",
        position_level=5
    ) == "Stajyer"
    assert parse_experience(title="Junior Python Developer") == "Junior"
    assert parse_experience(title="İnsan Kaynakları Uzman Yardımcısı") == "Junior"
    assert parse_experience(title="İnsan Kaynakları Asistanı") == "Junior"
    assert parse_experience(title="Muhasebe Asistanlığı") == "Junior"
    assert parse_experience(title="HR Assistant") == "Junior"


def test_parse_experience_keeps_ambiguous_specialist_as_mid_level():

    assert parse_experience(title="İnsan Kaynakları Uzmanı") == "Mid-Level"
    assert parse_experience(title="Marketing Specialist") == "Mid-Level"


def test_parse_experience_detects_explicit_senior_specialist():

    assert parse_experience(title="Kıdemli İnsan Kaynakları Uzmanı") == "Senior"
    assert parse_experience(title="Senior Marketing Specialist") == "Senior"


def test_parse_experience_detects_management_titles_before_assistant_words():

    assert parse_experience(title="İnsan Kaynakları Müdür Yardımcısı") == "Manager"
    assert parse_experience(title="Assistant Manager") == "Manager"


def test_parse_experience_handles_cross_domain_titles():

    examples = [
        ("Stajyer Grafik Tasarımcı", "Stajyer"),
        ("Zorunlu Staj Yazılım Geliştirici", "Stajyer"),
        ("Muhasebe Yardımcı Elemanı", "Junior"),
        ("Çağrı Merkezi Asistanı", "Junior"),
        ("Junior Frontend Developer", "Junior"),
        ("Satış Uzmanı", "Mid-Level"),
        ("Operasyon Specialist", "Mid-Level"),
        ("Kıdemli Backend Developer", "Senior"),
        ("Senior Data Analyst", "Senior"),
        ("Depo Müdürü", "Manager"),
        ("Software Engineering Manager", "Manager"),
        ("Finance Director", "Director"),
        ("Chief Technology Officer", "Director"),
    ]

    for title, expected in examples:
        assert parse_experience(title=title) == expected


def test_parse_experience_detects_year_based_senior_level():

    assert parse_experience(description="En az 4 yıl deneyimli") == "Senior"


def test_parse_remote_prioritizes_hybrid_over_remote():

    assert parse_remote(work_model="Remote + office") == "Hibrit"


def test_parse_remote_detects_remote_and_office():

    assert parse_remote(description="Evden çalışma imkanı") == "Remote"
    assert parse_remote(work_model="Ofis") == "Ofis"
