from utils.job_parser import parse_experience, parse_remote


def test_parse_experience_uses_position_level_override():

    assert parse_experience(position_level=10) == "Senior"


def test_parse_experience_detects_intern_and_junior():

    assert parse_experience(title="Stajyer Yazılım Geliştirici") == "Stajyer"
    assert parse_experience(title="Junior Python Developer") == "Junior"


def test_parse_experience_detects_year_based_senior_level():

    assert parse_experience(description="En az 4 yıl deneyimli") == "Senior"


def test_parse_remote_prioritizes_hybrid_over_remote():

    assert parse_remote(work_model="Remote + office") == "Hibrit"


def test_parse_remote_detects_remote_and_office():

    assert parse_remote(description="Evden çalışma imkanı") == "Remote"
    assert parse_remote(work_model="Ofis") == "Ofis"
