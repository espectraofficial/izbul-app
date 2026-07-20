import re
from pathlib import Path

import pytest

from ui import config
from ui.config import APP_VERSION, load_app_version


ROOT = Path(__file__).resolve().parent.parent


def test_version_file_is_the_application_version_source():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert APP_VERSION == version
    assert load_app_version() == version


def test_packaging_files_read_version_instead_of_hardcoding_it():
    macos_script = (ROOT / "scripts/build_macos.sh").read_text(
        encoding="utf-8"
    )
    windows_script = (ROOT / "scripts/build_windows.ps1").read_text(
        encoding="utf-8"
    )
    inno_setup = (ROOT / "packaging/windows/izbul.iss").read_text(
        encoding="utf-8"
    )
    app_spec = (ROOT / "app.spec").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/build-installers.yml").read_text(
        encoding="utf-8"
    )

    assert "< VERSION" in macos_script
    assert "Get-Content $VersionFile" in windows_script
    assert "/DMyAppVersion=$AppVersion" in windows_script
    assert "#ifndef MyAppVersion" in inno_setup
    assert "Path('VERSION').read_text" in app_spec
    assert "('VERSION', '.')" in app_spec
    assert "('packaging/update_public_key.txt', '.')" in app_spec
    assert '--add-data "$PWD/VERSION:."' in macos_script
    assert '--add-data "$PWD/packaging/update_public_key.txt:."' in macos_script
    assert 'ZIP_NAME="Izbul-macOS.zip"' in macos_script
    assert "scripts/sign_update.py" in macos_script
    assert "secrets.IZBUL_UPDATE_PRIVATE_KEY" in workflow
    assert "actions/download-artifact@v8" in workflow
    assert "gh release upload" in workflow
    assert "contents: write" in workflow


def test_invalid_version_file_is_rejected(monkeypatch, tmp_path):
    invalid_version = tmp_path / "VERSION"
    invalid_version.write_text("v1.0", encoding="utf-8")
    monkeypatch.setattr(config, "get_version_file", lambda: invalid_version)

    with pytest.raises(RuntimeError, match="major.minor.patch"):
        config.load_app_version()


def test_bundled_application_reads_version_from_pyinstaller_dir(
    monkeypatch,
    tmp_path
):
    bundled_version = tmp_path / "VERSION"
    bundled_version.write_text("9.8.7", encoding="utf-8")
    monkeypatch.setattr(config.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert config.get_version_file() == bundled_version
    assert config.load_app_version() == "9.8.7"
