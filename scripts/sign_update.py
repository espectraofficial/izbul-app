#!/usr/bin/env python3
import argparse
import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def load_private_key(key_file=None):
    key_text = os.getenv("IZBUL_UPDATE_PRIVATE_KEY", "").strip()
    if key_text:
        key_data = key_text.replace("\\n", "\n").encode("ascii")
    elif key_file:
        key_data = Path(key_file).read_bytes()
    else:
        raise RuntimeError("Güncelleme özel anahtarı bulunamadı.")

    private_key = serialization.load_pem_private_key(key_data, password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("Güncelleme anahtarı Ed25519 türünde olmalı.")
    return private_key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()

    private_key = load_private_key(args.key_file)
    digest_builder = hashlib.sha256()
    with args.archive.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest_builder.update(chunk)
    digest = digest_builder.digest()
    signature = private_key.sign(digest)
    signature_file = args.archive.with_name(args.archive.name + ".sig")
    signature_file.write_text(
        base64.b64encode(signature).decode("ascii") + "\n",
        encoding="ascii",
    )
    print(f"Created {signature_file}")


if __name__ == "__main__":
    main()
