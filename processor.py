from __future__ import annotations

import io
import zipfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

try:
    import cairosvg
except Exception:  # pragma: no cover
    cairosvg = None


CANVAS_WIDTH = 356
CANVAS_HEIGHT = 346
CIRCLE_DIAMETER = 346  # exact circle inside 356x346 canvas
SIDE_PADDING = (CANVAS_WIDTH - CIRCLE_DIAMETER) // 2  # 5 px


@dataclass
class LogoSettings:
    threshold: int = 245
    logo_scale: float = 0.46
    x_offset: int = 0
    y_offset: int = 0
    bg_color: tuple[int, int, int, int] = (255, 255, 255, 255)


def svg_bytes_to_rgba(svg_bytes: bytes, width: int = 1400, height: int = 1400) -> Image.Image:
    if cairosvg is None:
        raise RuntimeError("SVG support requires cairosvg. Install dependencies from requirements.txt.")
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def load_image_from_bytes(data: bytes, filename: str) -> Image.Image:
    suffix = Path(filename).suffix.lower()
    if suffix == ".svg":
        return svg_bytes_to_rgba(data)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def is_near_white(pixel: tuple[int, int, int, int], threshold: int) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= threshold and g >= threshold and b >= threshold


def remove_corner_connected_background(img: Image.Image, threshold: int = 245) -> Image.Image:
    """
    Removes only the near-white background that is connected to the image edges.
    This avoids deleting white details that are part of the logo itself.
    """
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    visited = [[False] * w for _ in range(h)]
    q = deque()

    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))

    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_near_white(px[x, y], threshold):
            continue

        px[x, y] = (255, 255, 255, 0)

        q.append((x + 1, y))
        q.append((x - 1, y))
        q.append((x, y + 1))
        q.append((x, y - 1))

    return img


def trim_transparent_edges(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def resize_logo(img: Image.Image, logo_scale: float) -> Image.Image:
    max_box = int(CIRCLE_DIAMETER * logo_scale)
    out = img.copy()
    out.thumbnail((max_box, max_box), Image.LANCZOS)
    return out


def create_exact_circle_badge(bg_color=(255, 255, 255, 255)) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    left = SIDE_PADDING
    top = 0
    right = SIDE_PADDING + CIRCLE_DIAMETER
    bottom = CIRCLE_DIAMETER
    draw.ellipse((left, top, right, bottom), fill=bg_color)
    return canvas


def render_badge_from_bytes(data: bytes, filename: str, settings: LogoSettings) -> Image.Image:
    img = load_image_from_bytes(data, filename)
    img = remove_corner_connected_background(img, threshold=settings.threshold)
    img = trim_transparent_edges(img)
    img = resize_logo(img, settings.logo_scale)

    badge = create_exact_circle_badge(bg_color=settings.bg_color)
    x = (CANVAS_WIDTH - img.width) // 2 + settings.x_offset
    y = (CANVAS_HEIGHT - img.height) // 2 + settings.y_offset
    badge.alpha_composite(img, (x, y))
    return badge


def batch_zip(rendered_images: list[tuple[str, Image.Image]], zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, img in rendered_images:
            stem = Path(filename).stem
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            zf.writestr(f"{stem}_branded.png", buf.getvalue())
    return zip_path
