# Job Finder

Job Finder is a desktop job search app built with Python and CustomTkinter.

The app searches job listings, displays them in a single interface, supports filters, pagination, favorites, and external LinkedIn job search links.

## Current Sources

- Kariyer.net
- Jooble, when a Jooble API key is provided
- LinkedIn Jobs external search link

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

- macOS builds should be created on macOS.
- Windows builds should be created on Windows.

macOS:

```bash
bash scripts/build_macos.sh
```

Windows PowerShell:

```powershell
.\scripts\build_windows.ps1
```

Build outputs are created under `dist/`.

Distribution outputs:

- macOS: `release/macos/Job-Finder-macOS.dmg`
- macOS fallback: `release/macos/Job-Finder-macOS.zip`
- Windows: `release/windows/Job-Finder-Windows-Setup.exe`

GitHub Actions can build both installers from the **Build Installers** workflow. Run it manually from the Actions tab, then download the generated artifacts.
