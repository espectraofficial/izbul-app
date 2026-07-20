import json
import logging
import platform
import re
import sys
import threading
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ui.config import APP_NAME, APP_VERSION
from ui.storage import get_app_data_dir


LOG_DIRECTORY_NAME = "logs"
LOG_FILE_NAME = "izbul.log"
SENSITIVE_SETTING_MARKERS = (
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
)
PRIVATE_SETTING_KEYS = {
    "last_keyword",
    "last_city",
    "search_history",
}


class RedactingFormatter(logging.Formatter):
    REDACTION_PATTERNS = (
        (re.compile(r"(/api/)[^/\s?]+", re.IGNORECASE), r"\1[GİZLENDİ]"),
        (
            re.compile(
                r"((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+",
                re.IGNORECASE,
            ),
            r"\1[GİZLENDİ]",
        ),
    )

    def format(self, record):
        message = super().format(record)

        for pattern, replacement in self.REDACTION_PATTERNS:
            message = pattern.sub(replacement, message)

        return message


def get_log_dir(app_data_dir=None):
    base_dir = Path(app_data_dir) if app_data_dir else get_app_data_dir()
    return base_dir / LOG_DIRECTORY_NAME


def get_log_file(app_data_dir=None):
    return get_log_dir(app_data_dir) / LOG_FILE_NAME


def _log_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger("izbul.crash").critical(
        "Yakalanmayan uygulama hatası",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def _log_thread_exception(args):
    logging.getLogger("izbul.crash").critical(
        "Arka plan iş parçacığında yakalanmayan hata: %s",
        args.thread.name if args.thread else "bilinmiyor",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def configure_logging(app_data_dir=None):
    log_file = get_log_file(app_data_dir)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    resolved_log_file = log_file.resolve()
    has_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename).resolve() == resolved_log_file
        for handler in root_logger.handlers
    )

    if not has_file_handler:
        handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            RedactingFormatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        root_logger.addHandler(handler)

    sys.excepthook = _log_uncaught_exception
    threading.excepthook = _log_thread_exception

    logging.getLogger("izbul").info(
        "%s %s başlatıldı | %s | Python %s",
        APP_NAME,
        APP_VERSION,
        platform.platform(),
        platform.python_version(),
    )

    return log_file


def _sanitize_settings(value):
    if isinstance(value, dict):
        return {
            key: (
                "[GİZLENDİ]"
                if (
                    key.lower() in PRIVATE_SETTING_KEYS
                    or any(
                        marker in key.lower()
                        for marker in SENSITIVE_SETTING_MARKERS
                    )
                )
                else _sanitize_settings(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_sanitize_settings(item) for item in value]

    return value


def _load_safe_settings(app_data_dir):
    settings_file = Path(app_data_dir) / "settings.json"

    if not settings_file.exists():
        return {}

    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"durum": "Ayarlar dosyası okunamadı."}

    return _sanitize_settings(data) if isinstance(data, dict) else {}


def build_diagnostic_archive(destination, app_data_dir=None):
    app_data_dir = Path(app_data_dir) if app_data_dir else get_app_data_dir()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "application": APP_NAME,
        "version": APP_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "frozen_application": bool(getattr(sys, "frozen", False)),
        "settings": _load_safe_settings(app_data_dir),
    }

    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "diagnostics.json",
            json.dumps(report, ensure_ascii=False, indent=2),
        )

        log_dir = get_log_dir(app_data_dir)
        if log_dir.exists():
            for log_file in sorted(log_dir.glob(f"{LOG_FILE_NAME}*")):
                if log_file.is_file():
                    archive.write(log_file, f"logs/{log_file.name}")

    return destination
