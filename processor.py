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
CIRCLE_DIAMETER = 346
SIDE_GUTTER = (CANVAS_WIDTH - CIRCLE_DIAMETER) // 2


@dataclass
class LogoSettings:
    threshold: int = 245
    logo_scale: float = 0.46
    x_offset: int = 0
    y_offset: int = 0
    optical_centering: bool = True
    bg_color: tuple[int, int, int, int] = (255, 255, 255, 255)


def svg_bytes_to_rgba(svg_bytes: bytes, width: int = 1600, height: int = 1600) -> Image.Image:
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


def remove_edge_connected_background(img: Image.Image, threshold: int = 245) -> Image.Image:
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
        if x < 0 or x >= w or y < 0 or y >= h or visited[y][x]:
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


def alpha_center_of_mass(img: Image.Image) -> tuple[float, float]:
    alpha = img.getchannel("A")
    w, h = img.size
    px = alpha.load()

    total = 0.0
    sum_x = 0.0
    sum_y = 0.0

    for y in range(h):
        for x in range(w):
            a = px[x, y]
            if a:
                total += a
                sum_x += x * a
                sum_y += y * a

    if total == 0:
        return w / 2, h / 2

    return sum_x / total, sum_y / total


def compute_optical_offsets(img: Image.Image) -> tuple[int, int]:
    cx, cy = alpha_center_of_mass(img)
    target_x = img.width / 2
    target_y = img.height / 2
    return round(target_x - cx), round(target_y - cy)


def create_badge(bg_color=(255, 255, 255, 255)) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse(
        (SIDE_GUTTER, 0, SIDE_GUTTER + CIRCLE_DIAMETER, CIRCLE_DIAMETER),
        fill=bg_color,
    )
    return canvas


def render_badge_from_bytes(data: bytes, filename: str, settings: LogoSettings) -> Image.Image:
    img = load_image_from_bytes(data, filename)
    img = remove_edge_connected_background(img, threshold=settings.threshold)
    img = trim_transparent_edges(img)
    img = resize_logo(img, settings.logo_scale)

    auto_x = 0
    auto_y = 0
    if settings.optical_centering:
        auto_x, auto_y = compute_optical_offsets(img)

    badge = create_badge(bg_color=settings.bg_color)
    x = (CANVAS_WIDTH - img.width) // 2 + auto_x + settings.x_offset
    y = (CANVAS_HEIGHT - img.height) // 2 + auto_y + settings.y_offset
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
