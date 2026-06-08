#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Izbul"
DISPLAY_NAME="İzbul"
DMG_VOLUME_NAME="Izbul"
APP_VERSION="1.0.0"
DMG_NAME="Izbul-macOS.dmg"
DMG_RW_NAME="Izbul-macOS-rw.dmg"
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
rm -rf build/dmg
mkdir -p build/dmg/.background
cp -R "dist/$APP_NAME.app" "build/dmg/$APP_NAME.app"
ln -s /Applications "build/dmg/Applications"

python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

width, height = 720, 440
background = Image.new("RGBA", (width, height), "#071827")
draw = ImageDraw.Draw(background)

for y in range(height):
    ratio = y / max(1, height - 1)
    r = int(8 + 2 * ratio)
    g = int(34 + 20 * ratio)
    b = int(55 + 36 * ratio)
    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)
glow_draw.ellipse((70, -80, 360, 210), fill=(0, 190, 210, 55))
glow_draw.ellipse((420, 210, 780, 560), fill=(255, 178, 45, 35))
background = Image.alpha_composite(background, glow.filter(ImageFilter.GaussianBlur(45)))
draw = ImageDraw.Draw(background)

def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

title_font = load_font(30, bold=True)
body_font = load_font(15)
small_font = load_font(13)

title = "İzbul"
subtitle = "Kurmak için uygulamayı Applications klasörüne sürükleyin."

title_box = draw.textbbox((0, 0), title, font=title_font)
subtitle_box = draw.textbbox((0, 0), subtitle, font=body_font)
draw.text(((width - (title_box[2] - title_box[0])) / 2, 42), title, font=title_font, fill=(245, 250, 255, 255))
draw.text(((width - (subtitle_box[2] - subtitle_box[0])) / 2, 82), subtitle, font=body_font, fill=(190, 211, 222, 255))

card = Image.new("RGBA", (560, 210), (255, 255, 255, 0))
card_draw = ImageDraw.Draw(card)
card_draw.rounded_rectangle((0, 0, 560, 210), radius=26, fill=(255, 255, 255, 22), outline=(255, 255, 255, 42), width=1)
background.alpha_composite(card, (80, 145))

draw = ImageDraw.Draw(background)

arrow_y = 250
draw.line((285, arrow_y, 435, arrow_y), fill=(80, 220, 230, 210), width=7)
draw.polygon([(435, arrow_y), (408, arrow_y - 18), (408, arrow_y + 18)], fill=(80, 220, 230, 230))
draw.line((285, arrow_y + 18, 435, arrow_y + 18), fill=(255, 180, 38, 130), width=2)

left_label = "1. İzbul"
right_label = "2. Applications"
hint = "Sürükle ve bırak"
left_box = draw.textbbox((0, 0), left_label, font=small_font)
right_box = draw.textbbox((0, 0), right_label, font=small_font)
hint_box = draw.textbbox((0, 0), hint, font=small_font)
draw.text((178 - (left_box[2] - left_box[0]) / 2, 328), left_label, font=small_font, fill=(220, 235, 242, 230))
draw.text((542 - (right_box[2] - right_box[0]) / 2, 328), right_label, font=small_font, fill=(220, 235, 242, 230))
draw.text(((width - (hint_box[2] - hint_box[0])) / 2, 282), hint, font=small_font, fill=(255, 200, 75, 230))

background.save("build/dmg/.background/background.png")
PY

create_basic_dmg() {
  hdiutil create \
    -volname "$DMG_VOLUME_NAME" \
    -srcfolder "build/dmg" \
    -ov \
    -format UDZO \
    "release/macos/$DMG_NAME"
}

DMG_CREATED=false

if hdiutil create \
    -volname "$DMG_VOLUME_NAME" \
    -srcfolder "build/dmg" \
    -ov \
    -format UDRW \
    "build/$DMG_RW_NAME"; then

  MOUNT_OUTPUT=$(
    hdiutil attach \
      "build/$DMG_RW_NAME" \
      -readwrite \
      -noverify \
      -noautoopen
  )

  MOUNT_POINT=$(
    printf "%s\n" "$MOUNT_OUTPUT" |
    awk '/\/Volumes\// {for (i=3; i<=NF; i++) {printf $i; if (i<NF) printf " "}; print ""; exit}'
  )

  osascript <<APPLESCRIPT || true
tell application "Finder"
  tell disk "$DMG_VOLUME_NAME"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {120, 120, 840, 560}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 104
    set background picture of viewOptions to (POSIX file "$MOUNT_POINT/.background/background.png" as alias)
    set position of item "$APP_NAME.app" of container window to {178, 248}
    set position of item "Applications" of container window to {542, 248}
    update without registering applications
    delay 1
    close
  end tell
end tell
APPLESCRIPT

  sync
  hdiutil detach "$MOUNT_POINT"

  hdiutil convert \
    "build/$DMG_RW_NAME" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -ov \
    -o "release/macos/$DMG_NAME"

  DMG_CREATED=true

fi

if [ "$DMG_CREATED" = true ]; then

  echo "Created release/macos/$DMG_NAME"

else

  create_basic_dmg || {

    ZIP_NAME="Izbul-macOS.zip"

    ditto \
      -c \
      -k \
      --keepParent \
      "dist/$APP_NAME.app" \
      "release/macos/$ZIP_NAME"

    echo "DMG creation failed. Created release/macos/$ZIP_NAME instead."
  }

fi
