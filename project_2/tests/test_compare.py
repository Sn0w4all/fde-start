"""Tile-diff comparison tests (synthetic images, no network)."""
import io

from PIL import Image

from core.compare import compare


def _png(color, size=(90, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def test_identical_images_no_problems():
    a = _png((200, 50, 50))
    res = compare(a, a, 3, 0.15)
    assert res.overall < 0.01
    assert res.problem_tiles == []
    assert len(res.tiles) == 9  # 3x3 grid


def test_totally_different_all_tiles_problem():
    res = compare(_png((0, 0, 0)), _png((255, 255, 255)), 3, 0.15)
    assert res.overall > 0.9
    assert len(res.problem_tiles) == 9


def test_partial_diff_flags_only_changed_tile():
    base = Image.new("RGB", (90, 90), (0, 0, 0))
    other = Image.new("RGB", (90, 90), (0, 0, 0))
    # paint the top-left tile (0..30, 0..30) white
    for x in range(30):
        for y in range(30):
            other.putpixel((x, y), (255, 255, 255))

    def enc(im):
        b = io.BytesIO()
        im.save(b, "PNG")
        return b.getvalue()

    res = compare(enc(base), enc(other), 3, 0.15)
    assert "r1c1" in res.problem_tiles
    assert "r3c3" not in res.problem_tiles
    assert 0 < res.overall < 0.5


def test_render_resized_to_original_size():
    # different sizes must not raise — render is resized to original internally
    orig = _png((10, 20, 30), size=(120, 60))
    rend = _png((10, 20, 30), size=(300, 300))
    res = compare(orig, rend, 3, 0.15)
    assert res.overall < 0.02
