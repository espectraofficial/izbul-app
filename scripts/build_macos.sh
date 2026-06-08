#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Izbul"
DISPLAY_NAME="İzbul"
APP_VERSION="1.0.0"
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
  --osx-bundle-identifier "com.umitegeguldez.izbul" \
  --collect-data customtkinter \
  --collect-data PIL \
  --workpath build/work \
  --specpath build/spec \
  --distpath dist \
  ui/app.py

/usr/libexec/PlistBuddy \
  -c "Set :CFBundleDisplayName $DISPLAY_NAME" \
  -c "Set :CFBundleName $DISPLAY_NAME" \
  -c "Set :CFBundleShortVersionString $APP_VERSION" \
  -c "Add :CFBundleVersion string $APP_VERSION" \
  "dist/$APP_NAME.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy \
  -c "Set :CFBundleDisplayName $DISPLAY_NAME" \
  -c "Set :CFBundleName $DISPLAY_NAME" \
  -c "Set :CFBundleShortVersionString $APP_VERSION" \
  -c "Set :CFBundleVersion $APP_VERSION" \
  "dist/$APP_NAME.app/Contents/Info.plist"

xattr -cr "dist/$APP_NAME.app" 2>/dev/null || true
codesign --force --deep --sign - "dist/$APP_NAME.app" 2>/dev/null || true

mkdir -p release/macos

if hdiutil create \
    -volname "$DISPLAY_NAME" \
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
