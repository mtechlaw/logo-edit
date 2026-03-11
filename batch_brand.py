from __future__ import annotations

import argparse
from pathlib import Path

from processor import LogoSettings, batch_zip, load_image_from_bytes, render_badge, save_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-brand logos into white-circle PNG badges.")
    parser.add_argument("input_dir", help="Folder containing source logo files")
    parser.add_argument("output_dir", help="Folder to write branded PNG files")
    parser.add_argument("--threshold", type=int, default=245)
    parser.add_argument("--logo-scale", type=float, default=0.62)
    parser.add_argument("--circle-margin", type=int, default=12)
    parser.add_argument("--x-offset", type=int, default=0)
    parser.add_argument("--y-offset", type=int, default=0)
    parser.add_argument("--zip", action="store_true", help="Create branded_logos.zip")
    args = parser.parse_args()

    settings = LogoSettings(
        threshold=args.threshold,
        logo_scale=args.logo_scale,
        circle_margin=args.circle_margin,
        x_offset=args.x_offset,
        y_offset=args.y_offset,
    )

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    supported = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
    rendered = []

    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in supported:
            img = load_image_from_bytes(path.read_bytes(), path.name)
            branded = render_badge(img, settings)
            out_path = output_dir / f"{path.stem}_branded.png"
            save_png(branded, out_path)
            rendered.append((path.name, branded))
            print(f"Created {out_path.name}")

    if args.zip and rendered:
        zip_path = output_dir / "branded_logos.zip"
        batch_zip(rendered, zip_path)
        print(f"Created {zip_path.name}")


if __name__ == "__main__":
    main()
