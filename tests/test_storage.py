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
