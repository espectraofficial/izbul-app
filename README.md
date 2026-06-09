# İzbul

İzbul is a desktop job search app built with Python and CustomTkinter.

The app searches job listings, displays them in a single interface, supports filters, pagination, favorites, and external LinkedIn job search links.

## Ownership

İzbul was created by **Ümit Ege Güldez**.

© 2026 Ümit Ege Güldez. Tüm hakları saklıdır.

Bu projenin kaynak kodu, tasarımı, uygulama adı ve dağıtım paketleri Ümit Ege Güldez'e aittir. Yazılı izin olmadan kopyalanamaz, değiştirilemez, yeniden dağıtılamaz, satılamaz veya başka bir kişi/kurum tarafından sahiplenilemez.

All rights reserved. No part of this project may be copied, modified, redistributed, sold, sublicensed, or claimed as another person's or organization's work without prior written permission from Ümit Ege Güldez.

See [NOTICE.md](NOTICE.md) for third-party source, trademark, and dependency notices.

## Current Sources

- Kariyer.net
- Jooble, when a Jooble API key is provided
- Eleman.net
- LinkedIn Jobs external search link

Kariyer.net search results are obtained through a JSON search endpoint used by Kariyer.net's public web search flow. This does not imply an official partnership, endorsement, sponsorship, or authorization by Kariyer.net. See [NOTICE.md](NOTICE.md) for details.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Jooble API Key

Jooble is optional. The app works without it and skips Jooble results.

You can provide the API key with an environment variable:

```bash
export JOOBLE_API_KEY=your_api_key
python ui/app.py
```

Or create a local `jooble_api_key.txt` file in the project root and put only the API key inside it.

The default Jooble endpoint is `tr.jooble.org`, which is used for Turkey-based API keys. If Jooble gives you a different regional endpoint, you can override it:

```bash
export JOOBLE_API_HOST=jooble.org
```

## Run

```bash
python ui/app.py
```

## Packaging

The project is packaged separately on macOS and Windows. Use the generated files under `release/` for distribution.

- App name: `İzbul`
- Version: `1.0.0`
- Creator / Publisher: `Ümit Ege Güldez`
- macOS bundle identifier: `com.umitegeguldez.izbul`
- Technical bundle / executable name: `Izbul`

- macOS builds should be created on macOS.
- Windows builds should be created on Windows.

macOS:

```bash
bash scripts/build_macos.sh
```

macOS signing and notarization:

For local test builds, the script falls back to ad-hoc signing when a
Developer ID certificate is not installed.

For public distribution outside the Mac App Store, install a
`Developer ID Application` certificate in Keychain Access, then store
notary credentials once:

```bash
xcrun notarytool store-credentials "izbul-notary"
```

Then build with notarization enabled:

```bash
export MACOS_NOTARY_PROFILE="izbul-notary"
bash scripts/build_macos.sh
```

If multiple Developer ID certificates exist, choose one explicitly:

```bash
export MACOS_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export MACOS_NOTARY_PROFILE="izbul-notary"
bash scripts/build_macos.sh
```

Windows PowerShell:

```powershell
.\scripts\build_windows.ps1
```

Build outputs are created under `dist/`.

Distribution outputs:

- macOS: `release/macos/Izbul-macOS.dmg`
- macOS fallback: `release/macos/Izbul-macOS.zip`
- Windows: `release/windows/Izbul-Windows-Setup.exe`

GitHub Actions can build both installers from the **Build Installers** workflow. Run it manually from the Actions tab, then download the generated artifacts.

## Updates

İzbul checks the latest GitHub Release on startup and from the Settings screen.

Use semantic release tags such as `v1.0.0`, `v1.1.0`, and attach the generated
macOS / Windows installer files to each release.
