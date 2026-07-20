import json
import logging
import zipfile

from ui.diagnostics import (
    build_diagnostic_archive,
    configure_logging,
    get_log_file,
)


def test_configure_logging_writes_and_redacts_sensitive_url(tmp_path):
    log_file = configure_logging(tmp_path)
    root_logger = logging.getLogger()

    logging.getLogger("test.diagnostics").error(
        "İstek başarısız: https://tr.jooble.org/api/private-test-key"
    )

    matching_handlers = [
        handler
        for handler in root_logger.handlers
        if getattr(handler, "baseFilename", None) == str(log_file)
    ]

    for handler in matching_handlers:
        handler.flush()

    contents = log_file.read_text(encoding="utf-8")
    assert "private-test-key" not in contents
    assert "/api/[GİZLENDİ]" in contents

    for handler in matching_handlers:
        root_logger.removeHandler(handler)
        handler.close()


def test_diagnostic_archive_excludes_private_data_and_user_files(tmp_path):
    app_data_dir = tmp_path / "app-data"
    log_file = get_log_file(app_data_dir)
    log_file.parent.mkdir(parents=True)
    log_file.write_text("örnek log", encoding="utf-8")

    (app_data_dir / "settings.json").write_text(
        json.dumps(
            {
                "appearance_mode": "dark",
                "last_keyword": "kişisel arama",
                "search_history": ["gizli arama"],
                "api_key": "private-key",
            }
        ),
        encoding="utf-8",
    )
    (app_data_dir / "favorites.json").write_text("[]", encoding="utf-8")
    (app_data_dir / "jooble_api_key.txt").write_text(
        "private-key",
        encoding="utf-8",
    )

    archive_path = build_diagnostic_archive(
        tmp_path / "diagnostics.zip",
        app_data_dir=app_data_dir,
    )

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        report = json.loads(archive.read("diagnostics.json"))

    assert names == {"diagnostics.json", "logs/izbul.log"}
    assert report["settings"]["appearance_mode"] == "dark"
    assert report["settings"]["last_keyword"] == "[GİZLENDİ]"
    assert report["settings"]["search_history"] == "[GİZLENDİ]"
    assert report["settings"]["api_key"] == "[GİZLENDİ]"
