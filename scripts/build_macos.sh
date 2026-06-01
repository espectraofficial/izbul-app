#!/usr/bin/env bash
set -euo pipefail

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pyinstaller \
  --windowed \
  --name "Job Finder" \
  --icon icon.icns \
  ui/app.py
