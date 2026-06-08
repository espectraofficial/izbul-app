#!/usr/bin/env bash
set -euo pipefail

APP_NAME="İzbul"
DMG_NAME="Izbul-macOS.dmg"
PYINSTALLER_CONFIG_DIR="$PWD/build/pyinstaller-cache"
ICON_PATH="$PWD/icon.icns"
export PYINSTALLER_CONFIG_DIR

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

rm -rf build dist release/macos
mkdir -p build/spec "$PYINSTALLER_CONFIG_DIR"

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --icon "$ICON_PATH" \
  --collect-data customtkinter \
  --collect-data PIL \
  --workpath build/work \
  --specpath build/spec \
  --distpath dist \
  ui/app.py

mkdir -p release/macos

if hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "dist/$APP_NAME.app" \
    -ov \
    -format UDZO \
    "release/macos/$DMG_NAME"; then

  echo "Created release/macos/$DMG_NAME"

else

  ZIP_NAME="Izbul-macOS.zip"

  ditto \
    -c \
    -k \
    --keepParent \
    "dist/$APP_NAME.app" \
    "release/macos/$ZIP_NAME"

  echo "DMG creation failed. Created release/macos/$ZIP_NAME instead."

fi
