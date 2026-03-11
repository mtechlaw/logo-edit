from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

try:
    import cairosvg
except Exception:  # pragma: no cover
    cairosvg = None


DEFAULT_CANVAS_WIDTH = 356
DEFAULT_CANVAS_HEIGHT = 346


@dataclass
class LogoSettings:
    threshold: int = 245
    logo_scale: float = 0.62
    circle_margin: int = 12
    x_offset: int = 0
    y_offset: int = 0
    canvas_width: int = DEFAULT_CANVAS_WIDTH
    canvas_height: int = DEFAULT_CANVAS_HEIGHT


def _is_near_white(r: int, g: int, b: int, threshold: int) -> bool:
    return r >= threshold and g >= threshold and b >= threshold


def svg_bytes_to_rgba(svg_bytes: bytes, width: int = 1200, height: int = 1200) -> Image.Image:
    if cairosvg is None:
        raise RuntimeError("SVG support requires cairosvg. Install dependencies from requirements.txt.")
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def load_image_from_bytes(data: bytes, filename: str) -> Image.Image:
    suffix = Path(filename).suffix.lower()
    if suffix == ".svg":
        return svg_bytes_to_rgba(data)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def make_near_white_transparent(img: Image.Image, threshold: int = 245) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if _is_near_white(r, g, b, threshold):
                px[x, y] = (255, 255, 255, 0)
    return img


def trim_transparent_edges(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def resize_logo(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
    out = img.copy()
    out.thumbnail((max_width, max_height), Image.LANCZOS)
    return out


def create_badge_canvas(width: int, height: int, margin: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((margin, margin, width - margin, height - margin), fill=(255, 255, 255, 255))
    return canvas


def render_badge(img: Image.Image, settings: LogoSettings) -> Image.Image:
    cleaned = make_near_white_transparent(img, threshold=settings.threshold)
    cleaned = trim_transparent_edges(cleaned)

    max_dim = int(min(settings.canvas_width, settings.canvas_height) * settings.logo_scale)
    logo = resize_logo(cleaned, max_dim, max_dim)

    badge = create_badge_canvas(settings.canvas_width, settings.canvas_height, settings.circle_margin)
    x = (settings.canvas_width - logo.width) // 2 + settings.x_offset
    y = (settings.canvas_height - logo.height) // 2 + settings.y_offset
    badge.alpha_composite(logo, (x, y))
    return badge


def render_badge_from_bytes(data: bytes, filename: str, settings: LogoSettings) -> Image.Image:
    img = load_image_from_bytes(data, filename)
    return render_badge(img, settings)


def save_png(img: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")
    return path


def batch_zip(rendered_images: list[tuple[str, Image.Image]], zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, img in rendered_images:
            stem = Path(filename).stem
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            zf.writestr(f"{stem}_branded.png", buf.getvalue())
    return zip_path
