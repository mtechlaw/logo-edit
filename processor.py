from __future__ import annotations

import io
import math
import zipfile
from pathlib import Path
from typing import Iterable, Tuple

from PIL import Image, ImageChops, ImageDraw


CANVAS_SIZE = (356, 346)
CIRCLE_MARGIN = 12
LOGO_SCALE = 0.62  # fraction of the smallest canvas dimension


def load_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    return img


def make_near_white_transparent(img: Image.Image, threshold: int = 245) -> Image.Image:
    """
    Makes near-white pixels transparent.
    Useful for logos exported on plain white backgrounds.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (255, 255, 255, 0)
    return img


def trim_transparent_edges(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def resize_logo(img: Image.Image, max_box: Tuple[int, int]) -> Image.Image:
    img = img.copy()
    img.thumbnail(max_box, Image.LANCZOS)
    return img


def create_white_circle_canvas(size: Tuple[int, int] = CANVAS_SIZE, margin: int = CIRCLE_MARGIN) -> Image.Image:
    canvas = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)

    left = margin
    top = margin
    right = size[0] - margin
    bottom = size[1] - margin

    draw.ellipse((left, top, right, bottom), fill=(255, 255, 255, 255))
    return canvas


def center_paste(base: Image.Image, overlay: Image.Image) -> Image.Image:
    x = (base.width - overlay.width) // 2
    y = (base.height - overlay.height) // 2
    result = base.copy()
    result.alpha_composite(overlay, (x, y))
    return result


def process_logo(
    input_path: Path,
    output_path: Path,
    threshold: int = 245,
    canvas_size: Tuple[int, int] = CANVAS_SIZE,
    circle_margin: int = CIRCLE_MARGIN,
    logo_scale: float = LOGO_SCALE,
) -> Path:
    img = load_image(input_path)
    img = make_near_white_transparent(img, threshold=threshold)
    img = trim_transparent_edges(img)

    max_dim = int(min(canvas_size) * logo_scale)
    logo = resize_logo(img, (max_dim, max_dim))

    base = create_white_circle_canvas(canvas_size, margin=circle_margin)
    final = center_paste(base, logo)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, "PNG")
    return output_path


def batch_process(
    input_dir: Path,
    output_dir: Path,
    threshold: int = 245,
    canvas_size: Tuple[int, int] = CANVAS_SIZE,
    circle_margin: int = CIRCLE_MARGIN,
    logo_scale: float = LOGO_SCALE,
) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    files = [p for p in input_dir.iterdir() if p.suffix.lower() in exts and p.is_file()]

    outputs = []
    for file in files:
        out = output_dir / f"{file.stem}_branded.png"
        outputs.append(
            process_logo(
                file,
                out,
                threshold=threshold,
                canvas_size=canvas_size,
                circle_margin=circle_margin,
                logo_scale=logo_scale,
            )
        )
    return outputs


def zip_outputs(output_dir: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(output_dir.glob("*.png")):
            zf.write(file, arcname=file.name)
    return zip_path
