from ui.versioning import is_newer_version, parse_version_parts


def test_parse_version_parts_normalizes_tags():

    assert parse_version_parts("v1.2.3") == (1, 2, 3)
    assert parse_version_parts("1.2") == (1, 2, 0)


def test_is_newer_version_detects_patch_update():

    assert is_newer_version("v1.0.2", "1.0.1") is True


def test_is_newer_version_rejects_same_or_older_version():

    assert is_newer_version("v1.0.1", "1.0.1") is False
    assert is_newer_version("v1.0.0", "1.0.1") is False
