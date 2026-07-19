APP_NAME = "İzbul"
APP_VERSION = "1.0.1"
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
