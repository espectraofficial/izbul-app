#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Izbul"
DISPLAY_NAME="İzbul"
DMG_VOLUME_NAME="Izbul"
APP_VERSION="1.0.1"
DMG_NAME="Izbul-macOS.dmg"
DMG_RW_NAME="Izbul-macOS-rw.dmg"
PYINSTALLER_CONFIG_DIR="$PWD/build/pyinstaller-cache"
ICON_PATH="$PWD/icon.icns"
ENTITLEMENTS_PATH="$PWD/packaging/macos/entitlements.plist"
MACOS_CODESIGN_IDENTITY="${MACOS_CODESIGN_IDENTITY:-}"
MACOS_NOTARY_PROFILE="${MACOS_NOTARY_PROFILE:-}"
export PYINSTALLER_CONFIG_DIR

detect_codesign_identity() {
  if [ -n "$MACOS_CODESIGN_IDENTITY" ]; then
    return
  fi

  MACOS_CODESIGN_IDENTITY=$(
    security find-identity -v -p codesigning |
    awk -F '"' '/Developer ID Application/ {print $2; exit}'
  )
}

sign_app_bundle() {
  detect_codesign_identity

  if [ -n "$MACOS_CODESIGN_IDENTITY" ]; then
    echo "Signing with Developer ID identity: $MACOS_CODESIGN_IDENTITY"

    codesign \
      --force \
      --deep \
      --timestamp \
      --options runtime \
      --entitlements "$ENTITLEMENTS_PATH" \
      --sign "$MACOS_CODESIGN_IDENTITY" \
      "dist/$APP_NAME.app"
  else
    echo "Developer ID certificate was not found. Using ad-hoc signing."

    codesign \
      --force \
      --deep \
      --sign - \
      "dist/$APP_NAME.app"
  fi

  codesign \
    --verify \
    --deep \
    --strict \
    --verbose=2 \
    "dist/$APP_NAME.app"
}

notarize_dmg_if_configured() {
  if [ -z "$MACOS_NOTARY_PROFILE" ]; then
    echo "Notarization skipped. Set MACOS_NOTARY_PROFILE to enable it."
    return
  fi

  if [ -z "$MACOS_CODESIGN_IDENTITY" ]; then
    echo "Notarization skipped because no Developer ID certificate was found."
    return
  fi

  echo "Submitting DMG for notarization with profile: $MACOS_NOTARY_PROFILE"

  xcrun notarytool submit \
    "release/macos/$DMG_NAME" \
    --keychain-profile "$MACOS_NOTARY_PROFILE" \
    --wait

  xcrun stapler staple \
    "release/macos/$DMG_NAME"

  xcrun stapler validate \
    "release/macos/$DMG_NAME"
}

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
sign_app_bundle

mkdir -p release/macos
rm -rf build/dmg
mkdir -p build/dmg/.background
cp -R "dist/$APP_NAME.app" "build/dmg/$APP_NAME.app"
ln -s /Applications "build/dmg/Applications"

python3 - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

scale = 2
width, height = 900, 560
canvas_width, canvas_height = width * scale, height * scale
background = Image.new("RGBA", (canvas_width, canvas_height), "#071827")
draw = ImageDraw.Draw(background)

for y in range(canvas_height):
    ratio = y / max(1, canvas_height - 1)
    r = int(8 + 2 * ratio)
    g = int(34 + 20 * ratio)
    b = int(55 + 36 * ratio)
    draw.line([(0, y), (canvas_width, y)], fill=(r, g, b, 255))

glow = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)
glow_draw.ellipse((80 * scale, -110 * scale, 470 * scale, 275 * scale), fill=(0, 190, 210, 58))
glow_draw.ellipse((560 * scale, 245 * scale, 1010 * scale, 650 * scale), fill=(255, 178, 45, 42))
glow_draw.ellipse((350 * scale, 150 * scale, 670 * scale, 450 * scale), fill=(38, 105, 255, 30))
background = Image.alpha_composite(background, glow.filter(ImageFilter.GaussianBlur(58 * scale)))
draw = ImageDraw.Draw(background)

def load_font(size, bold=False):
    size *= scale
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

title_font = load_font(34, bold=True)
body_font = load_font(17)
small_font = load_font(14, bold=True)
caption_font = load_font(13)

title = "İzbul"
subtitle = "Kurulum için İzbul simgesini Applications klasörüne sürükleyin."

title_box = draw.textbbox((0, 0), title, font=title_font)
subtitle_box = draw.textbbox((0, 0), subtitle, font=body_font)
draw.text(((canvas_width - (title_box[2] - title_box[0])) / 2, 44 * scale), title, font=title_font, fill=(245, 250, 255, 255))
draw.text(((canvas_width - (subtitle_box[2] - subtitle_box[0])) / 2, 92 * scale), subtitle, font=body_font, fill=(202, 222, 232, 255))

draw = ImageDraw.Draw(background)

panel_x1, panel_y1 = 78 * scale, 138 * scale
panel_x2, panel_y2 = 822 * scale, 454 * scale
draw.rounded_rectangle(
    (panel_x1, panel_y1, panel_x2, panel_y2),
    radius=34 * scale,
    fill=(18, 48, 68, 255),
    outline=(72, 128, 150, 255),
    width=2 * scale
)

left_center = (250 * scale, 290 * scale)
right_center = (650 * scale, 290 * scale)
target_radius = 108 * scale

for center, tint in [
    (left_center, (10, 113, 134, 255)),
    (right_center, (124, 88, 24, 255))
]:
    cx, cy = center
    draw.rounded_rectangle(
        (
            cx - target_radius,
            cy - target_radius,
            cx + target_radius,
            cy + target_radius
        ),
        radius=32 * scale,
        fill=tint,
        outline=(142, 221, 230, 255),
        width=2 * scale
    )
    draw.rounded_rectangle(
        (
            cx - (target_radius - 14 * scale),
            cy - (target_radius - 14 * scale),
            cx + (target_radius - 14 * scale),
            cy + (target_radius - 14 * scale)
        ),
        radius=24 * scale,
        outline=(222, 242, 247, 90),
        width=1 * scale
    )

arrow_y = 290 * scale
draw.line((382 * scale, arrow_y, 518 * scale, arrow_y), fill=(88, 225, 232, 235), width=9 * scale)
draw.polygon(
    [
        (530 * scale, arrow_y),
        (502 * scale, arrow_y - 22 * scale),
        (502 * scale, arrow_y + 22 * scale)
    ],
    fill=(88, 225, 232, 245)
)
draw.line((382 * scale, arrow_y + 22 * scale, 518 * scale, arrow_y + 22 * scale), fill=(255, 190, 60, 150), width=2 * scale)

step_left = "1"
step_right = "2"
hint = "Sürükle ve bırak"
caption = "Uygulamayı kopyaladıktan sonra Applications klasöründen açın."
left_box = draw.textbbox((0, 0), step_left, font=small_font)
right_box = draw.textbbox((0, 0), step_right, font=small_font)
hint_box = draw.textbbox((0, 0), hint, font=small_font)
caption_box = draw.textbbox((0, 0), caption, font=caption_font)
for center, text, box in [
    (left_center, step_left, left_box),
    (right_center, step_right, right_box)
]:
    cx, cy = center
    badge_size = 28 * scale
    draw.ellipse(
        (cx - 96 * scale, cy - 104 * scale, cx - 96 * scale + badge_size, cy - 104 * scale + badge_size),
        fill=(255, 190, 60, 230)
    )
    draw.text(
        (
            cx - 96 * scale + (badge_size - (box[2] - box[0])) / 2,
            cy - 104 * scale + (badge_size - (box[3] - box[1])) / 2 - 1 * scale
        ),
        text,
        font=small_font,
        fill=(8, 25, 39, 255)
    )

draw.text(((canvas_width - (hint_box[2] - hint_box[0])) / 2, 338 * scale), hint, font=small_font, fill=(255, 206, 82, 255))
draw.text(((canvas_width - (caption_box[2] - caption_box[0])) / 2, 500 * scale), caption, font=caption_font, fill=(185, 210, 222, 235))

final = background.resize((width, height), Image.Resampling.LANCZOS)
final.save("build/dmg/.background/background.png")
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
    set the bounds of container window to {120, 120, 1020, 680}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 128
    set background picture of viewOptions to (POSIX file "$MOUNT_POINT/.background/background.png" as alias)
    set position of item "$APP_NAME.app" of container window to {250, 290}
    set position of item "Applications" of container window to {650, 290}
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
  notarize_dmg_if_configured

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

  if [ -f "release/macos/$DMG_NAME" ]; then
    notarize_dmg_if_configured
  fi

fi

for artifact in \
  "release/macos/$DMG_NAME" \
  "release/macos/${ZIP_NAME:-Izbul-macOS.zip}"
do
  if [ -f "$artifact" ]; then
    artifact_dir="$(dirname "$artifact")"
    artifact_name="$(basename "$artifact")"
    (
      cd "$artifact_dir"
      shasum -a 256 "$artifact_name" > "$artifact_name.sha256"
    )
    echo "Created $artifact.sha256"
  fi
done
