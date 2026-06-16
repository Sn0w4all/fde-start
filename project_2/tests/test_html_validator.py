"""Validator (render) tests. Skipped if Chromium is not installed locally."""
import pytest

from core.llm import _strip_markdown
from core.render import RenderError, Renderer, validate


def test_strip_markdown_fences():
    raw = "```html\n<html><body>hi</body></html>\n```"
    assert _strip_markdown(raw) == "<html><body>hi</body></html>"


def test_strip_markdown_noop():
    raw = "<!DOCTYPE html><html></html>"
    assert _strip_markdown(raw) == raw


async def test_validate_rejects_artifacts_without_rendering():
    """Artifact guard fails fast — raises before touching the renderer."""
    bad = "Looking at the problem zones, I need to fix:\n<!DOCTYPE html><html></html>"
    with pytest.raises(RenderError):
        await validate(None, bad)  # renderer never used; guard trips first


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return True
    except Exception:
        return False


needs_chromium = pytest.mark.skipif(
    not _chromium_available(), reason="Chromium not installed (run: playwright install chromium)"
)


@needs_chromium
async def test_valid_html_passes():
    r = Renderer()
    await r.start()
    try:
        result = await validate(
            r, "<!DOCTYPE html><html><body><h1>Hello world</h1></body></html>"
        )
        assert result.png[:8] == b"\x89PNG\r\n\x1a\n"
    finally:
        await r.stop()


@needs_chromium
async def test_console_error_html_fails():
    r = Renderer()
    await r.start()
    try:
        bad = (
            "<!DOCTYPE html><html><body><h1>x</h1>"
            "<script>throw new Error('boom')</script></body></html>"
        )
        with pytest.raises(RenderError):
            await validate(r, bad)
    finally:
        await r.stop()
