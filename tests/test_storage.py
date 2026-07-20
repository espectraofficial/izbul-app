import importlib
import json
import sys


def reload_storage(monkeypatch, tmp_path, platform="linux", appdata=None):

    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setenv("HOME", str(tmp_path))

    if appdata is None:

        monkeypatch.delenv("APPDATA", raising=False)

    else:

        monkeypatch.setenv("APPDATA", str(appdata))

    import ui.storage as storage

    return importlib.reload(storage)


def test_get_app_data_dir_uses_config_on_linux(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)

    assert storage.get_app_data_dir() == tmp_path / ".config" / "İzbul"


def test_get_app_data_dir_uses_appdata_on_windows(monkeypatch, tmp_path):

    appdata = tmp_path / "AppData" / "Roaming"
    storage = reload_storage(
        monkeypatch,
        tmp_path,
        platform="win32",
        appdata=appdata
    )

    assert storage.get_app_data_dir() == appdata / "İzbul"


def test_save_and_load_settings_roundtrip(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)

    settings = storage.DEFAULT_SETTINGS.copy()
    settings["default_city"] = "İstanbul"
    settings["jobs_per_page"] = 20

    storage.save_settings(settings)

    loaded = storage.load_settings()

    assert loaded["default_city"] == "İstanbul"
    assert loaded["jobs_per_page"] == 20


def test_load_settings_merges_defaults(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)
    settings_file = storage.get_settings_file()

    settings_file.write_text(
        json.dumps({"default_city": "Ankara"}),
        encoding="utf-8"
    )

    loaded = storage.load_settings()

    assert loaded["default_city"] == "Ankara"
    assert "selected_sources" in loaded


def test_atomic_json_write_keeps_previous_valid_backup(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)
    settings_file = storage.get_settings_file()

    storage.write_json_atomic(settings_file, {"default_city": "Ankara"})
    storage.write_json_atomic(settings_file, {"default_city": "İzmir"})

    backup_file = storage.get_backup_file(settings_file)

    assert json.loads(settings_file.read_text(encoding="utf-8")) == {
        "default_city": "İzmir"
    }
    assert json.loads(backup_file.read_text(encoding="utf-8")) == {
        "default_city": "Ankara"
    }
    assert not list(settings_file.parent.glob(".*.tmp"))


def test_load_settings_recovers_corrupt_primary_from_backup(
    monkeypatch,
    tmp_path
):

    storage = reload_storage(monkeypatch, tmp_path)
    settings_file = storage.get_settings_file()

    storage.write_json_atomic(settings_file, {"default_city": "Ankara"})
    storage.write_json_atomic(settings_file, {"default_city": "İzmir"})
    settings_file.write_text("{bozuk-json", encoding="utf-8")

    loaded = storage.load_settings()

    assert loaded["default_city"] == "Ankara"
    assert json.loads(settings_file.read_text(encoding="utf-8")) == {
        "default_city": "Ankara"
    }


def test_invalid_primary_does_not_replace_valid_backup(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)
    data_file = tmp_path / "favorites.json"

    storage.write_json_atomic(data_file, [{"title": "Birinci"}])
    storage.write_json_atomic(data_file, [{"title": "İkinci"}])
    data_file.write_text("bozuk", encoding="utf-8")
    storage.write_json_atomic(data_file, [{"title": "Üçüncü"}])

    backup = storage.get_backup_file(data_file)

    assert json.loads(backup.read_text(encoding="utf-8")) == [
        {"title": "Birinci"}
    ]


def test_first_json_write_also_creates_recovery_backup(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)
    data_file = tmp_path / "hidden_jobs.json"

    storage.write_json_atomic(data_file, [{"url": "https://example.test/1"}])
    data_file.write_text("bozuk", encoding="utf-8")

    recovered = storage.load_json_with_backup(
        data_file,
        [],
        expected_type=list
    )

    assert recovered == [{"url": "https://example.test/1"}]


def test_missing_primary_is_restored_from_existing_backup(monkeypatch, tmp_path):

    storage = reload_storage(monkeypatch, tmp_path)
    data_file = tmp_path / "favorites.json"
    expected = [{"url": "https://example.test/job"}]

    storage.write_json_atomic(data_file, expected)
    data_file.unlink()

    recovered = storage.load_json_with_backup(
        data_file,
        [],
        expected_type=list
    )

    assert recovered == expected
    assert json.loads(data_file.read_text(encoding="utf-8")) == expected


def test_favorites_mixin_recovers_favorites_and_hidden_jobs_from_backups(
    monkeypatch,
    tmp_path
):

    reload_storage(monkeypatch, tmp_path)

    from ui.favorites_mixin import FavoritesMixin

    writer = FavoritesMixin()
    writer.favorites_file = tmp_path / "favorites.json"
    writer.hidden_jobs_file = tmp_path / "hidden_jobs.json"
    writer.favorite_jobs = [
        {
            "url": "https://example.test/job/1",
            "application_status": "Kaydedildi",
            "application_note": "",
            "saved_at": "2026-07-20T12:00:00",
            "status_updated_at": "2026-07-20T12:00:00",
        }
    ]
    writer.hidden_jobs = [{"url": "https://example.test/job/2"}]
    writer.save_favorites()
    writer.save_hidden_jobs()

    writer.favorites_file.write_text("bozuk", encoding="utf-8")
    writer.hidden_jobs_file.write_text("bozuk", encoding="utf-8")

    reader = FavoritesMixin()
    reader.favorites_file = writer.favorites_file
    reader.hidden_jobs_file = writer.hidden_jobs_file
    reader.load_favorites()
    reader.load_hidden_jobs()

    assert reader.favorite_jobs[0]["url"] == "https://example.test/job/1"
    assert reader.hidden_jobs == [{"url": "https://example.test/job/2"}]
