"""Headless Chromium rendering + HTML validation via Playwright."""
from __future__ import annotations

from dataclasses import dataclass, field

import structlog
from playwright.async_api import Browser, async_playwright

from core.html_utils import looks_like_html_document

log = structlog.get_logger(__name__)


class RenderError(Exception):
    """Raised when HTML fails to render or produces console errors."""


@dataclass
class RenderResult:
    png: bytes
    width: int
    height: int
    console_errors: list[str] = field(default_factory=list)


class Renderer:
    """Owns a single long-lived Chromium instance shared across tasks."""

    def __init__(self) -> None:
        self._pw = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        log.info("renderer_started")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def render(
        self,
        html: str,
        *,
        viewport_width: int = 1280,
        full_page: bool = True,
    ) -> RenderResult:
        """Render HTML to PNG. Raises RenderError on page errors or empty body."""
        if self._browser is None:
            raise RenderError("renderer not started")

        errors: list[str] = []
        context = await self._browser.new_context(
            viewport={"width": viewport_width, "height": 800},
            device_scale_factor=1,
        )
        page = await context.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            await page.set_content(html, wait_until="networkidle", timeout=30_000)
            body_text = (await page.inner_text("body")).strip() if await page.query_selector("body") else ""
            box = await page.evaluate(
                "() => ({w: document.body.scrollWidth, h: document.body.scrollHeight})"
            )
            width = max(1, int(box["w"]))
            height = max(1, int(box["h"]))
            if width <= 1 and height <= 1 and not body_text:
                raise RenderError("rendered page is empty")
            png = await page.screenshot(full_page=full_page, type="png")
            return RenderResult(png=png, width=width, height=height, console_errors=errors)
        except RenderError:
            raise
        except Exception as exc:  # playwright timeouts, parse failures, etc.
            raise RenderError(f"render failed: {exc}") from exc
        finally:
            await context.close()


async def validate(renderer: Renderer, html: str) -> RenderResult:
    """Validate output: clean standalone document, no console errors, non-empty.

    The artifact check runs first (free, no render) so stray commentary/preamble
    is rejected before spending a render. Raises RenderError on any failure.
    """
    if not looks_like_html_document(html):
        raise RenderError(
            "output is not a clean standalone HTML document "
            "(stray text/commentary outside <!DOCTYPE html>…</html>)"
        )
    result = await renderer.render(html)
    if result.console_errors:
        raise RenderError("console errors: " + "; ".join(result.console_errors[:5]))
    return result
