from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

from scripts.generate_msix_assets import ASSET_SIZES, generate_assets


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAMESPACE = {
    "appx": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
}


def test_msix_manifest_matches_store_product_identity():
    manifest_path = (
        ROOT / "packaging" / "windows" / "AppxManifest.xml.template"
    )
    manifest = ElementTree.parse(manifest_path)
    identity = manifest.getroot().find("appx:Identity", MANIFEST_NAMESPACE)
    properties = manifest.getroot().find("appx:Properties", MANIFEST_NAMESPACE)

    assert identity is not None
    assert identity.attrib["Name"] == "Espectra.zbul"
    assert identity.attrib["Publisher"] == (
        "CN=05C69FDA-2F64-49D6-BDFC-D4FA004663E4"
    )
    assert identity.attrib["Version"] == "__MSIX_VERSION__"
    assert properties is not None
    assert properties.findtext(
        "appx:PublisherDisplayName",
        namespaces=MANIFEST_NAMESPACE
    ) == "Espectra"


def test_msix_assets_have_manifest_dimensions(tmp_path):
    output_dir = tmp_path / "Assets"
    generate_assets(ROOT / "icon.png", output_dir)

    for file_name, expected_size in ASSET_SIZES.items():
        with Image.open(output_dir / file_name) as image:
            assert image.size == expected_size
            assert image.mode == "RGBA"


def test_windows_build_creates_store_msix_and_checksum():
    build_script = (ROOT / "scripts" / "build_windows.ps1").read_text(
        encoding="utf-8"
    )

    assert "AppxManifest.xml.template" in build_script
    assert "generate_msix_assets.py" in build_script
    assert "MakeAppx.exe" in build_script
    assert "Izbul-Windows-Store.msix" in build_script
    assert '".msix"' in build_script
