import re
import sys
from pathlib import Path


APP_NAME = "İzbul"


def get_version_file():
    bundle_dir = getattr(sys, "_MEIPASS", None)

    if bundle_dir:
        bundled_version = Path(bundle_dir) / "VERSION"

        if bundled_version.exists():
            return bundled_version

    return Path(__file__).resolve().parent.parent / "VERSION"


def load_app_version():
    version_file = get_version_file()

    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(
            f"Uygulama sürüm dosyası okunamadı: {version_file}"
        ) from error

    if not version:
        raise RuntimeError("Uygulama sürümü boş olamaz.")

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise RuntimeError(
            "Uygulama sürümü major.minor.patch biçiminde olmalı."
        )

    return version


APP_VERSION = load_app_version()
LEGACY_APP_NAME = "Job Finder"

GITHUB_REPO = "espectraofficial/izbul-app"
GITHUB_RELEASES_API = (
    f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
)
GITHUB_RELEASES_URL = (
    f"https://github.com/{GITHUB_REPO}/releases/latest"
)

DEFAULT_SETTINGS = {
    "default_city": "",
    "jobs_per_page": 10,
    "appearance_mode": "dark",
    "last_keyword": "",
    "last_city": "",
    "selected_sources": [
        "kariyer",
        "jooble",
        "eleman"
    ],
    "eleman_source_added": False,
    "selected_application_statuses": [],
    "selected_experiences": [],
    "selected_remote": [],
    "sort_type": "Varsayılan",
    "search_history": []
}

THEME_LABELS = {
    "Koyu": "dark",
    "Açık": "light",
    "Sistem": "system"
}

THEME_VALUES = {
    value: label
    for label, value in THEME_LABELS.items()
}

APPLICATION_STATUSES = [
    "Kaydedildi",
    "Başvuruldu",
    "Görüşme",
    "Teklif",
    "Reddedildi"
]

APPLICATION_STATUS_COLORS = {
    "Kaydedildi": "#3A3A3A",
    "Başvuruldu": "#1F6AA5",
    "Görüşme": "#8E5A00",
    "Teklif": "#2E8B57",
    "Reddedildi": "#8B2E2E"
}


def get_theme_value(label):

    return THEME_LABELS.get(
        label,
        "dark"
    )


def get_theme_label(value):

    return THEME_VALUES.get(
        value,
        "Koyu"
    )
