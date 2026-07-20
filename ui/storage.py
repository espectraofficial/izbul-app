import copy
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

from ui.config import (
    APP_NAME,
    DEFAULT_SETTINGS,
    LEGACY_APP_NAME
)


logger = logging.getLogger(__name__)


def get_backup_file(file_path):
    file_path = Path(file_path)
    return file_path.with_suffix(file_path.suffix + ".bak")


def _write_bytes_atomic(file_path, content):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, file_path)
        temp_path = None

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _read_json(file_path, expected_type=None):
    with Path(file_path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    if expected_type is not None and not isinstance(data, expected_type):
        raise ValueError(
            f"Beklenen JSON türü {expected_type.__name__}, "
            f"bulunan {type(data).__name__}"
        )

    return data


def write_json_atomic(file_path, data):
    file_path = Path(file_path)
    backup_file = get_backup_file(file_path)
    serialized = (
        json.dumps(data, ensure_ascii=False, indent=4) + "\n"
    ).encode("utf-8")

    if file_path.exists():
        try:
            _read_json(file_path, expected_type=type(data))
            _write_bytes_atomic(backup_file, file_path.read_bytes())
        except (OSError, ValueError, json.JSONDecodeError):
            logger.warning(
                "Geçersiz ana JSON yedeklenmedi: %s",
                file_path,
                exc_info=True,
            )

    _write_bytes_atomic(file_path, serialized)

    if not backup_file.exists():
        _write_bytes_atomic(backup_file, serialized)


def load_json_with_backup(file_path, default, expected_type=None):
    file_path = Path(file_path)
    expected_type = expected_type or type(default)
    backup_file = get_backup_file(file_path)

    if not file_path.exists():
        if not backup_file.exists():
            return copy.deepcopy(default)

        logger.warning(
            "Ana JSON bulunamadı, yedek deneniyor: %s",
            file_path,
        )

    else:
        try:
            return _read_json(file_path, expected_type=expected_type)
        except (OSError, ValueError, json.JSONDecodeError):
            logger.warning(
                "Ana JSON okunamadı, yedek deneniyor: %s",
                file_path,
                exc_info=True,
            )


    try:
        recovered = _read_json(backup_file, expected_type=expected_type)
        restored_content = (
            json.dumps(recovered, ensure_ascii=False, indent=4) + "\n"
        ).encode("utf-8")
        _write_bytes_atomic(file_path, restored_content)
        logger.info("JSON yedekten geri yüklendi: %s", file_path)
        return recovered
    except (OSError, ValueError, json.JSONDecodeError):
        logger.error(
            "JSON ve yedeği okunamadı: %s",
            file_path,
            exc_info=True,
        )
        return copy.deepcopy(default)


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
                if target.suffix == ".json":
                    migrated_data = _read_json(source)
                    write_json_atomic(target, migrated_data)
                else:
                    _write_bytes_atomic(target, source.read_bytes())

            except Exception as e:

                logger.exception("Eski uygulama verisi taşınamadı")


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

    data = load_json_with_backup(
        settings_file,
        {},
        expected_type=dict
    )
    settings = DEFAULT_SETTINGS.copy()
    settings.update(data)
    return settings


def save_settings(settings):

    settings_file = get_settings_file()

    write_json_atomic(settings_file, settings)


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

            write_json_atomic(favorites_file, data)

            return

        except Exception as e:

            logger.exception("Eski favoriler taşınamadı")
