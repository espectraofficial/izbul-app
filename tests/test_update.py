import hashlib
import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ui import update_mixin
from ui.update_mixin import (
    UpdateMixin,
    download_verified_file,
    is_windows_store_install,
    parse_sha256_checksum,
)
from ui.macos_updater import find_running_app_bundle, verify_update_signature


class FakeResponse:
    def __init__(self, *, payload=None, text="", content=b"", headers=None):
        self._payload = payload
        self.text = text
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload

    def iter_content(self, chunk_size):
        midpoint = max(1, len(self.content) // 2)
        yield self.content[:midpoint]
        yield self.content[midpoint:]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_windows_store_install_is_detected_from_package_identity():
    assert is_windows_store_install(
        platform_name="win32",
        package_probe=lambda _length, _buffer: 122,
    )


def test_unpacked_or_non_windows_install_is_not_store_managed():
    assert not is_windows_store_install(
        platform_name="win32",
        package_probe=lambda _length, _buffer: 15700,
    )
    assert not is_windows_store_install(
        platform_name="darwin",
        package_probe=lambda _length, _buffer: 122,
    )


def test_store_install_skips_github_update_check(monkeypatch):
    class DummyUpdater(UpdateMixin):
        update_check_in_progress = False
        latest_release_info = {"version": "9.9.9"}

        def show_toast(self, message, color):
            self.toast = (message, color)

    monkeypatch.setattr(
        update_mixin,
        "is_windows_store_install",
        lambda: True,
    )
    updater = DummyUpdater()

    assert updater.check_for_updates(silent=False) is False
    assert updater.latest_release_info is None
    assert updater.update_check_in_progress is False
    assert "Microsoft Store" in updater.toast[0]


def test_parse_sha256_checksum_selects_matching_asset():
    expected = "a" * 64
    checksum_text = (
        f"{'b' * 64}  Izbul-Windows-Setup.exe\n"
        f"{expected}  Izbul-macOS.dmg\n"
    )

    assert parse_sha256_checksum(checksum_text, "Izbul-macOS.dmg") == expected


def test_get_latest_release_includes_checksum_size_and_notes(monkeypatch):
    release = {
        "tag_name": "v1.0.2",
        "html_url": "https://github.com/example/releases/v1.0.2",
        "body": "Hata düzeltmeleri ve performans iyileştirmeleri.",
        "assets": [
            {
                "name": "Izbul-macOS.zip",
                "browser_download_url": "https://example.test/Izbul-macOS.zip",
                "size": 12000,
            },
            {
                "name": "Izbul-macOS.zip.sha256",
                "browser_download_url": (
                    "https://example.test/Izbul-macOS.zip.sha256"
                ),
                "size": 90,
            },
            {
                "name": "Izbul-macOS.zip.sig",
                "browser_download_url": "https://example.test/Izbul-macOS.zip.sig",
                "size": 89,
            },
            {
                "name": "Izbul-macOS.dmg",
                "browser_download_url": "https://example.test/Izbul-macOS.dmg",
                "size": 12345,
            },
            {
                "name": "Izbul-macOS.dmg.sha256",
                "browser_download_url": (
                    "https://example.test/Izbul-macOS.dmg.sha256"
                ),
                "size": 90,
            },
        ],
    }

    monkeypatch.setattr(update_mixin.sys, "platform", "darwin")
    monkeypatch.setattr(
        update_mixin.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(payload=release),
    )

    info = UpdateMixin().get_latest_release()

    assert info["asset_name"] == "Izbul-macOS.zip"
    assert info["asset_size"] == 12000
    assert info["checksum_asset_name"] == "Izbul-macOS.zip.sha256"
    assert info["checksum_url"].endswith(".sha256")
    assert info["signature_asset_name"] == "Izbul-macOS.zip.sig"
    assert info["signature_url"].endswith(".sig")
    assert info["release_notes"].startswith("Hata düzeltmeleri")


def test_download_verified_file_replaces_target_after_validation(tmp_path):
    content = b"verified installer content"
    checksum = hashlib.sha256(content).hexdigest()
    progress = []

    def fake_get(url, **kwargs):
        if url.endswith(".sha256"):
            return FakeResponse(
                text=f"{checksum}  Izbul-macOS.dmg\n"
            )

        return FakeResponse(
            content=content,
            headers={"content-length": str(len(content))},
        )

    target = tmp_path / "Izbul-macOS.dmg"
    target.write_bytes(b"old installer")

    result = download_verified_file(
        "https://example.test/Izbul-macOS.dmg",
        "https://example.test/Izbul-macOS.dmg.sha256",
        target,
        target.name,
        expected_size=len(content),
        progress_callback=progress.append,
        request_get=fake_get,
    )

    assert result == target
    assert target.read_bytes() == content
    assert progress[-1] == 100
    assert not target.with_name(target.name + ".part").exists()


def test_hash_mismatch_keeps_existing_installer_and_removes_partial(tmp_path):
    content = b"tampered installer"

    def fake_get(url, **kwargs):
        if url.endswith(".sha256"):
            return FakeResponse(
                text=f"{'0' * 64}  Izbul-Windows-Setup.exe\n"
            )

        return FakeResponse(
            content=content,
            headers={"content-length": str(len(content))},
        )

    target = tmp_path / "Izbul-Windows-Setup.exe"
    target.write_bytes(b"previous valid installer")

    with pytest.raises(ValueError, match="SHA-256"):
        download_verified_file(
            "https://example.test/Izbul-Windows-Setup.exe",
            "https://example.test/Izbul-Windows-Setup.exe.sha256",
            target,
            target.name,
            expected_size=len(content),
            request_get=fake_get,
        )

    assert target.read_bytes() == b"previous valid installer"
    assert not target.with_name(target.name + ".part").exists()


def test_automatic_download_is_refused_without_checksum(monkeypatch):
    opened_urls = []

    class DummyUpdater(UpdateMixin):
        latest_release_info = None

        def show_toast(self, message, color):
            self.toast = (message, color)

    monkeypatch.setattr(
        update_mixin.webbrowser,
        "open",
        opened_urls.append,
    )
    updater = DummyUpdater()

    started = updater.start_update_download(
        {
            "url": "https://example.test/releases/v1.0.2",
            "download_url": "https://example.test/Izbul-macOS.dmg",
            "asset_name": "Izbul-macOS.dmg",
            "checksum_url": "",
        }
    )

    assert started is False
    assert "Checksum bulunamadı" in updater.toast[0]
    assert opened_urls == ["https://example.test/releases/v1.0.2"]


def test_macos_zip_is_refused_without_digital_signature(monkeypatch):
    opened_urls = []

    class DummyUpdater(UpdateMixin):
        latest_release_info = None

        def show_toast(self, message, color):
            self.toast = (message, color)

    monkeypatch.setattr(update_mixin.sys, "platform", "darwin")
    monkeypatch.setattr(update_mixin.webbrowser, "open", opened_urls.append)
    updater = DummyUpdater()

    started = updater.start_update_download(
        {
            "url": "https://example.test/releases/v1.0.2",
            "download_url": "https://example.test/Izbul-macOS.zip",
            "asset_name": "Izbul-macOS.zip",
            "checksum_url": "https://example.test/Izbul-macOS.zip.sha256",
            "signature_url": "",
        }
    )

    assert started is False
    assert "Dijital imza bulunamadı" in updater.toast[0]
    assert opened_urls == ["https://example.test/releases/v1.0.2"]


def test_ed25519_signature_verifies_archive_digest(tmp_path):
    archive = tmp_path / "Izbul-macOS.zip"
    archive.write_bytes(b"signed update archive")
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_key_file = tmp_path / "update_public_key.txt"
    public_key_file.write_text(
        base64.b64encode(public_key).decode("ascii"),
        encoding="ascii",
    )
    signature = private_key.sign(hashlib.sha256(archive.read_bytes()).digest())

    assert verify_update_signature(
        archive,
        base64.b64encode(signature).decode("ascii"),
        public_key_file,
    )

    archive.write_bytes(b"tampered update archive")
    with pytest.raises(ValueError, match="dijital imzası"):
        verify_update_signature(
            archive,
            base64.b64encode(signature).decode("ascii"),
            public_key_file,
        )


def test_running_app_bundle_is_found_from_pyinstaller_executable(tmp_path):
    executable = tmp_path / "Izbul.app" / "Contents" / "MacOS" / "Izbul"
    executable.parent.mkdir(parents=True)
    executable.touch()

    assert find_running_app_bundle(executable) == tmp_path / "Izbul.app"
