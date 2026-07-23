import ctypes
import hashlib
import logging
import os
import re
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk
import requests

from ui.config import (
    APP_VERSION,
    GITHUB_RELEASES_API,
    GITHUB_RELEASES_URL
)
from ui.storage import get_app_data_dir
from ui.versioning import is_newer_version

if sys.platform == "darwin":
    from ui.macos_updater import launch_macos_update, verify_update_signature


logger = logging.getLogger(__name__)


ERROR_INSUFFICIENT_BUFFER = 122


def is_windows_store_install(platform_name=None, package_probe=None):
    platform_name = platform_name or sys.platform

    if platform_name != "win32":
        return False

    try:
        if package_probe is None:
            package_probe = ctypes.windll.kernel32.GetCurrentPackageFullName

        package_name_length = ctypes.c_uint32(0)
        result = package_probe(
            ctypes.byref(package_name_length),
            None
        )
        return result == ERROR_INSUFFICIENT_BUFFER
    except (AttributeError, OSError):
        return False


def parse_sha256_checksum(checksum_text, asset_name):
    asset_name = Path(asset_name).name

    for raw_line in str(checksum_text or "").splitlines():
        line = raw_line.strip()
        match = re.match(
            r"^([a-fA-F0-9]{64})(?:\s+[*]?(.+))?$",
            line
        )

        if not match:
            continue

        listed_name = str(match.group(2) or "").strip()

        if listed_name and Path(listed_name).name != asset_name:
            continue

        return match.group(1).lower()

    raise ValueError("Güncelleme checksum değeri bulunamadı.")


def download_verified_file(
    download_url,
    checksum_url,
    target_file,
    asset_name,
    expected_size=0,
    progress_callback=None,
    request_get=requests.get,
):
    checksum_response = request_get(checksum_url, timeout=10)
    checksum_response.raise_for_status()
    expected_hash = parse_sha256_checksum(
        checksum_response.text,
        asset_name
    )

    target_file = Path(target_file)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    partial_file = target_file.with_name(target_file.name + ".part")
    partial_file.unlink(missing_ok=True)
    digest = hashlib.sha256()
    downloaded = 0

    try:
        with request_get(
            download_url,
            stream=True,
            timeout=20
        ) as response:
            response.raise_for_status()
            header_size = int(response.headers.get("content-length", 0) or 0)
            total_size = header_size or int(expected_size or 0)

            with partial_file.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue

                    file.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size:
                        progress_callback(
                            min(100, int(downloaded * 100 / total_size))
                        )

                file.flush()
                os.fsync(file.fileno())

        if header_size and downloaded != header_size:
            raise ValueError("Güncelleme dosyası eksik indirildi.")

        if expected_size and downloaded != int(expected_size):
            raise ValueError("Güncelleme dosyasının boyutu doğrulanamadı.")

        if digest.hexdigest().lower() != expected_hash:
            raise ValueError("Güncelleme dosyasının SHA-256 doğrulaması başarısız.")

        os.replace(partial_file, target_file)
        return target_file

    finally:
        partial_file.unlink(missing_ok=True)


class UpdateMixin:

    def get_latest_release(self):

        try:

            response = requests.get(
                GITHUB_RELEASES_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"Izbul/{APP_VERSION}"
                },
                timeout=8
            )

            response.raise_for_status()

        except requests.HTTPError as error:

            status_code = error.response.status_code if error.response else None

            if status_code == 404:

                raise RuntimeError(
                    "GitHub release bulunamadı. Repo private olabilir, "
                    "release henüz yayınlanmamış olabilir veya repo adı hatalı olabilir."
                ) from error

            if status_code == 403:

                raise RuntimeError(
                    "GitHub release bilgisine erişim engellendi. "
                    "Repo private olabilir veya GitHub API limitine takılmış olabilir."
                ) from error

            raise RuntimeError(
                f"GitHub release kontrolü başarısız oldu. HTTP {status_code}."
            ) from error

        release = response.json()

        tag_name = str(
            release.get(
                "tag_name",
                ""
            )
        ).strip()

        html_url = str(
            release.get(
                "html_url",
                ""
            )
        ).strip() or GITHUB_RELEASES_URL

        assets = release.get(
            "assets",
            []
        )

        download_url = html_url
        asset_name = ""
        selected_asset = None

        preferred_asset_groups = []

        if sys.platform == "darwin":

            preferred_asset_groups = [
                ["macOS", "zip"],
                ["macOS", "dmg"]
            ]

        elif sys.platform.startswith("win"):

            preferred_asset_groups = [
                ["Windows", "Setup", "exe"],
                ["Windows", "zip"]
            ]

        if preferred_asset_groups and isinstance(assets, list):

            for keywords in preferred_asset_groups:

                matching_asset = None

                for asset in assets:

                    candidate_name = str(
                        asset.get(
                            "name",
                            ""
                        )
                    )

                    if all(
                        keyword.lower() in candidate_name.lower()
                        for keyword in keywords
                    ):

                        matching_asset = asset

                        break

                if matching_asset:

                    selected_asset = matching_asset

                    asset_name = str(
                        matching_asset.get(
                            "name",
                            ""
                        )
                    )

                    download_url = matching_asset.get(
                        "browser_download_url",
                        html_url
                    )

                    break

        checksum_url = ""
        checksum_asset_name = ""
        signature_url = ""
        signature_asset_name = ""

        if selected_asset and asset_name:
            checksum_names = {
                f"{asset_name}.sha256".lower(),
                f"{asset_name}.sha256.txt".lower(),
                "sha256sums.txt",
            }

            for asset in assets:
                candidate_name = str(asset.get("name", ""))

                if candidate_name.lower() in checksum_names:
                    checksum_asset_name = candidate_name
                    checksum_url = str(
                        asset.get("browser_download_url", "")
                    ).strip()
                    break

            signature_names = {
                f"{asset_name}.sig".lower(),
                f"{asset_name}.signature".lower(),
            }

            for asset in assets:
                candidate_name = str(asset.get("name", ""))

                if candidate_name.lower() in signature_names:
                    signature_asset_name = candidate_name
                    signature_url = str(
                        asset.get("browser_download_url", "")
                    ).strip()
                    break

        return {
            "version": tag_name,
            "url": html_url,
            "download_url": download_url,
            "asset_name": asset_name,
            "asset_size": int(
                selected_asset.get("size", 0) or 0
            ) if selected_asset else 0,
            "checksum_url": checksum_url,
            "checksum_asset_name": checksum_asset_name,
            "signature_url": signature_url,
            "signature_asset_name": signature_asset_name,
            "release_notes": str(release.get("body", "") or "").strip(),
        }

    def open_latest_release(self):

        release_info = self.latest_release_info or {}

        self.start_update_download(
            release_info
        )

    def get_update_download_dir(self):

        downloads_dir = (
            Path.home()
            / "Downloads"
        )

        if not downloads_dir.exists():

            downloads_dir = get_app_data_dir()

        update_dir = downloads_dir / "Izbul Updates"

        update_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        return update_dir

    def get_update_file_name(self, release_info):

        asset_name = str(
            release_info.get(
                "asset_name",
                ""
            )
        ).strip()

        if asset_name:

            return asset_name

        if sys.platform == "darwin":

            return "Izbul-macOS.dmg"

        if sys.platform.startswith("win"):

            return "Izbul-Windows-Setup.exe"

        return "Izbul-update"

    def open_downloaded_update(self, file_path):

        file_path = Path(file_path)

        if sys.platform == "darwin":

            subprocess.Popen(
                [
                    "open",
                    str(file_path)
                ]
            )

        elif sys.platform.startswith("win"):

            os.startfile(str(file_path))

        else:

            webbrowser.open(
                file_path.as_uri()
            )

    def start_update_download(self, release_info=None, status_callback=None):

        release_info = release_info or self.latest_release_info or {}

        download_url = str(
            release_info.get(
                "download_url",
                ""
            )
        ).strip()

        release_url = str(
            release_info.get(
                "url",
                GITHUB_RELEASES_URL
            )
        ).strip()

        checksum_url = str(
            release_info.get("checksum_url", "")
        ).strip()
        signature_url = str(
            release_info.get("signature_url", "")
        ).strip()
        is_macos_self_update = (
            sys.platform == "darwin"
            and str(release_info.get("asset_name", "")).lower().endswith(".zip")
        )

        if not download_url or download_url == release_url:

            webbrowser.open(
                release_url or GITHUB_RELEASES_URL
            )

            return False

        if not checksum_url:
            message = (
                "Checksum bulunamadı; güvenli indirme için "
                "release sayfası açılıyor."
            )

            if status_callback:
                status_callback(message, "#C0392B")
            else:
                self.show_toast(message, "#C0392B")

            webbrowser.open(release_url or GITHUB_RELEASES_URL)
            return False

        if is_macos_self_update and not signature_url:
            message = (
                "Dijital imza bulunamadı; güvenli güncelleme için "
                "release sayfası açılıyor."
            )

            if status_callback:
                status_callback(message, "#C0392B")
            else:
                self.show_toast(message, "#C0392B")

            webbrowser.open(release_url or GITHUB_RELEASES_URL)
            return False

        file_name = self.get_update_file_name(
            release_info
        )

        target_file = (
            self.get_update_download_dir()
            / file_name
        )

        def set_status(message, color="#D8DEE9"):

            if status_callback:

                self.after(
                    0,
                    lambda:
                    status_callback(
                        message,
                        color
                    )
                )

            else:

                self.after(
                    0,
                    lambda:
                    self.show_toast(
                        message,
                        color
                    )
                )

        def run():

            try:

                set_status(
                    "Güncelleme indiriliyor...",
                    "#1F6AA5"
                )

                download_verified_file(
                    download_url=download_url,
                    checksum_url=checksum_url,
                    target_file=target_file,
                    asset_name=file_name,
                    expected_size=int(
                        release_info.get("asset_size", 0) or 0
                    ),
                    progress_callback=lambda percent: set_status(
                        f"Güncelleme indiriliyor... %{percent}",
                        "#1F6AA5"
                    )
                )

                if is_macos_self_update:
                    signature_response = requests.get(signature_url, timeout=10)
                    signature_response.raise_for_status()
                    verify_update_signature(
                        target_file,
                        signature_response.text,
                    )

                    set_status(
                        "Güncelleme doğrulandı. İzbul yeniden başlatılıyor...",
                        "#27AE60"
                    )
                    launch_macos_update(
                        target_file,
                        release_info.get("version", ""),
                    )
                    self.after(500, self.destroy)
                    return

                set_status(
                    "Güncelleme indirildi. Kurulum açılıyor...",
                    "#27AE60"
                )

                self.after(
                    500,
                    lambda:
                    self.open_downloaded_update(
                        target_file
                    )
                )

                self.after(
                    1600,
                    self.destroy
                )

            except Exception as e:

                logger.exception("Güncelleme indirilemedi")

                set_status(
                    "Güncelleme indirilemedi. Release sayfası açılıyor.",
                    "#C0392B"
                )

                self.after(
                    800,
                    lambda:
                    webbrowser.open(
                        release_url or GITHUB_RELEASES_URL
                    )
                )

        threading.Thread(
            target=run,
            daemon=True
        ).start()

        return True

    def show_update_prompt(self, release_info):

        if (
            self.update_prompt_window
            and self.update_prompt_window.winfo_exists()
        ):

            self.update_prompt_window.focus_force()

            return

        latest_version = release_info.get(
            "version",
            ""
        )

        update_window = ctk.CTkToplevel(self)
        self.update_prompt_window = update_window
        update_window.title("Güncelleme Mevcut")
        update_window.geometry("520x470")
        update_window.resizable(False, False)
        update_window.transient(self)
        update_window.focus_force()

        def close_update_window():

            self.update_prompt_window = None
            update_window.destroy()

        update_window.protocol(
            "WM_DELETE_WINDOW",
            close_update_window
        )

        container = ctk.CTkFrame(
            update_window,
            corner_radius=18
        )

        container.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=16
        )

        ctk.CTkLabel(
            container,
            text="Yeni sürüm mevcut",
            font=(
                "Arial",
                22,
                "bold"
            )
        ).pack(
            pady=(22, 8)
        )

        ctk.CTkLabel(
            container,
            text=(
                f"Kurulu sürüm: {APP_VERSION}\n"
                f"Yeni sürüm: {latest_version}\n\n"
                + (
                    "İzbul güvenli şekilde güncellenecek ve yeniden açılacak."
                    if sys.platform == "darwin"
                    and str(release_info.get("asset_name", "")).lower().endswith(".zip")
                    else "Güncelleme dosyası indirilecek ve kurulum açılacak."
                )
            ),
            justify="center",
            text_color="#D8DEE9",
            font=(
                "Arial",
                14
            )
        ).pack(
            padx=26,
            pady=(0, 10)
        )

        ctk.CTkLabel(
            container,
            text="Sürüm Notları",
            font=("Arial", 13, "bold"),
            anchor="w"
        ).pack(
            fill="x",
            padx=26,
            pady=(0, 5)
        )

        release_notes = str(
            release_info.get("release_notes", "")
            or "Bu sürüm için açıklama paylaşılmadı."
        )[:2500]

        notes_box = ctk.CTkTextbox(
            container,
            height=115,
            corner_radius=8,
            font=("Arial", 12),
            wrap="word"
        )
        notes_box.pack(
            fill="x",
            padx=24,
            pady=(0, 10)
        )
        notes_box.insert("1.0", release_notes)
        notes_box.configure(state="disabled")

        status_label = ctk.CTkLabel(
            container,
            text="",
            height=22,
            text_color="gray",
            font=(
                "Arial",
                12,
                "bold"
            )
        )

        status_label.pack(
            fill="x",
            padx=22,
            pady=(0, 10)
        )

        actions = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

        def set_status(message, color="#D8DEE9"):

            status_label.configure(
                text=message,
                text_color=color
            )

        def update_now():

            update_button.configure(
                state="disabled",
                text="İndiriliyor..."
            )

            continue_button.configure(
                state="disabled"
            )

            download_started = self.start_update_download(
                release_info,
                status_callback=set_status
            )

            if not download_started:

                update_button.configure(
                    state="normal",
                    text="Güncelle"
                )
                continue_button.configure(state="normal")

        continue_button = ctk.CTkButton(
            actions,
            text="Bu Sürümle Devam Et",
            height=40,
            fg_color="#3A3A3A",
            hover_color="#4A4A4A",
            command=close_update_window
        )

        continue_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        update_button = ctk.CTkButton(
            actions,
            text="Güncelle",
            height=40,
            fg_color="#2E8B57",
            hover_color="#247348",
            command=update_now
        )

        update_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(8, 0)
        )

    def handle_update_result(self, release_info, silent=False):

        self.update_check_in_progress = False

        latest_version = release_info.get(
            "version",
            ""
        )

        if latest_version and is_newer_version(
            latest_version,
            APP_VERSION
        ):

            self.latest_release_info = release_info

            self.show_update_prompt(
                release_info
            )

            return True

        self.latest_release_info = None

        if not silent:

            self.show_toast(
                "Uygulama güncel.",
                "#27AE60"
            )

        return False

    def handle_update_error(self, error, silent=False):

        self.update_check_in_progress = False

        logger.error("Güncelleme kontrolü başarısız: %s", error)

        if not silent:

            message = str(error).strip() or "Güncelleme kontrolü başarısız."

            self.show_toast(
                message,
                "#C0392B"
            )

    def check_for_updates(self, silent=False):

        if is_windows_store_install():

            self.latest_release_info = None
            self.update_check_in_progress = False

            if not silent:
                self.show_toast(
                    "Güncellemeler Microsoft Store tarafından yönetiliyor.",
                    "#27AE60"
                )

            return False

        if self.update_check_in_progress:

            return

        self.update_check_in_progress = True

        def run():

            try:

                release_info = self.get_latest_release()

                self.after(
                    0,
                    lambda:
                    self.handle_update_result(
                        release_info,
                        silent=silent
                    )
                )

            except Exception as e:

                self.after(
                    0,
                    lambda:
                    self.handle_update_error(
                        e,
                        silent=silent
                    )
                )

        threading.Thread(
            target=run,
            daemon=True
        ).start()
