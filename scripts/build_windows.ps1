$ErrorActionPreference = "Stop"

py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

pyinstaller `
  --windowed `
  --name "Job Finder" `
  --icon icon.ico `
  ui/app.py
