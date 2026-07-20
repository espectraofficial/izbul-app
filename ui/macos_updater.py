import base64
import hashlib
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from ui.config import APP_VERSION
from ui.storage import get_app_data_dir
from ui.versioning import is_newer_version


BUNDLE_IDENTIFIER = "com.umitegeguldez.izbul"
PUBLIC_KEY_FILE = "update_public_key.txt"


def get_public_key_file():
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundled_key = Path(bundle_dir) / PUBLIC_KEY_FILE
        if bundled_key.exists():
            return bundled_key

    return Path(__file__).resolve().parent.parent / "packaging" / PUBLIC_KEY_FILE


def verify_update_signature(archive_path, signature_text, public_key_file=None):
    archive_path = Path(archive_path)
    public_key_file = Path(public_key_file or get_public_key_file())

    try:
        public_key_bytes = base64.b64decode(
            public_key_file.read_text(encoding="ascii").strip(),
            validate=True,
        )
        signature = base64.b64decode(
            str(signature_text or "").strip(),
            validate=True,
        )
    except (OSError, ValueError) as error:
        raise ValueError("Güncelleme imza bilgisi okunamadı.") from error

    if len(public_key_bytes) != 32:
        raise ValueError("Güncelleme açık anahtarı geçersiz.")

    digest_builder = hashlib.sha256()
    with archive_path.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest_builder.update(chunk)
    digest = digest_builder.digest()

    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature,
            digest,
        )
    except InvalidSignature as error:
        raise ValueError("Güncelleme dijital imzası doğrulanamadı.") from error

    return True


def find_running_app_bundle(executable=None):
    executable = Path(executable or sys.executable).resolve()

    for candidate in (executable, *executable.parents):
        if candidate.suffix.lower() == ".app":
            return candidate

    return None


def extract_and_validate_update(archive_path, expected_version):
    archive_path = Path(archive_path).resolve()
    update_root = get_app_data_dir() / "updates"
    update_root.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix="staged-", dir=update_root))

    try:
        subprocess.run(
            ["/usr/bin/ditto", "-x", "-k", str(archive_path), str(staging_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        app_candidates = [
            path for path in staging_dir.iterdir()
            if path.is_dir() and path.suffix.lower() == ".app"
        ]
        if len(app_candidates) != 1:
            raise ValueError("Güncelleme arşivinde tek bir uygulama bulunmalı.")

        app_bundle = app_candidates[0]
        info_plist = app_bundle / "Contents" / "Info.plist"
        executable_dir = app_bundle / "Contents" / "MacOS"

        with info_plist.open("rb") as file:
            metadata = plistlib.load(file)

        bundle_identifier = str(metadata.get("CFBundleIdentifier", ""))
        bundle_version = str(metadata.get("CFBundleShortVersionString", ""))

        if bundle_identifier != BUNDLE_IDENTIFIER:
            raise ValueError("Güncelleme farklı bir uygulamaya ait.")
        if bundle_version != str(expected_version).lstrip("v"):
            raise ValueError("Güncelleme sürümü release bilgisiyle eşleşmiyor.")
        if not is_newer_version(bundle_version, APP_VERSION):
            raise ValueError("Güncelleme kurulu sürümden daha yeni değil.")
        if not executable_dir.is_dir() or not any(executable_dir.iterdir()):
            raise ValueError("Güncelleme uygulaması çalıştırılabilir dosya içermiyor.")

        subprocess.run(
            [
                "/usr/bin/codesign",
                "--verify",
                "--deep",
                "--strict",
                str(app_bundle),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return staging_dir, app_bundle

    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def create_update_helper(target_app, staged_app, archive_path):
    update_root = get_app_data_dir() / "updates"
    update_root.mkdir(parents=True, exist_ok=True)
    fd, helper_name = tempfile.mkstemp(
        prefix="install-update-",
        suffix=".sh",
        dir=update_root,
        text=True,
    )
    helper_path = Path(helper_name)
    script = """#!/bin/sh
set -eu

pid="$1"
target="$2"
staged="$3"
staging_root="$4"
archive="$5"
backup="${target}.izbul-update-backup"
incoming="${target}.izbul-update-new"

while kill -0 "$pid" 2>/dev/null; do
  sleep 0.2
done

rm -rf "$backup" "$incoming"
/usr/bin/ditto "$staged" "$incoming"

if ! mv "$target" "$backup"; then
  rm -rf "$incoming"
  /usr/bin/open "$target"
  exit 1
fi

if mv "$incoming" "$target"; then
  /usr/bin/open "$target"
  rm -rf "$backup" "$staging_root" "$archive" "$0"
  exit 0
fi

rm -rf "$incoming"
mv "$backup" "$target"
/usr/bin/open "$target"
exit 1
"""

    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(script)

    helper_path.chmod(0o700)
    return helper_path


def launch_macos_update(archive_path, expected_version, executable=None):
    if sys.platform != "darwin":
        raise RuntimeError("Uygulama içi paket değişimi yalnızca macOS'ta kullanılabilir.")

    target_app = find_running_app_bundle(executable)
    if target_app is None:
        raise RuntimeError("Çalışan İzbul uygulama paketi bulunamadı.")
    if str(target_app).startswith("/Volumes/"):
        raise RuntimeError("Güncelleme için İzbul'u Applications klasöründen açın.")
    if not os.access(target_app.parent, os.W_OK):
        raise PermissionError("Uygulamanın bulunduğu klasöre yazma izni yok.")

    staging_dir, staged_app = extract_and_validate_update(
        archive_path,
        expected_version,
    )
    helper_path = create_update_helper(
        target_app,
        staged_app,
        archive_path,
    )
    log_file = (get_app_data_dir() / "updates" / "update.log").open(
        "ab",
        buffering=0,
    )

    subprocess.Popen(
        [
            "/bin/sh",
            str(helper_path),
            str(os.getpid()),
            str(target_app),
            str(staged_app),
            str(staging_dir),
            str(Path(archive_path).resolve()),
        ],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    log_file.close()
    return True
