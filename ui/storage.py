import json
import os
import sys
from pathlib import Path

from ui.config import (
    APP_NAME,
    DEFAULT_SETTINGS,
    LEGACY_APP_NAME
)


def get_app_data_dir(app_name=APP_NAME):

    if sys.platform == "darwin":

        return (
            Path.home()
            / "Library"
            / "Application Support"
            / app_name
        )

    if sys.platform.startswith("win"):

        appdata = os.getenv("APPDATA")

        if appdata:

            return Path(appdata) / app_name

    return (
        Path.home()
        / ".config"
        / app_name
    )


def migrate_legacy_app_data():

    current_dir = get_app_data_dir(APP_NAME)
    legacy_dir = get_app_data_dir(LEGACY_APP_NAME)

    if not legacy_dir.exists():

        return

    current_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    for file_name in [
        "favorites.json",
        "hidden_jobs.json",
        "settings.json",
        "jooble_api_key.txt"
    ]:

        source = legacy_dir / file_name
        target = current_dir / file_name

        if source.exists() and not target.exists():

            try:

                target.write_bytes(
                    source.read_bytes()
                )

            except Exception as e:

                print("Eski uygulama verisi taşınamadı:", e)


def get_favorites_file():

    migrate_legacy_app_data()

    app_data_dir = get_app_data_dir()

    app_data_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data_dir / "favorites.json"


def get_hidden_jobs_file():

    migrate_legacy_app_data()

    app_data_dir = get_app_data_dir()

    app_data_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data_dir / "hidden_jobs.json"


def get_settings_file():

    migrate_legacy_app_data()

    app_data_dir = get_app_data_dir()

    app_data_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return app_data_dir / "settings.json"


def load_settings():

    settings_file = get_settings_file()

    if not settings_file.exists():

        return DEFAULT_SETTINGS.copy()

    try:

        with open(
            settings_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        settings = DEFAULT_SETTINGS.copy()

        if isinstance(data, dict):

            settings.update(data)

        return settings

    except Exception as e:

        print("Ayarlar yüklenemedi:", e)

        return DEFAULT_SETTINGS.copy()


def save_settings(settings):

    settings_file = get_settings_file()

    with open(
        settings_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            settings,
            file,
            ensure_ascii=False,
            indent=4
        )


def migrate_legacy_favorites(favorites_file):

    if favorites_file.exists():

        return

    legacy_paths = [
        Path.cwd() / "favorites.json",
        Path(__file__).resolve().parent.parent / "favorites.json"
    ]

    for legacy_path in legacy_paths:

        if not legacy_path.exists():

            continue

        try:

            with open(
                legacy_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if not isinstance(data, list):

                continue

            with open(
                favorites_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            return

        except Exception as e:

            print("Eski favoriler taşınamadı:", e)
