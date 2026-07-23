import argparse
from pathlib import Path

from PIL import Image


ASSET_SIZES = {
    "StoreLogo.png": (50, 50),
    "Square44x44Logo.png": (44, 44),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
    "Square310x310Logo.png": (310, 310),
}


def generate_assets(source_path, output_dir):
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as source:
        icon = source.convert("RGBA")

        for file_name, canvas_size in ASSET_SIZES.items():
            canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            padding_ratio = 0.08 if canvas_size[0] == canvas_size[1] else 0.12
            max_width = int(canvas_size[0] * (1 - 2 * padding_ratio))
            max_height = int(canvas_size[1] * (1 - 2 * padding_ratio))
            fitted = icon.copy()
            fitted.thumbnail(
                (max_width, max_height),
                Image.Resampling.LANCZOS
            )
            position = (
                (canvas_size[0] - fitted.width) // 2,
                (canvas_size[1] - fitted.height) // 2,
            )
            canvas.alpha_composite(fitted, position)
            canvas.save(output_dir / file_name, format="PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Microsoft Store visual assets from the İzbul icon."
    )
    parser.add_argument("source", help="Source PNG icon")
    parser.add_argument("output", help="Output Assets directory")
    args = parser.parse_args()
    generate_assets(args.source, args.output)


if __name__ == "__main__":
    main()
