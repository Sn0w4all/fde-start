"""Tile-based image comparison for IMG2HTML diagnostics (Pillow)."""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageChops


@dataclass
class TileDiff:
    label: str  # e.g. "r1c2" (row 1, col 2, 1-indexed)
    score: float  # mean normalized difference 0..1


@dataclass
class CompareResult:
    overall: float  # mean normalized diff over whole image 0..1
    tiles: list[TileDiff]  # all tiles
    problem_tiles: list[str]  # labels above threshold


def _load_rgb(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def to_size(png: bytes, width: int, height: int) -> bytes:
    """Resize a rendered PNG to the original's pixel size."""
    img = _load_rgb(png).resize((max(1, width), max(1, height)))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _mean_diff(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    # weighted mean of pixel differences per channel, normalized to 0..1
    total = 0.0
    pixels = a.width * a.height
    if pixels == 0:
        return 0.0
    for ch in range(3):
        channel = hist[ch * 256 : (ch + 1) * 256]
        total += sum(value * count for value, count in enumerate(channel))
    return total / (3 * pixels * 255)


def compare(original_png: bytes, render_png: bytes, grid: int, threshold: float) -> CompareResult:
    """Split both images into grid x grid tiles, score per-tile divergence."""
    orig = _load_rgb(original_png)
    rend = _load_rgb(render_png).resize(orig.size)
    w, h = orig.size
    tw, th = w // grid, h // grid

    tiles: list[TileDiff] = []
    problems: list[str] = []
    for r in range(grid):
        for c in range(grid):
            box = (
                c * tw,
                r * th,
                (c + 1) * tw if c < grid - 1 else w,
                (r + 1) * th if r < grid - 1 else h,
            )
            score = _mean_diff(orig.crop(box), rend.crop(box))
            label = f"r{r + 1}c{c + 1}"
            tiles.append(TileDiff(label=label, score=score))
            if score > threshold:
                problems.append(label)

    overall = _mean_diff(orig, rend)
    return CompareResult(overall=overall, tiles=tiles, problem_tiles=problems)
